#!/usr/bin/env python3
"""Persist resumable TAP orchestration work items without external services."""

import argparse
import datetime as dt
import json
import os
import tempfile
import re
from pathlib import Path

STATES = ("PLANNING", "WAITING_FOR_PLAN_APPROVAL", "IMPLEMENTING", "TESTING", "COMPLETED", "BLOCKED")
PLANNING_PHASES = ("INTENT_ANALYSIS", "MOCKUP_REVIEW", "PLAN_FINALIZATION")
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
            "transitionIds": [x["id"] for x in transitions]}


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
    mockup.add_argument("--source", choices=("claude-design", "html-artifact"), required=True)
    mockup.add_argument("--fallback-reason", default="", help="Bắt buộc khi source=html-artifact: vì sao không dùng được Claude Design")
    mockup.add_argument("--artifact-url", required=True)
    mockup.add_argument("--artifact-id", required=True)
    mockup.add_argument("--contract", required=True, help="Mockup contract JSON, không chứa secret")
    clarify = sub.add_parser("record-clarification")
    clarify.add_argument("work_id")
    clarify.add_argument("--assumptions", required=True)
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
                "steps": {}, "tests": [], "mockup": None, "planApproval": None, "parity": [], "events": []}
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
                needs_mockup = data.get("flowKind") in ("screen", "chat-display", "flow")
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
            data["phase"] = args.phase
            event(data, "phase", args.phase)
        elif args.command == "record-clarification":
            if data.get("clarificationCount", 0) >= 1:
                raise SystemExit("clarification UX đã dùng hết budget")
            try: data["assumptions"] = json.loads(args.assumptions)
            except json.JSONDecodeError as exc: raise SystemExit(f"assumptions JSON không hợp lệ: {exc}")
            data["clarificationCount"] = 1
            event(data, "clarification", "1/1")
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
            if args.source == "html-artifact" and not args.fallback_reason.strip():
                raise SystemExit("html-artifact chỉ là fallback: cần --fallback-reason (môi trường không có Claude Design)")
            data["mockup"] = {"source": args.source, "fallbackReason": args.fallback_reason or None, "artifactUrl": args.artifact_url,
                              "artifactId": args.artifact_id, "contract": contract,
                              "recordedAt": now(), **metadata}
            event(data, "mockup", args.source)
        elif args.command == "approve-plan":
            if data["state"] != "WAITING_FOR_PLAN_APPROVAL":
                raise SystemExit("chỉ approve plan khi đang WAITING_FOR_PLAN_APPROVAL")
            if not data.get("readOnly") and not data.get("mockup"):
                raise SystemExit("plan write cần mockup contract trước approval")
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
