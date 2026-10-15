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

Q = '[{"q":"Mục tiêu?","default":"Bán hàng"}]'
A = '[{"id":"A1","text":"fixture","userVisible":true}]'
TABLE = "| Trigger | Precondition | Chat panel | Display panel | System | Must not |\n|---|---|---|---|---|---|\n" + "".join(
    f"| [Chat] bước (T{i}) | có dữ liệu | chat | display | đọc | sai |\n" for i in range(1, 5))

def table_file(tmp, text=TABLE, name="req.md"):
    f = Path(tmp) / name; f.write_text(text, encoding="utf-8"); return str(f)

def fp(store, w):
    return json.loads(run(store, "show", w).stdout)["requirement"]["fingerprint"]

def test_state_and_clarification():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp); contract = json.dumps(multi_contract(), ensure_ascii=False)
        run(store, "create", "write-1", "--intent", "STORE_FRONT", "--summary", "multi", "--flow-kind", "screen")
        run(store, "transition", "write-1", "WAITING_FOR_PLAN_APPROVAL", ok=False)
        run(store, "transition", "write-1", "IMPLEMENTING", ok=False)  # lỗ hổng PLANNING → IMPLEMENTING đã vá
        run(store, "set-phase", "write-1", "MOCKUP_REVIEW", ok=False)
        run(store, "record-clarification", "write-1", "--assumptions", A, "--questions", Q)
        run(store, "set-phase", "write-1", "MOCKUP_REVIEW")
        run(store, "record-mockup", "write-1", "--source", "html-artifact", "--artifact-url", "mockups/journey.html", "--artifact-id", "journey", "--contract", contract, ok=False)
        run(store, "record-mockup", "write-1", "--source", "claude-design", "--artifact-url", "claude-design://journey", "--artifact-id", "journey", "--contract", contract)
        run(store, "set-phase", "write-1", "REQUIREMENT_CONFIRMATION", ok=False)  # chưa approve-mockup
        run(store, "approve-mockup", "write-1", "--quote", "đồng ý với Mockup")
        run(store, "set-phase", "write-1", "PLAN_FINALIZATION", ok=False)  # bỏ qua B3
        run(store, "set-phase", "write-1", "REQUIREMENT_CONFIRMATION")
        run(store, "record-requirement", "write-1", "--table-file", table_file(tmp, TABLE.replace("(T4)", "")), ok=False)  # thiếu transition T4
        run(store, "record-requirement", "write-1", "--table-file", table_file(tmp, "| Trigger | Precondition |\n|---|---|\n| a | b |\n"), ok=False)  # sai cột
        run(store, "record-requirement", "write-1", "--table-file", table_file(tmp))
        run(store, "confirm-requirement", "write-1", "--fingerprint", "sai", "--quote", "ok", ok=False)
        run(store, "transition", "write-1", "WAITING_FOR_PLAN_APPROVAL", ok=False)  # chưa confirm
        run(store, "confirm-requirement", "write-1", "--fingerprint", fp(store, "write-1"), "--quote", "xác nhận requirement + mockup")
        run(store, "set-phase", "write-1", "PLAN_FINALIZATION"); run(store, "transition", "write-1", "WAITING_FOR_PLAN_APPROVAL")
        run(store, "transition", "write-1", "IMPLEMENTING", ok=False); run(store, "approve-plan", "write-1", "--fingerprint", "v2-abc")
        run(store, "transition", "write-1", "IMPLEMENTING"); run(store, "transition", "write-1", "TESTING"); run(store, "record-parity", "write-1", "--status", "passed", "--evidence", "screen/lane/transition trace")
        run(store, "transition", "write-1", "COMPLETED"); data = json.loads(run(store, "show", "write-1").stdout)
        assert data["clarificationCount"] == 1 and data["mockup"]["screenIds"] == ["screen-01", "screen-02", "screen-03", "screen-04"]
        assert data["mockup"]["transitionLabels"]["search"] == "T1" and data["clarification"]["questions"][0]["q"]

def test_four_questions_rejected_and_mockup_rules():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp)
        run(store, "create", "q-1", "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", "screen")
        run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", "[]", ok=False)
        four = json.dumps([{"q": f"q{i}", "default": "d"} for i in range(4)])
        run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", four, ok=False)
        run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", '[{"q":"a"}]', ok=False)
        run(store, "record-clarification", "q-1", "--assumptions", A, "--questions", json.dumps([{"q": f"q{i}", "default": "d"} for i in range(3)]))
        run(store, "set-phase", "q-1", "MOCKUP_REVIEW")
        for mutate in (lambda c: c["screens"][0].pop("status"), lambda c: c["screens"][1].pop("mcpRef"),
                       lambda c: c["screens"][2].update(display={}), lambda c: c["screens"][3].update(chat={})):
            c = multi_contract(); mutate(c)
            run(store, "record-mockup", "q-1", "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", json.dumps(c), ok=False)

def test_confirmations_invalidate():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp); contract = json.dumps(multi_contract(), ensure_ascii=False)
        def reach_plan(w):
            run(store, "create", w, "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", "screen")
            run(store, "record-clarification", w, "--assumptions", A, "--questions", Q); run(store, "set-phase", w, "MOCKUP_REVIEW")
            run(store, "record-mockup", w, "--source", "claude-design", "--artifact-url", "claude-design://j", "--artifact-id", "j", "--contract", contract)
            run(store, "approve-mockup", w, "--quote", "đồng ý"); run(store, "set-phase", w, "REQUIREMENT_CONFIRMATION")
            run(store, "record-requirement", w, "--table-file", table_file(tmp)); run(store, "confirm-requirement", w, "--fingerprint", fp(store, w), "--quote", "ok")
            run(store, "set-phase", w, "PLAN_FINALIZATION")
        # (d1) sửa bảng sau xác nhận => mất hiệu lực
        reach_plan("inv-1"); run(store, "set-phase", "inv-1", "REQUIREMENT_CONFIRMATION")
        d = json.loads(run(store, "show", "inv-1").stdout); assert d["requirementConfirmed"] is None and d["requirement"] is None
        run(store, "transition", "inv-1", "WAITING_FOR_PLAN_APPROVAL", ok=False); run(store, "set-phase", "inv-1", "PLAN_FINALIZATION", ok=False)
        # (d2) đổi mockup sau xác nhận => mất hiệu lực mọi thứ phía sau
        reach_plan("inv-2"); run(store, "set-phase", "inv-2", "MOCKUP_REVIEW")
        run(store, "record-mockup", "inv-2", "--source", "claude-design", "--artifact-url", "claude-design://j2", "--artifact-id", "j2", "--contract", contract)
        d = json.loads(run(store, "show", "inv-2").stdout)
        assert d["mockupApproved"] is None and d["requirement"] is None and d["requirementConfirmed"] is None
        run(store, "set-phase", "inv-2", "REQUIREMENT_CONFIRMATION", ok=False)
        # approve-plan chặn khi chưa xác nhận requirement
        run(store, "create", "inv-3", "--intent", "STORE_FRONT", "--summary", "x", "--flow-kind", "screen")
        run(store, "approve-plan", "inv-3", "--fingerprint", "x", ok=False)

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
                        "--message", "fail Bearer abc.def-123 token=xyz sk-VzqtolULllXGPDTTBtc9gg a@b.vn 0912345678"], text=True, capture_output=True, check=True).stdout
    assert "[TAP - BÁO LỖI]" in r and "Google Chat TAP" in r and "Chuyện gì đã xảy ra" in r
    for leak in ("abc.def-123", "xyz", "VzqtolULll", "a@b.vn", "0912345678"): assert leak not in r, leak

def test_gateway_assets():
    orchestrator = (ROOT / "skills/tap-orchestration/SKILL.md").read_text(encoding="utf-8")
    assert "Claude Design (canvas)" in orchestrator and "Không có fallback HTML." in orchestrator
    assert "Sơ đồ nối màn hình" in orchestrator and "T<số bước>" in orchestrator
    assert "build_error_report.py" in orchestrator
    for marker in ("B1 —", "B2 —", "B3 —", "Cổng cứng", "record-clarification", "approve-mockup", "record-requirement", "confirm-requirement", "tối thiểu 1", "tối đa 3"):
        assert marker in orchestrator, marker
    assert "MCP preflight" in orchestrator and "mcp_pref.py" in orchestrator
    assert "không từ chối" in orchestrator and "Không có skill riêng cho giỏ hàng" in orchestrator and "clarificationCount" in orchestrator
    assert "không còn hỗ trợ capability giỏ hàng" not in orchestrator and not (ROOT / "skills" / ("tap-shopper" + "-cart")).exists()
    for command in (ROOT / "commands").glob("*.md"):
        text = command.read_text(encoding="utf-8"); assert "tap-orchestration" in text and "Không gọi worker hoặc MCP tool trực tiếp" in text
    for name in ("tap-status","tap-screen","tap-flow","tap-config","tap-chat-display"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8"); assert "Delegated-by: tap-orchestration" in text and "workItemId" in text

if __name__ == "__main__":
    test_state_and_clarification(); test_four_questions_rejected_and_mockup_rules(); test_confirmations_invalidate(); test_builder_v1_v2(); test_mcp_pref(); test_error_report(); test_gateway_assets(); print("✔ TAP orchestration tests passed")
