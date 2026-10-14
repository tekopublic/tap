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
    screens = [{"id": f"screen-0{i}", "number": i, "name": n, "goal": n, "laneIds": ["happy"], "chat": {}, "display": {}}
               for i, n in enumerate(("Nhập nhu cầu", "Kết quả", "Chi tiết", "Gợi ý"), 1)]
    return {"schemaVersion": 2, "title": "Multi-screen fixture", "states": ["default"], "actions": ["search"], "expectedUi": ["screen"],
            "chat": {}, "display": {}, "fixtures": {"label": "fixture-only"}, "transitions": [], "screens": screens,
            "flowMap": {"startScreenId": "screen-01", "lanes": [{"id":"happy","label":"Happy path","kind":"happy-path"}, {"id":"empty","label":"Empty state","kind":"empty-state"}, {"id":"error","label":"Error/Fallback","kind":"error-fallback"}], "transitions": [{"id":"search","fromScreenId":"screen-01","toScreenId":"screen-02","laneId":"happy","trigger":"submit","ctaLabel":"Tìm kiếm","expectedResult":"Kết quả"}, {"id":"detail","fromScreenId":"screen-02","toScreenId":"screen-03","laneId":"happy","trigger":"click","ctaLabel":"Xem chi tiết","expectedResult":"Chi tiết"}, {"id":"empty","fromScreenId":"screen-02","toScreenId":"screen-04","laneId":"empty","trigger":"none","ctaLabel":"No results","expectedResult":"Gợi ý"}, {"id":"retry","fromScreenId":"screen-03","toScreenId":"screen-02","laneId":"error","trigger":"retry","ctaLabel":"Thử lại","expectedResult":"Kết quả","fallback":"screen-02"}]}}

def test_state_and_clarification():
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp); contract = json.dumps(multi_contract(), ensure_ascii=False)
        run(store, "create", "write-1", "--intent", "STORE_FRONT", "--summary", "multi", "--flow-kind", "screen")
        run(store, "transition", "write-1", "WAITING_FOR_PLAN_APPROVAL", ok=False)
        run(store, "record-clarification", "write-1", "--assumptions", '[{"id":"A1","text":"fixture","userVisible":true}]')
        run(store, "record-clarification", "write-1", "--assumptions", "[]", ok=False)
        run(store, "set-phase", "write-1", "MOCKUP_REVIEW")
        run(store, "record-mockup", "write-1", "--source", "html-artifact", "--artifact-url", "mockups/journey.html", "--artifact-id", "journey", "--contract", contract, ok=False)
        run(store, "record-mockup", "write-1", "--source", "claude-design", "--artifact-url", "claude-design://journey", "--artifact-id", "journey", "--contract", contract)
        run(store, "set-phase", "write-1", "PLAN_FINALIZATION"); run(store, "transition", "write-1", "WAITING_FOR_PLAN_APPROVAL")
        run(store, "transition", "write-1", "IMPLEMENTING", ok=False); run(store, "approve-plan", "write-1", "--fingerprint", "v2-abc")
        run(store, "transition", "write-1", "IMPLEMENTING"); run(store, "transition", "write-1", "TESTING"); run(store, "record-parity", "write-1", "--status", "passed", "--evidence", "screen/lane/transition trace")
        run(store, "transition", "write-1", "COMPLETED"); data = json.loads(run(store, "show", "write-1").stdout)
        assert data["clarificationCount"] == 1 and data["mockup"]["screenIds"] == ["screen-01", "screen-02", "screen-03", "screen-04"]

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
    assert "Sơ đồ nối màn hình bắt buộc" in orchestrator and "T<số bước>" in orchestrator
    assert "build_error_report.py" in orchestrator
    assert "MCP preflight" in orchestrator and "mcp_pref.py" in orchestrator
    assert "không từ chối" in orchestrator and "Không có skill riêng cho giỏ hàng" in orchestrator and "clarificationCount" in orchestrator
    assert "không còn hỗ trợ capability giỏ hàng" not in orchestrator and not (ROOT / "skills" / ("tap-shopper" + "-cart")).exists()
    for command in (ROOT / "commands").glob("*.md"):
        text = command.read_text(encoding="utf-8"); assert "tap-orchestration" in text and "Không gọi worker hoặc MCP tool trực tiếp" in text
    for name in ("tap-status","tap-screen","tap-flow","tap-config","tap-chat-display"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8"); assert "Delegated-by: tap-orchestration" in text and "workItemId" in text

if __name__ == "__main__":
    test_state_and_clarification(); test_builder_v1_v2(); test_mcp_pref(); test_error_report(); test_gateway_assets(); print("✔ TAP orchestration tests passed")
