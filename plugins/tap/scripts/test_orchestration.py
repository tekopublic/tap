#!/usr/bin/env python3
"""Dependency-free regression suite for TAP gateway, state, and mockup assets."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE, MOCKUP = ROOT / "scripts/work_item_state.py", ROOT / "scripts/build_journey_mockup.py"

def run(store, *args, ok=True):
    r = subprocess.run([sys.executable, str(STATE), "--store", str(store), *args], text=True, capture_output=True)
    if (r.returncode == 0) != ok: raise AssertionError(r.stdout + r.stderr)
    return r

def multi_contract():
    screens = [{"id": f"screen-0{i}", "number": i, "name": n, "goal": n, "laneIds": ["happy"], "status": st, "mcpRef": ("code-%d" % i if st != "new" else None),
                "chat": {"messages": [{"role": "assistant", "text": n}]}, "display": {"title": n, "cards": []}}
               for i, (n, st) in enumerate((("Nhập nhu cầu", "existing"), ("Kết quả", "modify"), ("Chi tiết", "new"), ("Gợi ý", "new")), 1)]
    return {"schemaVersion": 2, "title": "Multi-screen fixture", "states": ["default"], "actions": ["search"], "expectedUi": ["screen"],
            "chat": {}, "display": {}, "fixtures": {"label": "fixture-only"}, "transitions": [], "screens": screens,
            "flowMap": {"startScreenId": "screen-01", "lanes": [{"id":"happy","label":"Happy path","kind":"happy-path"}, {"id":"empty","label":"Empty state","kind":"empty-state"}, {"id":"error","label":"Error/Fallback","kind":"error-fallback"}], "transitions": [{"id":"search","fromScreenId":"screen-01","toScreenId":"screen-02","laneId":"happy","trigger":"submit","ctaLabel":"Tìm kiếm","expectedResult":"Kết quả"}, {"id":"detail","fromScreenId":"screen-02","toScreenId":"screen-03","laneId":"happy","trigger":"click","ctaLabel":"Xem chi tiết","expectedResult":"Chi tiết"}, {"id":"empty","fromScreenId":"screen-02","toScreenId":"screen-04","laneId":"empty","trigger":"none","ctaLabel":"No results","expectedResult":"Gợi ý"}, {"id":"retry","fromScreenId":"screen-03","toScreenId":"screen-02","laneId":"error","trigger":"retry","ctaLabel":"Thử lại","expectedResult":"Kết quả","fallback":"screen-02"}]}}

Q = json.dumps([{"q": "Mục tiêu?", "options": ["A. Bán hàng", "B. Tư vấn"], "recommended": "A", "reason": "tenant bán lẻ"}], ensure_ascii=False)
A = '[{"id":"A1","text":"fixture","userVisible":true}]'
URL = "http://localhost:8041"
HEAD = "| ID | Scope | Trigger | Điều kiện trước | Chat panel | Display panel | Hệ thống | Không được làm | Pass rate |\n|---|---|---|---|---|---|---|---|---|\n"
def row(rid, trig, rate="100%", scope="issue 319"):
    return f"| {rid} | {scope} | {trig} | có dữ liệu | chat | display | đọc | sai | {rate} |\n"
TABLE = HEAD + "".join(row(f"SHOP-SRC-00{i}", f"[Chat] bước (T{i})") for i in range(1, 5))
PROBE = json.dumps({"status": "done", "tool": "claude-in-chrome", "useCases": [
    {"id": "UC1", "input": "tìm laptop", "expected": "có kết quả", "actual": "có 12 kết quả", "result": "pass"}]}, ensure_ascii=False)
CONTRACT = json.dumps(multi_contract(), ensure_ascii=False)

def table_file(tmp, text=TABLE, name="req.md"):
    f = Path(tmp) / name; f.write_text(text, encoding="utf-8"); return str(f)

def show(store, w):
    return json.loads(run(store, "show", w).stdout)

def fp(store, w):
    return show(store, w)["requirement"]["fingerprint"]

def gate_err(r):
    return json.loads(r.stdout)

def to_b1(store, tmp, w, kind="screen"):
    run(store, "create", w, "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", kind)
    run(store, "record-clarification", w, "--assumptions", A, "--questions", Q, "--tenant-url", URL)

def to_b2(store, tmp, w, kind="screen"):
    to_b1(store, tmp, w, kind)
    run(store, "record-live-probe", w, "--file", table_file(tmp, PROBE, f"{w}-probe.json"))
    run(store, "set-phase", w, "MOCKUP_REVIEW")
    run(store, "record-proposal", w, "--file", table_file(tmp, "Hiện trạng / Khoảng trống / Đề xuất", f"{w}-prop.md"))
    run(store, "record-mockup", w, "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", CONTRACT)
    run(store, "approve-mockup", w, "--quote", "đồng ý Mockup")

def to_b3(store, tmp, w, kind="screen", table=TABLE, rid="req-1"):
    to_b2(store, tmp, w, kind)
    run(store, "set-phase", w, "REQUIREMENT_CONFIRMATION")
    run(store, "record-requirement", w, "--table-file", table_file(tmp, table, f"{w}-t.md"))
    run(store, "confirm-requirement", w, "--fingerprint", fp(store, w), "--quote", "Xác nhận")
    run(store, "record-saved-requirement", w, "--requirement-id", rid, "--fingerprint", fp(store, w))

def test_full_flow():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp); w = "write-1"
        run(store, "create", w, "--intent", "STORE_FRONT", "--summary", "multi", "--flow-kind", "screen")
        run(store, "transition", w, "WAITING_FOR_PLAN_APPROVAL", ok=False)
        run(store, "transition", w, "IMPLEMENTING", ok=False)
        run(store, "set-phase", w, "MOCKUP_REVIEW", ok=False)
        run(store, "record-clarification", w, "--assumptions", A, "--questions", Q, "--tenant-url", URL)
        e = gate_err(run(store, "set-phase", w, "MOCKUP_REVIEW", ok=False))  # chưa live probe
        assert e["currentStep"] == "B1.5" and e["missingGates"] == ["B1.5"] and "| B1.5 |" in e["progress"], e
        run(store, "record-live-probe", w, "--file", table_file(tmp, PROBE, "probe.json"))
        run(store, "set-phase", w, "MOCKUP_REVIEW")
        run(store, "record-mockup", w, "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", CONTRACT, ok=False)  # chưa đề xuất
        run(store, "record-proposal", w, "--file", table_file(tmp, "Đề xuất", "p.md"))
        run(store, "record-mockup", w, "--source", "html-artifact", "--artifact-url", "x.html", "--artifact-id", "j", "--contract", CONTRACT, ok=False)
        run(store, "record-mockup", w, "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", CONTRACT)
        run(store, "set-phase", w, "REQUIREMENT_CONFIRMATION", ok=False)
        run(store, "approve-mockup", w, "--quote", "đồng ý Mockup")
        run(store, "set-phase", w, "PLAN_FINALIZATION", ok=False)
        run(store, "set-phase", w, "REQUIREMENT_CONFIRMATION")
        run(store, "record-requirement", w, "--table-file", table_file(tmp, TABLE.replace("(T4)", "")), ok=False)
        run(store, "record-requirement", w, "--table-file", table_file(tmp))
        run(store, "record-saved-requirement", w, "--requirement-id", "req-1", "--fingerprint", fp(store, w), ok=False)  # chưa Xác nhận
        run(store, "confirm-requirement", w, "--fingerprint", "sai", "--quote", "ok", ok=False)
        run(store, "confirm-requirement", w, "--fingerprint", fp(store, w), "--quote", "Xác nhận")
        assert show(store, w)["saveRequirementPayload"]["requirementTable"][0]["passRate"] == "100%"
        run(store, "set-phase", w, "PLAN_FINALIZATION", ok=False)  # chưa save_requirement
        run(store, "record-saved-requirement", w, "--requirement-id", "req-1", "--fingerprint", fp(store, w))
        run(store, "set-phase", w, "PLAN_FINALIZATION"); run(store, "transition", w, "WAITING_FOR_PLAN_APPROVAL")
        run(store, "transition", w, "IMPLEMENTING", ok=False)
        run(store, "approve-plan", w, "--fingerprint", "khac", ok=False)
        run(store, "approve-plan", w, "--fingerprint", fp(store, w), "--quote", "duyệt")
        run(store, "transition", w, "IMPLEMENTING")
        run(store, "transition", w, "TESTING", ok=False)  # chưa khai thay đổi
        run(store, "record-change", w, "--artifact", "screen:x", "--row-ids", "SHOP-SRC-999", "--reason", "r", ok=False)
        run(store, "record-change", w, "--artifact", "screen:x", "--row-ids", "SHOP-SRC-001,SHOP-SRC-002", "--reason", "đổi CTA")
        run(store, "transition", w, "TESTING", ok=False)  # chưa link review
        run(store, "record-review-link", w, "--url", "https://admin.example/review/1")
        run(store, "transition", w, "TESTING")
        run(store, "record-parity", w, "--status", "passed", "--evidence", "trace", "--row-ids", "SHOP-SRC-001")
        run(store, "transition", w, "COMPLETED", ok=False)  # parity chưa phủ đủ ID
        run(store, "record-parity", w, "--status", "passed", "--evidence", "trace", "--row-ids", ",".join(f"SHOP-SRC-00{i}" for i in range(1, 5)))
        run(store, "transition", w, "COMPLETED")
        assert "| B6 |" in run(store, "progress", w).stdout and "Xong" in run(store, "progress", w).stdout

def test_clarification_rules():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp)
        run(store, "create", "q-1", "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", "screen")
        bad = [("[]", URL), (json.dumps([{"q": f"q{i}", "options": ["a", "b"], "recommended": "a", "reason": "r"} for i in range(4)]), URL),
               ('[{"q":"a","default":"b"}]', URL),  # thiếu options (R5)
               ('[{"q":"a","options":["x"],"recommended":"x","reason":"r"}]', URL),  # < 2 phương án
               ('[{"q":"a","options":["x","y"],"recommended":"x"}]', URL),  # thiếu reason
               (Q, "localhost:8041"), (Q, "skipped")]
        for questions, url in bad:
            run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", questions, "--tenant-url", url, ok=False)
        run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", Q, "--tenant-url", "skipped:chưa có môi trường")
        run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", Q, "--tenant-url", URL, ok=False)  # chỉ một lượt
        done_probe = table_file(tmp, PROBE, "probe.json")
        run(store, "record-live-probe", "q-1", "--file", done_probe, ok=False)  # url skipped → chỉ được skipped
        run(store, "record-live-probe", "q-1", "--file", table_file(tmp, '{"status":"skipped"}', "s0.json"), ok=False)  # thiếu lý do
        run(store, "record-live-probe", "q-1", "--file", table_file(tmp, '{"status":"skipped","reason":"không có trình duyệt"}', "s.json"))
        run(store, "set-phase", "q-1", "MOCKUP_REVIEW")
        run(store, "record-proposal", "q-1", "--file", table_file(tmp, "Đề xuất", "p.md"))
        for mutate in (lambda c: c["screens"][0].pop("status"), lambda c: c["screens"][1].pop("mcpRef"),
                       lambda c: c["screens"][2].update(display={}), lambda c: c["screens"][3].update(chat={})):
            c = multi_contract(); mutate(c)
            run(store, "record-mockup", "q-1", "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", json.dumps(c), ok=False)

def test_table_rules():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp); to_b2(store, tmp, "t-1"); run(store, "set-phase", "t-1", "REQUIREMENT_CONFIRMATION")
        old6 = "| Trigger | Precondition | Chat panel | Display panel | System | Must not |\n|---|---|---|---|---|---|\n| [Chat] a (T1) | b | c | d | e | f |\n"
        rows = lambda *r: HEAD + "".join(r) + "".join(row(f"SHOP-SRC-00{i}", f"[Chat] bước (T{i})") for i in range(2, 5))
        bad = [old6,
               rows(row("SHOP-SRC-001", "[Chat] (T1)").replace("| sai |", "|  |")),  # ô trống
               rows(row("SHOP-SRC-001", "[Chat] (T1)", scope="Changelog")),
               rows(row("SHOP-SRC-001", "[Chat] (T1)", scope="#319")),
               rows(row("SHOP-SRC-001", "[Chat] (T1)", rate="90%")),
               rows(row("SHOP-SRC-001", "[Display click] (T1)", rate="80%")),
               rows(row("SHOP-SRC-001", "[Chat] a [Chat chip] b (T1)", rate="80%")),
               rows(row("SHOP-SRC-002", "[Chat] (T1)")),  # trùng ID
               rows(row("abc", "[Chat] (T1)"))]
        for i, t in enumerate(bad):
            run(store, "record-requirement", "t-1", "--table-file", table_file(tmp, t, f"b{i}.md"), ok=False)
        run(store, "record-requirement", "t-1", "--table-file", table_file(tmp, rows(row("SHOP-SRC-001", "[Chat] hỏi (T1) 🔒", rate="80%", scope="issue 319 🔒"))))

def test_id_stability():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp)
        base = HEAD + row("SHOP-SRC-001", "[Chat] a") + row("SHOP-SRC-002", "[Chat] b") + row("SHOP-SRC-003A", "[Chat] c")
        run(store, "create", "id-1", "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", "screen", "--requirement-id", "req-9",
            "--requirement-status", "draft", "--baseline-table-file", table_file(tmp, base, "base.md"), "--retired-ids", "SHOP-SRC-004")
        run(store, "record-clarification", "id-1", "--assumptions", A, "--questions", Q, "--tenant-url", URL)
        run(store, "record-live-probe", "id-1", "--file", table_file(tmp, PROBE, "probe.json")); run(store, "set-phase", "id-1", "MOCKUP_REVIEW")
        run(store, "record-proposal", "id-1", "--file", table_file(tmp, "Đề xuất", "p.md"))
        run(store, "record-mockup", "id-1", "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", CONTRACT)
        run(store, "approve-mockup", "id-1", "--quote", "ok"); run(store, "set-phase", "id-1", "REQUIREMENT_CONFIRMATION")
        keep = row("SHOP-SRC-001", "[Chat] (T1)") + row("SHOP-SRC-002", "[Chat] (T2)") + row("SHOP-SRC-003A", "[Chat] (T3)")
        for i, extra in enumerate((row("SHOP-SRC-004", "[Chat] (T4)"),   # ID đã xoá, dùng lại
                                   row("SHOP-SRC-002B", "[Chat] (T4)"),  # case mới của usecase chỉ có một case: ok là B — kiểm ở dưới
                                   row("SHOP-SRC-003A", "[Chat] x (T4)"),  # trùng
                                   row("SHOP-SRC-001", "[Chat] (T4)") if False else row("SHOP-SRC-007", "[Chat] (T4)"))):  # nhảy số
            ok = i == 1
            run(store, "record-requirement", "id-1", "--table-file", table_file(tmp, HEAD + keep + extra, f"i{i}.md"), ok=ok)
        run(store, "record-requirement", "id-1", "--table-file", table_file(tmp, HEAD + keep + row("SHOP-SRC-003A", "[Chat]").replace("SHOP-SRC-003A", "SHOP-SRC-003B").replace("[Chat] |", "[Chat] (T4) |"), "i5.md"))
        run(store, "record-requirement", "id-1", "--table-file", table_file(tmp, HEAD + keep + row("SHOP-SRC-005", "[Chat] (T4)"), "i6.md"))
        run(store, "confirm-requirement", "id-1", "--fingerprint", fp(store, "id-1"), "--quote", "Xác nhận")
        assert show(store, "id-1")["saveRequirementPayload"]["requirementId"] == "req-9"
        # bản đã Public → supersedesId
        run(store, "create", "id-2", "--intent", "S", "--summary", "x", "--flow-kind", "screen", "--requirement-id", "req-8", "--requirement-status", "published")
        run(store, "create", "id-3", "--intent", "S", "--summary", "x", "--requirement-id", "req-8", ok=False)  # thiếu status

def test_confirmations_invalidate():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp)
        def reach_plan(w):
            to_b3(store, tmp, w); run(store, "set-phase", w, "PLAN_FINALIZATION")
        reach_plan("inv-1"); run(store, "set-phase", "inv-1", "REQUIREMENT_CONFIRMATION")
        d = show(store, "inv-1"); assert d["requirementConfirmed"] is None and d["requirement"] is None and "B3" in d["invalidatedSteps"]
        run(store, "transition", "inv-1", "WAITING_FOR_PLAN_APPROVAL", ok=False); run(store, "set-phase", "inv-1", "PLAN_FINALIZATION", ok=False)
        assert "Đang ở đây** (làm lại)" in run(store, "progress", "inv-1").stdout
        reach_plan("inv-2"); run(store, "set-phase", "inv-2", "MOCKUP_REVIEW")
        run(store, "record-mockup", "inv-2", "--source", "claude-design", "--artifact-url", "claude-design://j2", "--artifact-id", "j2", "--contract", CONTRACT)
        d = show(store, "inv-2"); assert d["mockupApproved"] is None and d["requirement"] is None and {"B2", "B3"} <= set(d["invalidatedSteps"])
        out = run(store, "progress", "inv-2").stdout; assert "Bị mất hiệu lực" in out, out
        run(store, "set-phase", "inv-2", "REQUIREMENT_CONFIRMATION", ok=False)
        # quay lại B1.5 để chạy lại live probe: được, nhưng không hỏi lượt 2
        reach_plan("inv-4"); run(store, "set-phase", "inv-4", "INTENT_ANALYSIS")
        run(store, "record-clarification", "inv-4", "--assumptions", A, "--questions", Q, "--tenant-url", URL, ok=False)
        run(store, "set-phase", "inv-4", "MOCKUP_REVIEW", ok=False)
        run(store, "record-live-probe", "inv-4", "--file", table_file(tmp, PROBE, "p4.json")); run(store, "set-phase", "inv-4", "MOCKUP_REVIEW")
        run(store, "create", "inv-3", "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", "screen")
        run(store, "approve-plan", "inv-3", "--fingerprint", "x", ok=False)
        # config cũng bị gắn cổng (Q1=B); read-only thì không
        run(store, "create", "cfg-1", "--intent", "CONFIG", "--summary", "x", "--flow-kind", "config")
        run(store, "transition", "cfg-1", "WAITING_FOR_PLAN_APPROVAL", ok=False)
        run(store, "create", "ro-1", "--intent", "STATUS", "--summary", "x", "--read-only")
        assert "chỉ đọc" in run(store, "progress", "ro-1").stdout

def test_builder_v1_v2():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        v1 = {"title":"Legacy","chat":{"messages":[]},"display":{"title":"Display","cards":[]},"transitions":[]}
        for name, scenario in (("v1",v1),("v2",multi_contract())):
            src, out = root / f"{name}.json", root / f"{name}.html"; src.write_text(json.dumps(scenario, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(MOCKUP), "--scenario", str(src), "--out", str(out)], text=True, capture_output=True)
            if r.returncode: raise AssertionError(r.stdout+r.stderr)
            html = out.read_text(encoding="utf-8"); assert "Fixture-only" in html and "fingerprint" in html and "localhost:8931/preview" not in html
        html = (root / "v2.html").read_text(encoding="utf-8")
        for text in ("Flow map", "Happy path", "Empty state", "Error/Fallback", "transitionId", "CTA") : assert text in html

def test_mcp_pref():
    with tempfile.TemporaryDirectory() as tmp:
        f = str(Path(tmp) / "p.json"); cmd = [sys.executable, str(ROOT / "scripts/mcp_pref.py"), "--file", f]
        out = lambda *a: subprocess.run(cmd + list(a), text=True, capture_output=True, check=True).stdout
        assert json.loads(out("get"))["server"] is None
        out("set", "phongvu-tap-mcp"); assert json.loads(out("get"))["server"] == "phongvu-tap-mcp"
        out("clear"); assert json.loads(out("get"))["server"] is None

def test_error_report():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_error_report.py"), "--category", "server-error", "--server", "phongvu-tap-mcp", "--env", "PROD",
                        "--message", "fail Bearer abc.def-123 token=xyz sk-FAKEtestKEY0000000000 a@b.vn 0912345678"], text=True, capture_output=True, check=True).stdout
    assert "[TAP - BÁO LỖI]" in r and "Google Chat TAP" in r and "Chuyện gì đã xảy ra" in r
    for leak in ("abc.def-123", "xyz", "FAKEtestKEY", "a@b.vn", "0912345678"): assert leak not in r, leak

def test_gateway_assets():
    orchestrator = (ROOT / "skills/tap-orchestration/SKILL.md").read_text(encoding="utf-8")
    assert "Claude Design (canvas)" in orchestrator and "Không có fallback HTML." in orchestrator
    assert "Sơ đồ nối màn hình" in orchestrator and "T<số bước>" in orchestrator
    assert "build_error_report.py" in orchestrator
    for marker in ("B1 —", "B1.5 —", "B2 —", "B3 —", "B4 —", "B5 —", "B6 —", "Cổng cứng", "record-clarification", "record-live-probe", "record-proposal", "approve-mockup", "record-requirement", "confirm-requirement", "save_requirement", "record-saved-requirement", "declare_requirement_changes", "progress", "Phát hiện sai bước", "Khung hỏi", "tối thiểu 1", "tối đa 3", "9 cột"):
        assert marker in orchestrator, marker
    assert "MCP preflight" in orchestrator and "mcp_pref.py" in orchestrator
    assert "không từ chối" in orchestrator and "Không có skill riêng cho giỏ hàng" in orchestrator and "clarificationCount" in orchestrator
    assert "không còn hỗ trợ capability giỏ hàng" not in orchestrator and not (ROOT / "skills" / ("tap-shopper" + "-cart")).exists()
    for command in (ROOT / "commands").glob("*.md"):
        text = command.read_text(encoding="utf-8"); assert "tap-orchestration" in text and "Không gọi worker hoặc MCP tool trực tiếp" in text
    for name in ("tap-status","tap-screen","tap-flow","tap-config","tap-chat-display"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8"); assert "Delegated-by: tap-orchestration" in text and "workItemId" in text
        if name != "tap-status": assert "requirementId" in text and "BLOCKED" in text, name
    # plugin 3.3.0: AI không Public — không skill/reference nào còn hướng dẫn gọi publish_screen/flow/persona
    import re as _re
    allowed = ("tool-index.md", "permissions.md", "renderer-pitfalls.md")
    for f in (ROOT / "skills").rglob("*.md"):
        if f.name in allowed: continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if _re.search(r"publish_(screen|interaction_flow|persona)", line):
                assert _re.search(r"[Kk]hông( bao giờ)?( gọi)? `?publish|không còn gọi", line), f"{f}: {line[:120]}"

if __name__ == "__main__":
    test_full_flow(); test_clarification_rules(); test_table_rules(); test_id_stability(); test_confirmations_invalidate(); test_builder_v1_v2(); test_mcp_pref(); test_error_report(); test_gateway_assets(); print("✔ TAP orchestration tests passed")
