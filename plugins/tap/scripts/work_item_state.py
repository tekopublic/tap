#!/usr/bin/env python3
"""Persist resumable TAP orchestration work items without external services.

Plugin 3.3.0: mọi yêu cầu có ghi phải đi đủ B0 → B1 → B1.5 → B2 → B3 → B4 → B5 → B6.
Lệnh sai thứ tự bị từ chối (exit 2) với JSON {currentStep, attemptedStep, missingGates,
nextAction, progress} để gateway in lại bảng tiến trình cho người dùng.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

STATES = ("PLANNING", "WAITING_FOR_PLAN_APPROVAL", "IMPLEMENTING", "TESTING", "COMPLETED", "BLOCKED")
# B1/B1.5 INTENT_ANALYSIS → B2 MOCKUP_REVIEW → B3 REQUIREMENT_CONFIRMATION → B4 PLAN_FINALIZATION
PLANNING_PHASES = ("INTENT_ANALYSIS", "MOCKUP_REVIEW", "REQUIREMENT_CONFIRMATION", "PLAN_FINALIZATION")
FLOW_KINDS = ("screen", "chat-display", "flow", "config", "other")
SCREEN_STATUS = ("existing", "modify", "new")
# 9 cột theo chuẩn usecase spec (a_tap6 .prompts/skills/write-usecase-spec.md) — key JSON của save_requirement
REQ_KEYS = ["id", "scope", "trigger", "precondition", "chatPanel", "displayPanel", "system", "mustNot", "passRate"]
REQ_HEADER_ALIASES = [
    {"id"}, {"scope"}, {"trigger"},
    {"điều kiện trước", "precondition"}, {"chat panel"}, {"display panel"},
    {"hệ thống", "system"}, {"không được làm", "must not"}, {"pass rate"},
]
REQ_HEADER_LABEL = "ID | Scope | Trigger | Điều kiện trước | Chat panel | Display panel | Hệ thống | Không được làm | Pass rate"
SCOPE_RE = re.compile(r"^(issue \d+|Change|Proposed|Deferred post-MVP)(?=$|[\s,;·(🔒⏳])")
REQ_ID_RE = re.compile(r"^([A-Z][A-Z0-9]*-[A-Z][A-Z0-9]*)-(\d{3,})([A-Z]?)$")
URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$")
TRANSITIONS = {
    "PLANNING": {"WAITING_FOR_PLAN_APPROVAL", "IMPLEMENTING", "BLOCKED"},
    "WAITING_FOR_PLAN_APPROVAL": {"IMPLEMENTING", "BLOCKED"},
    "IMPLEMENTING": {"TESTING", "BLOCKED"},
    "TESTING": {"IMPLEMENTING", "COMPLETED", "BLOCKED"},
    "COMPLETED": set(),
    "BLOCKED": set(),
}
SCREEN_ID = re.compile(r"screen-\d{2,}$")
STEPS = [
    ("B0", "Tiếp nhận"),
    ("B1", "Làm rõ yêu cầu (+ địa chỉ web tenant)"),
    ("B1.5", "Chạy thử use case trên web tenant"),
    ("B2", "Đề xuất + mockup Claude Design"),
    ("B3", "Bảng Requirement 9 cột + save_requirement"),
    ("B4", "Chốt plan"),
    ("B5", "Triển khai vào bản nháp + declare_requirement_changes"),
    ("B6", "Kiểm thử parity + dẫn sang Tenant Admin để Public"),
]
STEP_INDEX = {code: i for i, (code, _) in enumerate(STEPS)}
NEXT_ACTION = {
    "B0": "create work item",
    "B1": "hỏi 1-3 câu UX (mỗi câu có phương án + đề xuất) + câu địa chỉ web tenant, rồi record-clarification --tenant-url",
    "B1.5": "chạy thử use case trên web tenant (hoặc ghi skipped kèm lý do), rồi record-live-probe",
    "B2": "set-phase MOCKUP_REVIEW → in đề xuất + record-proposal → record-mockup → người dùng đồng ý → approve-mockup",
    "B3": "set-phase REQUIREMENT_CONFIRMATION → in bảng 9 cột + record-requirement → người dùng Xác nhận → confirm-requirement → gọi MCP save_requirement → record-saved-requirement",
    "B4": "set-phase PLAN_FINALIZATION → transition WAITING_FOR_PLAN_APPROVAL → người dùng duyệt → approve-plan → transition IMPLEMENTING",
    "B5": "ghi nháp mang requirementId → gọi MCP declare_requirement_changes → record-change; record-review-link → transition TESTING",
    "B6": "record-parity --row-ids <mọi ID> → transition COMPLETED; dẫn người dùng sang Tenant Admin để Public",
}


class GateError(Exception):
    def __init__(self, message, attempted=None, missing=None):
        super().__init__(message)
        self.attempted, self.missing = attempted, missing or []


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
    """Mọi yêu cầu có ghi (kể cả config) đều qua cổng; chỉ yêu cầu read-only được miễn."""
    return not data.get("readOnly")


def mockup_approved_valid(data):
    a, m = data.get("mockupApproved"), data.get("mockup")
    return bool(data.get("proposal") and a and m and a.get("mockupHash") == mockup_hash(m))


def requirement_confirmed_valid(data):
    c, r = data.get("requirementConfirmed"), data.get("requirement")
    return bool(mockup_approved_valid(data) and c and r and c.get("fingerprint") == r.get("fingerprint"))


def requirement_saved_valid(data):
    s, r = data.get("savedRequirement"), data.get("requirement")
    return bool(requirement_confirmed_valid(data) and s and r and s.get("fingerprint") == r.get("fingerprint"))


def invalidate(data, *fields):
    for f in fields:
        data[f] = None


# ---------- tiến trình B0–B6 ----------

def step_done(data, code):
    state = data.get("state")
    if code == "B0":
        return True
    if code == "B1":
        return bool(data.get("clarification"))
    if code == "B1.5":
        return bool(data.get("clarification") and data.get("liveProbe"))
    if code == "B2":
        return bool(data.get("liveProbe")) and mockup_approved_valid(data)
    if code == "B3":
        return requirement_saved_valid(data)
    if code == "B4":
        return requirement_saved_valid(data) and bool(data.get("planApproval")) and state in ("IMPLEMENTING", "TESTING", "COMPLETED")
    if code == "B5":
        return bool(data.get("changes")) and bool(data.get("reviewLink")) and state in ("TESTING", "COMPLETED")
    if code == "B6":
        return state == "COMPLETED"
    return False


def done_set(data):
    if not gated(data):
        return {"B0"}
    done = set()
    for code, _ in STEPS:
        if not step_done(data, code):
            break
        done.add(code)
    return done


def current_step(data):
    if not gated(data):
        return "B0"
    done = done_set(data)
    for code, _ in STEPS:
        if code not in done:
            return code
    return "B6"


def step_evidence(data, code):
    ev = {
        "B0": f"workItem `{data.get('id')}`" + (f", resume `{data['baseRequirement']['requirementId']}`" if data.get("baseRequirement") else ""),
        "B1": (data.get("clarification") or {}).get("tenantUrl", ""),
        "B1.5": (data.get("liveProbe") or {}).get("summary", ""),
        "B2": f"\"{(data.get('mockupApproved') or {}).get('quote', '')}\"" if data.get("mockupApproved") else "",
        "B3": f"requirementId `{(data.get('savedRequirement') or {}).get('requirementId', '')}`" if data.get("savedRequirement") else "",
        "B4": f"plan `{(data.get('planApproval') or {}).get('fingerprint', '')}`" if data.get("planApproval") else "",
        "B5": (f"{len(data.get('changes') or [])} thay đổi đã khai" + (f", review {data['reviewLink']}" if data.get("reviewLink") else "")) if data.get("changes") else "",
        "B6": (data.get("parity") or [{}])[-1].get("status", "") if data.get("parity") else "",
    }
    return ev.get(code, "")


def progress_table(data, short=False):
    cur = current_step(data)
    if short:
        name = dict(STEPS)[cur]
        tail = "đã xong toàn bộ" if data.get("state") == "COMPLETED" else NEXT_ACTION[cur]
        return f"Bước hiện tại: {cur} — {name} — tiếp theo: {tail}"
    if not gated(data):
        return f"Yêu cầu chỉ đọc (`{data.get('id')}`): không cần B1–B6, trả lời trực tiếp. Mọi yêu cầu có ghi phải tạo work item mới và đi đủ B0–B6."
    done, invalid = done_set(data), set(data.get("invalidatedSteps") or [])
    lines = ["| # | Bước | Trạng thái | Bằng chứng |", "|---|---|---|---|"]
    for code, name in STEPS:
        if code in done:
            status = "Xong"
        elif code == cur and data.get("state") != "COMPLETED":
            status = "**Đang ở đây**" + (" (làm lại)" if code in invalid else "")
        elif code in invalid:
            status = "Bị mất hiệu lực"
        else:
            status = "Chưa làm"
        lines.append(f"| {code} | {name} | {status} | {step_evidence(data, code) if code in done else ''} |")
    lines.append("")
    lines.append(f"Việc tiếp theo: {NEXT_ACTION[cur] if data.get('state') != 'COMPLETED' else 'không còn — đã COMPLETED'}")
    return "\n".join(lines)


def gate(cond, message, attempted, *missing):
    if not cond:
        raise GateError(message, attempted, list(missing))


# ---------- bảng Requirement 9 cột ----------

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
    header = [c.lower() for c in rows[0]]
    if len(header) != 9 or not all(h in REQ_HEADER_ALIASES[i] for i, h in enumerate(header)):
        raise ValueError(f"header bảng phải đúng 9 cột theo thứ tự: {REQ_HEADER_LABEL}")
    body = rows[1:]
    if not body:
        raise ValueError("bảng không có dòng dữ liệu")
    out = []
    for i, r in enumerate(body, 1):
        if len(r) != 9 or not all(r):
            raise ValueError(f"dòng {i} phải đủ 9 ô, không để trống")
        out.append(dict(zip(REQ_KEYS, r)))
    return out


def validate_rows(rows):
    seen = set()
    for i, r in enumerate(rows, 1):
        rid = r["id"]
        if not REQ_ID_RE.match(rid):
            raise ValueError(f"dòng {i}: ID `{rid}` sai định dạng <MODULE>-<FAMILY>-<nnn><X> (vd CART-DEL-017C)")
        if rid in seen:
            raise ValueError(f"dòng {i}: ID `{rid}` bị trùng trong bảng")
        seen.add(rid)
        if not SCOPE_RE.match(r["scope"]):
            raise ValueError(f"dòng {i} ({rid}): Scope phải bắt đầu bằng `issue <số>`, `Change`, `Proposed` hoặc `Deferred post-MVP` (nguyên từ)")
        if r["passRate"] not in ("100%", "80%"):
            raise ValueError(f"dòng {i} ({rid}): Pass rate chỉ nhận 100% hoặc 80%")
        if r["passRate"] == "80%":
            tags = re.findall(r"\[[^\]]+\]", r["trigger"])
            if "[Chat]" not in tags or any("chip" in t.lower() for t in tags):
                raise ValueError(f"dòng {i} ({rid}): 80% chỉ cho Trigger `[Chat]` không gắn tag chip")


def check_id_stability(rows, history, retired):
    """Quy tắc ID sau lần lưu đầu (BR-03 / write-usecase-spec §5)."""
    if not history:
        return
    # số / chữ cái lớn nhất tính cả ID đã xoá (History của spec)
    parsed_hist = [REQ_ID_RE.match(h) for h in set(history) | set(retired)]
    parsed_hist = [m for m in parsed_hist if m]
    max_num = max((int(m.group(2)) for m in parsed_hist), default=0)
    letters = {}
    for m in parsed_hist:
        letters.setdefault(int(m.group(2)), []).append(m.group(3) or "A")
    new_nums = []
    for r in rows:
        rid = r["id"]
        if rid in retired:
            raise ValueError(f"ID `{rid}` đã bị xoá trước đó, không được dùng lại")
        if rid in history:
            continue
        m = REQ_ID_RE.match(rid)
        num, letter = int(m.group(2)), m.group(3)
        if num in letters:
            if not letter or letter <= max(letters[num]):
                raise ValueError(f"ID mới `{rid}`: case mới của usecase {num:03d} phải lấy chữ cái sau `{max(letters[num])}`")
        elif num <= max_num:
            raise ValueError(f"ID mới `{rid}`: usecase mới phải lấy số lớn hơn {max_num:03d} (số lớn nhất đã dùng)")
        else:
            new_nums.append(num)
    if new_nums and sorted(set(new_nums)) != list(range(max_num + 1, max_num + 1 + len(set(new_nums)))):
        raise ValueError(f"usecase mới phải đánh số liên tiếp từ {max_num + 1:03d}")


def table_fingerprint(rows, mockup_h):
    return sha(json.dumps(rows, ensure_ascii=False, sort_keys=True) + mockup_h)


# ---------- câu hỏi B1 (R5) ----------

def validate_questions(questions):
    if not isinstance(questions, list) or not 1 <= len(questions) <= 3:
        raise ValueError("phải hỏi tối thiểu 1 và tối đa 3 câu UX (câu địa chỉ web không tính, ghi bằng --tenant-url)")
    for i, q in enumerate(questions, 1):
        if not isinstance(q, dict) or not str(q.get("q", "")).strip():
            raise ValueError(f"câu {i}: thiếu nội dung `q`")
        opts = q.get("options")
        if not isinstance(opts, list) or len([o for o in opts if str(o).strip()]) < 2:
            raise ValueError(f"câu {i}: phải có `options` gồm ít nhất 2 phương án (kèm giải thích hệ quả)")
        if not str(q.get("recommended", "")).strip() or not str(q.get("reason", "")).strip():
            raise ValueError(f"câu {i}: phải có `recommended` (phương án đề xuất) và `reason` (lý do)")


def validate_probe(probe, tenant_url):
    if not isinstance(probe, dict) or probe.get("status") not in ("done", "skipped"):
        raise ValueError("live probe phải có status done hoặc skipped")
    if probe["status"] == "skipped":
        if not str(probe.get("reason", "")).strip():
            raise ValueError("live probe skipped phải ghi lý do (reason)")
        return f"skipped: {probe['reason']}"
    if not URL_RE.match(tenant_url or ""):
        raise ValueError("địa chỉ web tenant đang là skipped — live probe chỉ có thể skipped")
    cases = probe.get("useCases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("live probe done phải có ít nhất 1 use case")
    for i, c in enumerate(cases, 1):
        for k in ("id", "input", "expected", "actual", "result"):
            if not str(c.get(k, "")).strip():
                raise ValueError(f"use case {i}: thiếu `{k}`")
        if c["result"] not in ("pass", "diff", "not-run"):
            raise ValueError(f"use case {i}: result chỉ nhận pass / diff / not-run")
    count = {k: sum(1 for c in cases if c["result"] == k) for k in ("pass", "diff", "not-run")}
    return f"{len(cases)} use case: {count['pass']} khớp, {count['diff']} lệch, {count['not-run']} không chạy"


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


def load_json_arg(text, label):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GateError(f"{label} JSON không hợp lệ: {exc}")


def read_file(path, label):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"không đọc được {label}: {exc}")


def build_parser():
    parser = argparse.ArgumentParser(description="Manage resumable TAP work items (B0–B6)")
    parser.add_argument("--store", default=".tap-work-items")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("work_id")
    create.add_argument("--intent", required=True)
    create.add_argument("--read-only", action="store_true")
    create.add_argument("--summary", required=True)
    create.add_argument("--flow-kind", choices=FLOW_KINDS, default="other")
    create.add_argument("--clarification-count", type=int, default=0)
    create.add_argument("--assumptions", default="[]", help="JSON visible assumptions")
    create.add_argument("--requirement-id", help="Resume/sửa Requirement đã có (lấy từ get_requirement)")
    create.add_argument("--requirement-status", choices=("draft", "implementing", "published"))
    create.add_argument("--baseline-table-file", help="Bảng 9 cột hiện tại của Requirement (từ get_requirement) để giữ ID")
    create.add_argument("--retired-ids", default="", help="ID đã xoá trước đó, cách nhau dấu phẩy")
    show = sub.add_parser("show")
    show.add_argument("work_id")
    prog = sub.add_parser("progress")
    prog.add_argument("work_id")
    prog.add_argument("--short", action="store_true")
    transition = sub.add_parser("transition")
    transition.add_argument("work_id")
    transition.add_argument("state", choices=STATES)
    transition.add_argument("--reason", default="")
    phase = sub.add_parser("set-phase")
    phase.add_argument("work_id")
    phase.add_argument("phase", choices=PLANNING_PHASES)
    clarify = sub.add_parser("record-clarification")
    clarify.add_argument("work_id")
    clarify.add_argument("--assumptions", required=True)
    clarify.add_argument("--questions", required=True,
                         help='JSON 1-3 câu: [{"q":"...","options":["A. ...","B. ..."],"recommended":"A","reason":"..."}]')
    clarify.add_argument("--tenant-url", required=True, help="Địa chỉ web storefront của tenant (http/https) hoặc skipped:<lý do>")
    probe = sub.add_parser("record-live-probe")
    probe.add_argument("work_id")
    probe.add_argument("--file", required=True, help="JSON {status: done|skipped, reason?, tool?, useCases:[{id,input,expected,actual,result}]}")
    proposal = sub.add_parser("record-proposal")
    proposal.add_argument("work_id")
    proposal.add_argument("--file", required=True, help="Markdown đề xuất đã in ra chat (hiện trạng / khoảng trống / thay đổi đề xuất)")
    mockup = sub.add_parser("record-mockup")
    mockup.add_argument("work_id")
    mockup.add_argument("--source", choices=("claude-design",), required=True)
    mockup.add_argument("--artifact-url", required=True)
    mockup.add_argument("--artifact-id", required=True)
    mockup.add_argument("--contract", required=True, help="Mockup contract JSON, không chứa secret")
    am = sub.add_parser("approve-mockup")
    am.add_argument("work_id")
    am.add_argument("--quote", required=True, help="Nguyên văn người dùng đồng ý với Mockup")
    rr = sub.add_parser("record-requirement")
    rr.add_argument("work_id")
    rr.add_argument("--table-file", required=True, help="File markdown bảng Requirement 9 cột đã in ra chat")
    cr = sub.add_parser("confirm-requirement")
    cr.add_argument("work_id")
    cr.add_argument("--fingerprint", required=True)
    cr.add_argument("--quote", required=True, help="Nguyên văn người dùng xác nhận requirement + mockup")
    sr = sub.add_parser("record-saved-requirement")
    sr.add_argument("work_id")
    sr.add_argument("--requirement-id", required=True, help="requirementId do MCP save_requirement trả về")
    sr.add_argument("--fingerprint", required=True)
    sr.add_argument("--status", default="draft")
    approve = sub.add_parser("approve-plan")
    approve.add_argument("work_id")
    approve.add_argument("--fingerprint", required=True, help="fingerprint của bảng Requirement đã lưu")
    approve.add_argument("--quote", default="", help="Nguyên văn người dùng duyệt plan")
    change = sub.add_parser("record-change")
    change.add_argument("work_id")
    change.add_argument("--artifact", required=True, help="vd screen:<code>, flow:<code>, persona, theme")
    change.add_argument("--row-ids", required=True, help="ID dòng bảng Requirement, cách nhau dấu phẩy")
    change.add_argument("--reason", required=True)
    link = sub.add_parser("record-review-link")
    link.add_argument("work_id")
    link.add_argument("--url", required=True)
    parity = sub.add_parser("record-parity")
    parity.add_argument("work_id")
    parity.add_argument("--status", choices=("passed", "failed"), required=True)
    parity.add_argument("--evidence", required=True)
    parity.add_argument("--row-ids", default="", help="ID dòng đã kiểm, cách nhau dấu phẩy (passed phải phủ mọi ID)")
    mark = sub.add_parser("mark-step")
    mark.add_argument("work_id")
    mark.add_argument("step")
    mark.add_argument("--status", choices=("completed", "failed"), required=True)
    test = sub.add_parser("record-test")
    test.add_argument("work_id")
    test.add_argument("name")
    test.add_argument("--status", choices=("passed", "failed", "blocked"), required=True)
    test.add_argument("--evidence", default="")
    return parser


def split_ids(text):
    return [x.strip() for x in text.split(",") if x.strip()]


def table_ids(data):
    return [r["id"] for r in (data.get("requirement") or {}).get("rows", [])]


def cmd_create(args, path):
    if path.exists():
        raise GateError(f"work item đã tồn tại: {path}")
    if args.clarification_count not in (0, 1):
        raise GateError("clarificationCount chỉ có thể là 0 hoặc 1")
    assumptions = load_json_arg(args.assumptions, "assumptions")
    base, history = None, []
    if args.requirement_id:
        if not args.requirement_status:
            raise GateError("resume Requirement cần --requirement-status (draft/implementing/published)")
        base = {"requirementId": args.requirement_id, "status": args.requirement_status}
        if args.baseline_table_file:
            try:
                rows = parse_requirement_table(read_file(args.baseline_table_file, "baseline table"))
                validate_rows(rows)
            except ValueError as exc:
                raise GateError(f"bảng baseline không hợp lệ: {exc}")
            history = [r["id"] for r in rows]
    data = {"id": args.work_id, "intent": args.intent, "readOnly": args.read_only,
            "summary": args.summary, "state": "PLANNING", "createdAt": now(),
            "updatedAt": now(), "phase": "INTENT_ANALYSIS", "flowKind": args.flow_kind,
            "clarificationCount": args.clarification_count, "assumptions": assumptions,
            "steps": {}, "tests": [], "mockup": None, "clarification": None, "liveProbe": None,
            "proposal": None, "mockupApproved": None, "requirement": None, "requirementConfirmed": None,
            "savedRequirement": None, "baseRequirement": base, "idHistory": history,
            "retiredIds": split_ids(args.retired_ids), "planApproval": None, "changes": [],
            "reviewLink": None, "parity": [], "invalidatedSteps": [], "events": []}
    event(data, "created", base["requirementId"] if base else "")
    return data


def cmd_transition(args, data):
    target, cur = args.state, data["state"]
    if target == cur:
        event(data, "transition-idempotent", target)
        return
    if target not in TRANSITIONS[cur]:
        raise GateError(f"transition không hợp lệ: {cur} → {target}", attempted=None)
    if gated(data):
        if cur == "PLANNING" and target == "IMPLEMENTING":
            raise GateError("không nhảy thẳng PLANNING → IMPLEMENTING; phải qua WAITING_FOR_PLAN_APPROVAL (B4)", "B5", "B4")
        if cur == "PLANNING" and target == "WAITING_FOR_PLAN_APPROVAL":
            gate(data.get("clarification"), "B1 chưa xong: cần record-clarification", "B4", "B1")
            gate(data.get("liveProbe"), "B1.5 chưa xong: cần record-live-probe (done hoặc skipped)", "B4", "B1.5")
            gate(mockup_approved_valid(data), "B2 chưa xong: cần record-proposal, record-mockup rồi approve-mockup", "B4", "B2")
            gate(requirement_confirmed_valid(data), "B3 chưa xong: cần record-requirement rồi confirm-requirement", "B4", "B3")
            gate(requirement_saved_valid(data), "B3 chưa xong: cần gọi MCP save_requirement rồi record-saved-requirement", "B4", "B3")
            gate(data["phase"] == "PLAN_FINALIZATION", "cần set-phase PLAN_FINALIZATION trước plan approval", "B4", "B4")
        if cur == "WAITING_FOR_PLAN_APPROVAL" and target == "IMPLEMENTING":
            gate(data.get("planApproval"), "B4 chưa xong: người dùng chưa duyệt plan (approve-plan)", "B5", "B4")
        if cur == "IMPLEMENTING" and target == "TESTING":
            gate(data.get("changes"), "B5 chưa xong: chưa khai thay đổi nào (declare_requirement_changes → record-change)", "B6", "B5")
            gate(data.get("reviewLink"), "B5 chưa xong: chưa ghi link review (record-review-link)", "B6", "B5")
        if cur == "TESTING" and target == "COMPLETED":
            last = (data.get("parity") or [None])[-1]
            gate(last and last["status"] == "passed", "B6 chưa xong: parity gần nhất chưa passed", "B6", "B6")
            missing = sorted(set(table_ids(data)) - set(last.get("rowIds") or []))
            gate(not missing, f"B6 chưa xong: parity chưa phủ ID {', '.join(missing)}", "B6", "B6")
        if target == "IMPLEMENTING" and cur == "TESTING":
            data["invalidatedSteps"] = sorted(set(data.get("invalidatedSteps") or []) | {"B5", "B6"})
    data["state"] = target
    event(data, "transition", f"{cur} → {target}; {args.reason}")


def cmd_set_phase(args, data):
    gate(data["state"] == "PLANNING", "chỉ đổi phase khi work item đang PLANNING", None)
    cur, new = PLANNING_PHASES.index(data["phase"]), PLANNING_PHASES.index(args.phase)
    target_step = {"INTENT_ANALYSIS": "B1.5", "MOCKUP_REVIEW": "B2", "REQUIREMENT_CONFIRMATION": "B3", "PLAN_FINALIZATION": "B4"}[args.phase]
    if gated(data):
        gate(new <= cur + 1, f"không được bỏ qua bước: {data['phase']} → {args.phase}", target_step, current_step(data))
        if args.phase == "MOCKUP_REVIEW" and new > cur:
            gate(data.get("clarification"), "B1 chưa xong: cần record-clarification trước khi vào B2", "B2", "B1")
            gate(data.get("liveProbe"), "B1.5 chưa xong: cần record-live-probe (done hoặc skipped) trước khi vào B2", "B2", "B1.5")
        if args.phase == "REQUIREMENT_CONFIRMATION" and new > cur:
            gate(mockup_approved_valid(data), "B2 chưa xong: cần record-proposal + approve-mockup trước khi vào B3", "B3", "B2")
        if args.phase == "PLAN_FINALIZATION":
            gate(requirement_confirmed_valid(data), "B3 chưa xong: cần confirm-requirement trước PLAN_FINALIZATION", "B4", "B3")
            gate(requirement_saved_valid(data), "B3 chưa xong: cần save_requirement + record-saved-requirement trước PLAN_FINALIZATION", "B4", "B3")
        if new < cur:
            invalidate(data, "requirementConfirmed", "planApproval")
            if args.phase == "INTENT_ANALYSIS":
                # chỉ để chạy lại live probe; không mở lượt hỏi UX thứ 2
                invalidate(data, "liveProbe", "proposal", "mockupApproved", "requirement")
            elif args.phase == "MOCKUP_REVIEW":
                invalidate(data, "mockupApproved", "requirement")
            else:
                invalidate(data, "requirement")
            event(data, "invalidate", f"quay lại {args.phase}")
    data["phase"] = args.phase
    event(data, "phase", args.phase)


def cmd_clarification(args, data):
    gate(not data.get("clarification") and data.get("clarificationCount", 0) < 1,
         "clarification UX đã dùng hết budget (chỉ một lượt hỏi)", "B1")
    gate(data["phase"] == "INTENT_ANALYSIS", "record-clarification chỉ trong INTENT_ANALYSIS (B1)", "B1")
    questions = load_json_arg(args.questions, "questions")
    try:
        validate_questions(questions)
    except ValueError as exc:
        raise GateError(str(exc), "B1", ["B1"])
    url = args.tenant_url.strip()
    if url.startswith("skipped"):
        gate(len(url.split(":", 1)) == 2 and url.split(":", 1)[1].strip(), "tenant-url skipped phải kèm lý do: skipped:<lý do>", "B1", "B1")
    else:
        gate(URL_RE.match(url), "tenant-url phải là http(s)://... hoặc skipped:<lý do>", "B1", "B1")
    data["clarification"] = {"questions": questions, "tenantUrl": url, "at": now()}
    data["assumptions"] = load_json_arg(args.assumptions, "assumptions")
    data["clarificationCount"] = 1
    event(data, "clarification", f"1 lượt, {len(questions)} câu UX + địa chỉ web")


def cmd_live_probe(args, data):
    gate(data["state"] == "PLANNING" and data["phase"] == "INTENT_ANALYSIS",
         "record-live-probe chỉ trong INTENT_ANALYSIS (B1.5)", "B1.5")
    gate(data.get("clarification"), "B1 chưa xong: cần hỏi + record-clarification (có địa chỉ web) trước khi chạy thử", "B1.5", "B1")
    probe = load_json_arg(read_file(args.file, "live probe"), "live probe")
    try:
        summary = validate_probe(probe, data["clarification"]["tenantUrl"])
    except ValueError as exc:
        raise GateError(str(exc), "B1.5", ["B1.5"])
    invalidate(data, "proposal", "mockupApproved", "requirement", "requirementConfirmed", "planApproval")
    data["liveProbe"] = {**probe, "summary": summary, "recordedAt": now()}
    event(data, "live-probe", summary)


def cmd_proposal(args, data):
    gate(data["state"] == "PLANNING" and data["phase"] == "MOCKUP_REVIEW", "record-proposal chỉ trong MOCKUP_REVIEW (B2)", "B2")
    gate(data.get("liveProbe"), "B1.5 chưa xong: đề xuất phải gộp kết quả live probe", "B2", "B1.5")
    text = read_file(args.file, "proposal").strip()
    gate(text, "đề xuất rỗng", "B2", "B2")
    invalidate(data, "mockupApproved", "requirement", "requirementConfirmed", "planApproval")
    data["proposal"] = {"text": text, "hash": sha(text), "recordedAt": now()}
    event(data, "proposal", data["proposal"]["hash"])


def cmd_mockup(args, data):
    gate(data["state"] == "PLANNING" and data["phase"] == "MOCKUP_REVIEW", "mockup chỉ được ghi trong PLANNING/MOCKUP_REVIEW (B2)", "B2")
    gate(data.get("proposal") or not gated(data), "chưa in đề xuất: cần record-proposal trước record-mockup", "B2", "B2")
    contract = load_json_arg(args.contract, "mockup contract")
    try:
        metadata = validate_mockup(contract)
    except ValueError as exc:
        raise GateError(str(exc), "B2", ["B2"])
    gate("/preview/" not in args.artifact_url and "localhost:8931" not in args.artifact_url,
         "MCP renderer preview URL không phải journey mockup artifact", "B2", "B2")
    data["mockup"] = {"source": args.source, "artifactUrl": args.artifact_url,
                      "artifactId": args.artifact_id, "contract": contract,
                      "recordedAt": now(), **metadata}
    invalidate(data, "mockupApproved", "requirement", "requirementConfirmed", "planApproval")
    event(data, "mockup", args.source)


def cmd_approve_mockup(args, data):
    gate(data["state"] == "PLANNING" and data["phase"] == "MOCKUP_REVIEW", "approve-mockup chỉ trong PLANNING/MOCKUP_REVIEW (B2)", "B2")
    gate(data.get("mockup"), "chưa có mockup để duyệt", "B2", "B2")
    gate(args.quote.strip(), "cần nguyên văn người dùng đồng ý Mockup", "B2", "B2")
    data["mockupApproved"] = {"quote": args.quote, "mockupHash": mockup_hash(data["mockup"]), "at": now()}
    invalidate(data, "requirement", "requirementConfirmed", "planApproval")
    event(data, "mockup-approved", data["mockupApproved"]["mockupHash"])


def cmd_requirement(args, data):
    gate(data["phase"] == "REQUIREMENT_CONFIRMATION" and data["state"] == "PLANNING",
         "record-requirement chỉ trong PLANNING/REQUIREMENT_CONFIRMATION (B3)", "B3")
    gate(mockup_approved_valid(data), "mockup chưa được người dùng đồng ý (hoặc đã đổi sau khi duyệt)", "B3", "B2")
    try:
        rows = parse_requirement_table(read_file(args.table_file, "bảng requirement"))
        validate_rows(rows)
        check_id_stability(rows, data.get("idHistory") or [], set(data.get("retiredIds") or []))
    except ValueError as exc:
        raise GateError(f"bảng requirement không hợp lệ: {exc}", "B3", ["B3"])
    triggers = [r["trigger"] for r in rows]
    missing = [label for _, label in data["mockup"].get("transitionLabels", {}).items()
               if not any(re.search(rf"\b{label}\b", t) for t in triggers)]
    gate(not missing, f"bảng thiếu transition (cột Trigger phải ghi kèm (T<n>)): {', '.join(missing)}", "B3", "B3")
    fp = table_fingerprint(rows, data["mockupApproved"]["mockupHash"])
    data["requirement"] = {"rows": rows, "rowCount": len(rows), "fingerprint": fp, "recordedAt": now()}
    invalidate(data, "requirementConfirmed", "planApproval")
    event(data, "requirement", fp)


def save_payload(data):
    r, base, saved = data["requirement"], data.get("baseRequirement"), data.get("savedRequirement")
    payload = {"requirementTable": r["rows"], "fingerprint": r["fingerprint"],
               "idempotencyKey": f"{data['id']}-{r['fingerprint']}",
               "assumptions": [a.get("text", a) if isinstance(a, dict) else a for a in (data.get("assumptions") or [])],
               "mockupCanvasUrl": (data.get("mockup") or {}).get("artifactUrl")}
    if base and base["status"] == "published":
        payload["supersedesId"] = base["requirementId"]
    elif saved:
        payload["requirementId"] = saved["requirementId"]
    elif base:
        payload["requirementId"] = base["requirementId"]
    return payload


def cmd_confirm(args, data):
    gate(data["phase"] == "REQUIREMENT_CONFIRMATION" and data["state"] == "PLANNING",
         "confirm-requirement chỉ trong PLANNING/REQUIREMENT_CONFIRMATION (B3)", "B3")
    gate(data.get("requirement") and args.fingerprint == data["requirement"]["fingerprint"],
         "fingerprint không khớp bảng requirement hiện tại", "B3", "B3")
    gate(args.quote.strip(), "cần nguyên văn người dùng xác nhận", "B3", "B3")
    data["requirementConfirmed"] = {"fingerprint": args.fingerprint, "quote": args.quote, "at": now()}
    data["saveRequirementPayload"] = save_payload(data)
    event(data, "requirement-confirmed", args.fingerprint)


def cmd_saved(args, data):
    gate(data["phase"] == "REQUIREMENT_CONFIRMATION" and data["state"] == "PLANNING",
         "record-saved-requirement chỉ trong PLANNING/REQUIREMENT_CONFIRMATION (B3)", "B3")
    gate(requirement_confirmed_valid(data), "người dùng chưa Xác nhận bảng: không được gọi save_requirement", "B3", "B3")
    gate(args.fingerprint == data["requirement"]["fingerprint"], "fingerprint không khớp bảng đã xác nhận", "B3", "B3")
    gate(args.requirement_id.strip(), "thiếu requirementId do save_requirement trả về", "B3", "B3")
    ids = table_ids(data)
    prev = set((data.get("savedRequirement") or {}).get("rowIds") or []) or set(data.get("idHistory") or [])
    data["retiredIds"] = sorted(set(data.get("retiredIds") or []) | (prev - set(ids)))
    data["idHistory"] = sorted(set(data.get("idHistory") or []) | set(ids))
    data["savedRequirement"] = {"requirementId": args.requirement_id, "fingerprint": args.fingerprint,
                                "status": args.status, "rowIds": ids, "at": now()}
    event(data, "requirement-saved", args.requirement_id)


def cmd_approve_plan(args, data):
    gate(data["state"] == "WAITING_FOR_PLAN_APPROVAL", "chỉ approve plan khi đang WAITING_FOR_PLAN_APPROVAL", "B4", "B4")
    if gated(data):
        gate(data.get("mockup"), "plan write cần mockup contract trước approval", "B4", "B2")
        gate(requirement_saved_valid(data), "plan write cần Requirement đã xác nhận và đã lưu (B3)", "B4", "B3")
        gate(args.fingerprint == data["requirement"]["fingerprint"], "fingerprint plan không khớp bảng Requirement đã lưu", "B4", "B4")
    data["planApproval"] = {"fingerprint": args.fingerprint, "quote": args.quote, "approvedAt": now()}
    event(data, "plan-approved", args.fingerprint)


def cmd_change(args, data):
    gate(data["state"] == "IMPLEMENTING", "record-change chỉ khi IMPLEMENTING (B5), sau khi plan đã duyệt", "B5", "B4")
    gate(requirement_saved_valid(data), "chưa có Requirement đã lưu để khai thay đổi", "B5", "B3")
    ids = split_ids(args.row_ids)
    unknown = sorted(set(ids) - set(table_ids(data)))
    gate(ids and not unknown, f"row-ids phải là ID có trong bảng Requirement; sai: {', '.join(unknown) or '(rỗng)'}", "B5", "B5")
    gate(args.reason.strip(), "phải khai lý do thay đổi", "B5", "B5")
    data.setdefault("changes", []).append({"artifact": args.artifact, "rowIds": ids, "reason": args.reason,
                                           "requirementId": data["savedRequirement"]["requirementId"], "at": now()})
    event(data, "change", args.artifact)


def cmd_review_link(args, data):
    gate(data["state"] in ("IMPLEMENTING", "TESTING"), "record-review-link chỉ trong B5/B6", "B5", "B4")
    gate(URL_RE.match(args.url), "link review phải là http(s)://...", "B5", "B5")
    data["reviewLink"] = args.url
    event(data, "review-link", args.url)


def cmd_parity(args, data):
    if gated(data):
        gate(data["state"] == "TESTING", "record-parity chỉ khi TESTING (B6)", "B6", "B5")
    data["parity"].append({"status": args.status, "evidence": args.evidence, "rowIds": split_ids(args.row_ids), "at": now()})
    event(data, "mockup-parity", args.status)


def main():
    args = build_parser().parse_args()
    data = None
    try:
        try:
            path = item_path(args.store, args.work_id)
        except ValueError as exc:
            raise GateError(str(exc))
        if args.command == "create":
            write(path, cmd_create(args, path))
            print(json.dumps(read(path), ensure_ascii=False, indent=2, sort_keys=True))
            return
        if not path.exists():
            raise GateError(f"không tìm thấy work item: {path}")
        data = read(path)
        if args.command == "progress":
            print(progress_table(data, args.short))
            return
        if args.command == "show":
            print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
            return
        before = done_set(data)
        handlers = {
            "transition": cmd_transition, "set-phase": cmd_set_phase, "record-clarification": cmd_clarification,
            "record-live-probe": cmd_live_probe, "record-proposal": cmd_proposal, "record-mockup": cmd_mockup,
            "approve-mockup": cmd_approve_mockup, "record-requirement": cmd_requirement,
            "confirm-requirement": cmd_confirm, "record-saved-requirement": cmd_saved,
            "approve-plan": cmd_approve_plan, "record-change": cmd_change,
            "record-review-link": cmd_review_link, "record-parity": cmd_parity,
        }
        if args.command in handlers:
            handlers[args.command](args, data)
        elif args.command == "mark-step":
            current = data["steps"].get(args.step)
            gate(not (current == "completed" and args.status != "completed"), "không thể ghi đè step completed", None)
            data["steps"][args.step] = args.status
            event(data, "step", f"{args.step}: {args.status}")
        elif args.command == "record-test":
            data["tests"].append({"name": args.name, "status": args.status, "evidence": args.evidence, "at": now()})
            event(data, "test", f"{args.name}: {args.status}")
        lost = before - done_set(data)
        if lost:
            data["invalidatedSteps"] = sorted(set(data.get("invalidatedSteps") or []) | lost, key=STEP_INDEX.get)
            event(data, "invalidate-steps", ", ".join(sorted(lost, key=STEP_INDEX.get)))
        write(path, data)
        print(json.dumps(read(path), ensure_ascii=False, indent=2, sort_keys=True))
    except GateError as exc:
        out = {"ok": False, "error": str(exc), "attemptedStep": exc.attempted, "missingGates": exc.missing}
        if data is not None:
            cur = current_step(data)
            out.update({"currentStep": cur, "nextAction": NEXT_ACTION[cur], "progress": progress_table(data),
                        "instruction": "Dừng. In nguyên `progress` ra chat, nói đang ở bước nào và sai ở đâu (kèm phương án + đề xuất), rồi quay về làm đúng bước currentStep."})
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()
