#!/usr/bin/env python3
"""Persist resumable TAP orchestration work items without external services."""

import argparse
import datetime as dt
import hashlib
import json
import os
import tempfile
import re
from pathlib import Path

STATES = ("PLANNING", "WAITING_FOR_PLAN_APPROVAL", "IMPLEMENTING", "TESTING", "COMPLETED", "BLOCKED")
# B1 INTENT_ANALYSIS (hỏi 1-3 câu) → B2 MOCKUP_REVIEW (Claude Design) → B3 REQUIREMENT_CONFIRMATION (bảng requirement) → PLAN_FINALIZATION
PLANNING_PHASES = ("INTENT_ANALYSIS", "MOCKUP_REVIEW", "REQUIREMENT_CONFIRMATION", "PLAN_FINALIZATION")
GATED_FLOWS = ("screen", "chat-display", "flow")
SCREEN_STATUS = ("existing", "modify", "new")
REQ_COLUMNS = ["trigger", "precondition", "chat panel", "display panel", "system", "must not"]
TRANSITIONS = {
    "PLANNING": {"WAITING_FOR_PLAN_APPROVAL", "IMPLEMENTING", "BLOCKED"},
    "WAITING_FOR_PLAN_APPROVAL": {"IMPLEMENTING", "BLOCKED"},
    "IMPLEMENTING": {"TESTING", "BLOCKED"},
    "TESTING": {"IMPLEMENTING", "COMPLETED", "BLOCKED"},
    "COMPLETED": set(),
    "BLOCKED": set(),
}
SCREEN_ID = re.compile(r"screen-\d{2,}$")


def validate_mockup(contract):
    for field in ("states", "actions", "expectedUi", "chat", "display", "fixtures", "transitions"):
        if field not in contract:
            raise ValueError(f"mockup contract thiếu trường: {field}")
    screens = contract.get("screens")
    if not screens:
        return {"schemaVersion": contract.get("schemaVersion", 1), "screenIds": [], "laneIds": [], "transitionIds": []}
    flow = contract.get("flowMap", {})
    if not flow.get("startScreenId") or not flow.get("lanes") or "transitions" not in flow:
        raise ValueError("multi-screen contract thiếu flowMap")
    for x in screens:
        if x.get("status") not in SCREEN_STATUS:
            raise ValueError(f"{x.get('id')}: status phải là existing/modify/new")
        if x["status"] != "new" and not x.get("mcpRef"):
            raise ValueError(f"{x.get('id')}: màn existing/modify phải có mcpRef (mã screen lấy từ MCP get_screen)")
        for panel in ("chat", "display"):
            if not isinstance(x.get(panel), dict) or not x[panel]:
                raise ValueError(f"{x.get('id')}: thiếu hoặc rỗng {panel} panel (mỗi màn phải đủ chat + display)")
    ids = [x.get("id") for x in screens]
    if len(ids) != len(set(ids)) or not all(isinstance(x, str) and SCREEN_ID.fullmatch(x) for x in ids):
        raise ValueError("screen ID không hợp lệ")
    if sorted(x.get("number") for x in screens) != list(range(1, len(screens) + 1)):
        raise ValueError("screen number không liên tiếp")
    lanes = [x.get("id") for x in flow["lanes"]]
    if flow["startScreenId"] not in ids or not lanes:
        raise ValueError("flowMap start/lane không hợp lệ")
    transitions = flow["transitions"]
    for t in transitions:
        if not {"id", "fromScreenId", "toScreenId", "laneId", "trigger", "ctaLabel", "expectedResult"} <= set(t):
            raise ValueError("transition thiếu field")
        if t["fromScreenId"] not in ids or t["toScreenId"] not in ids or t["laneId"] not in lanes:
            raise ValueError("transition tham chiếu không hợp lệ")
    return {"schemaVersion": contract.get("schemaVersion", 2), "screenIds": ids, "laneIds": lanes,
            "transitionIds": [x["id"] for x in transitions],
            "transitionLabels": {x["id"]: f"T{i}" for i, x in enumerate(transitions, 1)}}


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def mockup_hash(mockup):
    return sha(json.dumps({"contract": mockup["contract"], "artifactId": mockup["artifactId"]}, sort_keys=True, ensure_ascii=False))


def gated(data):
    return data.get("flowKind") in GATED_FLOWS and not data.get("readOnly")


def mockup_approved_valid(data):
    a, m = data.get("mockupApproved"), data.get("mockup")
    return bool(a and m and a.get("mockupHash") == mockup_hash(m))


def requirement_confirmed_valid(data):
    c, r = data.get("requirementConfirmed"), data.get("requirement")
    return bool(mockup_approved_valid(data) and c and r and c.get("fingerprint") == r.get("fingerprint"))


def invalidate(data, *fields):
    for f in fields:
        data[f] = None


def parse_requirement_table(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    if not rows:
        raise ValueError("không tìm thấy bảng markdown")
    if [c.lower() for c in rows[0]] != REQ_COLUMNS:
        raise ValueError("header bảng phải đúng 6 cột: Trigger | Precondition | Chat panel | Display panel | System | Must not")
    body = rows[1:]
    if not body:
        raise ValueError("bảng không có dòng dữ liệu")
    for i, r in enumerate(body, 1):
        if len(r) != 6 or not all(r):
            raise ValueError(f"dòng {i} phải đủ 6 ô, không để trống")
    return body


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def item_path(store, work_id):
    if not work_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in work_id):
        raise ValueError("work_id chỉ gồm chữ, số, dấu gạch ngang hoặc gạch dưới")
    return Path(store) / f"{work_id}.json"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".work-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def event(data, kind, detail):
    data.setdefault("events", []).append({"at": now(), "kind": kind, "detail": detail})
    data["updatedAt"] = now()


def main():
    parser = argparse.ArgumentParser(description="Manage resumable TAP work items")
    parser.add_argument("--store", default=".tap-work-items")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("work_id")
    create.add_argument("--intent", required=True)
    create.add_argument("--read-only", action="store_true")
    create.add_argument("--summary", required=True)
    create.add_argument("--flow-kind", choices=("screen", "chat-display", "flow", "other"), default="other")
    create.add_argument("--clarification-count", type=int, default=0)
    create.add_argument("--assumptions", default="[]", help="JSON visible assumptions")
    show = sub.add_parser("show")
    show.add_argument("work_id")
    transition = sub.add_parser("transition")
    transition.add_argument("work_id")
    transition.add_argument("state", choices=STATES)
    transition.add_argument("--reason", default="")
    phase = sub.add_parser("set-phase")
    phase.add_argument("work_id")
    phase.add_argument("phase", choices=PLANNING_PHASES)
    mockup = sub.add_parser("record-mockup")
    mockup.add_argument("work_id")
    mockup.add_argument("--source", choices=("claude-design",), required=True)
    mockup.add_argument("--artifact-url", required=True)
    mockup.add_argument("--artifact-id", required=True)
    mockup.add_argument("--contract", required=True, help="Mockup contract JSON, không chứa secret")
    clarify = sub.add_parser("record-clarification")
    clarify.add_argument("work_id")
    clarify.add_argument("--assumptions", required=True)
    clarify.add_argument("--questions", required=True, help='JSON list 1-3 câu: [{"q":"...","default":"..."}]')
    am = sub.add_parser("approve-mockup")
    am.add_argument("work_id")
    am.add_argument("--quote", required=True, help="Nguyên văn người dùng đồng ý với Mockup")
    rr = sub.add_parser("record-requirement")
    rr.add_argument("work_id")
    rr.add_argument("--table-file", required=True, help="File markdown bảng requirement 6 cột đã in ra chat")
    cr = sub.add_parser("confirm-requirement")
    cr.add_argument("work_id")
    cr.add_argument("--fingerprint", required=True)
    cr.add_argument("--quote", required=True, help="Nguyên văn người dùng xác nhận requirement + mockup")
    approve = sub.add_parser("approve-plan")
    approve.add_argument("work_id")
    approve.add_argument("--fingerprint", required=True)
    parity = sub.add_parser("record-parity")
    parity.add_argument("work_id")
    parity.add_argument("--status", choices=("passed", "failed"), required=True)
    parity.add_argument("--evidence", required=True)
    mark = sub.add_parser("mark-step")
    mark.add_argument("work_id")
    mark.add_argument("step")
    mark.add_argument("--status", choices=("completed", "failed"), required=True)
    test = sub.add_parser("record-test")
    test.add_argument("work_id")
    test.add_argument("name")
    test.add_argument("--status", choices=("passed", "failed", "blocked"), required=True)
    test.add_argument("--evidence", default="")
    args = parser.parse_args()
    path = item_path(args.store, args.work_id)

    if args.command == "create":
        if path.exists():
            raise SystemExit(f"work item đã tồn tại: {path}")
        if args.clarification_count not in (0, 1):
            raise SystemExit("clarificationCount chỉ có thể là 0 hoặc 1")
        try: assumptions = json.loads(args.assumptions)
        except json.JSONDecodeError as exc: raise SystemExit(f"assumptions JSON không hợp lệ: {exc}")
        data = {"id": args.work_id, "intent": args.intent, "readOnly": args.read_only,
                "summary": args.summary, "state": "PLANNING", "createdAt": now(),
                "updatedAt": now(), "phase": "INTENT_ANALYSIS", "flowKind": args.flow_kind,
                "clarificationCount": args.clarification_count, "assumptions": assumptions,
                "steps": {}, "tests": [], "mockup": None, "clarification": None, "mockupApproved": None,
                "requirement": None, "requirementConfirmed": None, "planApproval": None, "parity": [], "events": []}
        event(data, "created", "")
        write(path, data)
    else:
        if not path.exists():
            raise SystemExit(f"không tìm thấy work item: {path}")
        data = read(path)
        if args.command == "transition":
            if args.state == data["state"]:
                event(data, "transition-idempotent", args.state)
            elif args.state not in TRANSITIONS[data["state"]]:
                raise SystemExit(f"transition không hợp lệ: {data['state']} → {args.state}")
            else:
                needs_mockup = data.get("flowKind") in GATED_FLOWS
                if gated(data) and data["state"] == "PLANNING" and args.state in ("WAITING_FOR_PLAN_APPROVAL", "IMPLEMENTING"):
                    if args.state == "IMPLEMENTING":
                        raise SystemExit("flow ghi phải qua WAITING_FOR_PLAN_APPROVAL, không nhảy thẳng PLANNING → IMPLEMENTING")
                    if not data.get("clarification"):
                        raise SystemExit("B1 chưa xong: cần record-clarification (1-3 câu hỏi)")
                    if not mockup_approved_valid(data):
                        raise SystemExit("B2 chưa xong: cần record-mockup rồi approve-mockup (người dùng đồng ý Mockup)")
                    if not requirement_confirmed_valid(data):
                        raise SystemExit("B3 chưa xong: cần record-requirement rồi confirm-requirement (người dùng xác nhận bảng requirement)")
                    if data["phase"] != "PLAN_FINALIZATION":
                        raise SystemExit("cần phase PLAN_FINALIZATION trước plan approval")
                if data["state"] == "PLANNING" and args.state == "WAITING_FOR_PLAN_APPROVAL" and needs_mockup and not data.get("mockup"):
                    raise SystemExit("flow này cần mockup contract trước plan approval")
                if data["state"] == "WAITING_FOR_PLAN_APPROVAL" and args.state == "IMPLEMENTING" and needs_mockup and not data.get("planApproval"):
                    raise SystemExit("flow này cần plan approval fingerprint trước implementation")
                old = data["state"]
                data["state"] = args.state
                event(data, "transition", f"{old} → {args.state}; {args.reason}")
        elif args.command == "set-phase":
            if data["state"] != "PLANNING":
                raise SystemExit("chỉ đổi phase khi work item đang PLANNING")
            cur, new = PLANNING_PHASES.index(data["phase"]), PLANNING_PHASES.index(args.phase)
            if gated(data):
                if new > cur + 1:
                    raise SystemExit(f"không được bỏ qua bước: {data['phase']} → {args.phase}")
                if new == 0 and cur > 0:
                    raise SystemExit("không quay lại INTENT_ANALYSIS (B1 chỉ có một lượt)")
                if args.phase == "MOCKUP_REVIEW" and not data.get("clarification"):
                    raise SystemExit("B1 chưa xong: cần record-clarification (tối thiểu 1 câu hỏi) trước khi vào B2")
                if args.phase == "REQUIREMENT_CONFIRMATION" and not mockup_approved_valid(data):
                    raise SystemExit("B2 chưa xong: cần approve-mockup trước khi vào B3")
                if args.phase == "PLAN_FINALIZATION" and not requirement_confirmed_valid(data):
                    raise SystemExit("B3 chưa xong: cần confirm-requirement trước PLAN_FINALIZATION")
                if new < cur:
                    invalidate(data, "requirementConfirmed", "planApproval")
                    if args.phase == "MOCKUP_REVIEW":
                        invalidate(data, "mockupApproved", "requirement")
                    else:
                        invalidate(data, "requirement")
                    event(data, "invalidate", f"quay lại {args.phase}")
            data["phase"] = args.phase
            event(data, "phase", args.phase)
        elif args.command == "record-clarification":
            if data.get("clarification") or data.get("clarificationCount", 0) >= 1:
                raise SystemExit("clarification UX đã dùng hết budget")
            if data["phase"] != "INTENT_ANALYSIS":
                raise SystemExit("record-clarification chỉ trong INTENT_ANALYSIS (B1)")
            try: questions = json.loads(args.questions)
            except json.JSONDecodeError as exc: raise SystemExit(f"questions JSON không hợp lệ: {exc}")
            if not isinstance(questions, list) or not 1 <= len(questions) <= 3:
                raise SystemExit("phải hỏi tối thiểu 1 và tối đa 3 câu")
            if not all(isinstance(q, dict) and str(q.get("q", "")).strip() and str(q.get("default", "")).strip() for q in questions):
                raise SystemExit("mỗi câu hỏi phải có q và default (đáp án mặc định đề xuất)")
            data["clarification"] = {"questions": questions, "at": now()}
            try: data["assumptions"] = json.loads(args.assumptions)
            except json.JSONDecodeError as exc: raise SystemExit(f"assumptions JSON không hợp lệ: {exc}")
            data["clarificationCount"] = 1
            event(data, "clarification", f"1 lượt, {len(questions)} câu")
        elif args.command == "record-mockup":
            if data["state"] != "PLANNING" or data["phase"] != "MOCKUP_REVIEW":
                raise SystemExit("mockup chỉ được ghi trong PLANNING/MOCKUP_REVIEW")
            try:
                contract = json.loads(args.contract)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"mockup contract JSON không hợp lệ: {exc}")
            try: metadata = validate_mockup(contract)
            except ValueError as exc: raise SystemExit(str(exc))
            if "/preview/" in args.artifact_url or "localhost:8931" in args.artifact_url:
                raise SystemExit("MCP renderer preview URL không phải journey mockup artifact")
            data["mockup"] = {"source": args.source,  "artifactUrl": args.artifact_url,
                              "artifactId": args.artifact_id, "contract": contract,
                              "recordedAt": now(), **metadata}
            invalidate(data, "mockupApproved", "requirement", "requirementConfirmed", "planApproval")
            event(data, "mockup", args.source)
        elif args.command == "approve-mockup":
            if data["state"] != "PLANNING" or data["phase"] != "MOCKUP_REVIEW":
                raise SystemExit("approve-mockup chỉ trong PLANNING/MOCKUP_REVIEW")
            if not data.get("mockup"):
                raise SystemExit("chưa có mockup để duyệt")
            if not args.quote.strip():
                raise SystemExit("cần nguyên văn người dùng đồng ý Mockup")
            data["mockupApproved"] = {"quote": args.quote, "mockupHash": mockup_hash(data["mockup"]), "at": now()}
            invalidate(data, "requirement", "requirementConfirmed", "planApproval")
            event(data, "mockup-approved", data["mockupApproved"]["mockupHash"])
        elif args.command == "record-requirement":
            if data["phase"] != "REQUIREMENT_CONFIRMATION" or data["state"] != "PLANNING":
                raise SystemExit("record-requirement chỉ trong PLANNING/REQUIREMENT_CONFIRMATION (B3)")
            if not mockup_approved_valid(data):
                raise SystemExit("mockup chưa được người dùng đồng ý (hoặc đã đổi sau khi duyệt)")
            try: text = Path(args.table_file).read_text(encoding="utf-8"); body = parse_requirement_table(text)
            except (OSError, ValueError) as exc: raise SystemExit(f"bảng requirement không hợp lệ: {exc}")
            triggers = [r[0] for r in body]
            missing = [label for tid, label in data["mockup"].get("transitionLabels", {}).items()
                       if not any(re.search(rf"\b{label}\b", t) for t in triggers)]
            if missing:
                raise SystemExit(f"bảng thiếu transition (cột Trigger phải ghi kèm (T<n>)): {', '.join(missing)}")
            fp = sha(text.strip() + data["mockupApproved"]["mockupHash"])
            data["requirement"] = {"table": text, "rows": len(body), "fingerprint": fp, "recordedAt": now()}
            invalidate(data, "requirementConfirmed", "planApproval")
            event(data, "requirement", fp)
        elif args.command == "confirm-requirement":
            if data["phase"] != "REQUIREMENT_CONFIRMATION" or data["state"] != "PLANNING":
                raise SystemExit("confirm-requirement chỉ trong PLANNING/REQUIREMENT_CONFIRMATION (B3)")
            if not data.get("requirement") or args.fingerprint != data["requirement"]["fingerprint"]:
                raise SystemExit("fingerprint không khớp bảng requirement hiện tại")
            if not args.quote.strip():
                raise SystemExit("cần nguyên văn người dùng xác nhận")
            data["requirementConfirmed"] = {"fingerprint": args.fingerprint, "quote": args.quote, "at": now()}
            event(data, "requirement-confirmed", args.fingerprint)
        elif args.command == "approve-plan":
            if data["state"] != "WAITING_FOR_PLAN_APPROVAL":
                raise SystemExit("chỉ approve plan khi đang WAITING_FOR_PLAN_APPROVAL")
            if not data.get("readOnly") and not data.get("mockup"):
                raise SystemExit("plan write cần mockup contract trước approval")
            if gated(data) and not requirement_confirmed_valid(data):
                raise SystemExit("plan write cần requirement đã được người dùng xác nhận (B3)")
            data["planApproval"] = {"fingerprint": args.fingerprint, "approvedAt": now()}
            event(data, "plan-approved", args.fingerprint)
        elif args.command == "record-parity":
            data["parity"].append({"status": args.status, "evidence": args.evidence, "at": now()})
            event(data, "mockup-parity", args.status)
        elif args.command == "mark-step":
            current = data["steps"].get(args.step)
            if current == "completed" and args.status != "completed":
                raise SystemExit("không thể ghi đè step completed")
            data["steps"][args.step] = args.status
            event(data, "step", f"{args.step}: {args.status}")
        elif args.command == "record-test":
            data["tests"].append({"name": args.name, "status": args.status, "evidence": args.evidence, "at": now()})
            event(data, "test", f"{args.name}: {args.status}")
        write(path, data)
    print(json.dumps(read(path), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
