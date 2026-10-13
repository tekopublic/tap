#!/usr/bin/env python3
"""check_live.py

Kiểm tra trực tiếp tool list từ MCP server đang chạy (chỉ dùng cho LOCAL,
cần MCP_AUTH_DISABLED=1 hoặc header thích hợp).
So sánh danh sách tool nhận được với tool-index.md.

Sử dụng:
  MCP_AUTH_DISABLED=1 python3 scripts/check_live.py --url http://localhost:8931/mcp
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

TOOL_INDEX_PATH = "/Users/quyet/Desktop/code/teko/1temp/plugin/tap/skills/tap-core/references/tool-index.md"


def parse_args():
    p = argparse.ArgumentParser(description="Compare live MCP tool list with plugin tool-index")
    p.add_argument("--url", default="http://localhost:8931/mcp", help="MCP server URL")
    p.add_argument("--tool-index", default=TOOL_INDEX_PATH, help="Path to tool-index.md")
    return p.parse_args()


def _decode_mcp_response(raw: str) -> dict:
    """Accept a JSON response or one SSE data frame from Streamable HTTP."""
    # JSON-RPC notifications have no response body; Streamable HTTP commonly
    # acknowledges them with 202 and an empty body.
    if not raw.strip():
        return {}
    for line in raw.splitlines():
        if line.startswith("data:"):
            return json.loads(line.removeprefix("data:").strip())
    return json.loads(raw)


def call_mcp(url: str, payload: dict, session_id: str | None = None) -> tuple[dict, str | None]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return (
            _decode_mcp_response(resp.read().decode("utf-8")),
            resp.headers.get("Mcp-Session-Id"),
        )


def fetch_tool_list(url: str) -> list[str]:
    initialize, session_id = call_mcp(url, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "tap-contract-check", "version": "1.1.7"},
        },
    })
    if "error" in initialize:
        raise RuntimeError(f"initialize MCP thất bại: {initialize['error']}")

    # MCP lifecycle requires this notification before clients discover tools.
    # The local mcp-remote bridge sends it as well; omit it here and FastMCP
    # may produce an empty discovery result for a fresh Streamable HTTP session.
    call_mcp(url, {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }, session_id=session_id)

    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    try:
        data, _ = call_mcp(url, payload, session_id=session_id)
    except (urllib.error.URLError, json.JSONDecodeError, RuntimeError) as e:
        print(f"Lỗi kết nối MCP server {url}: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in data:
        error = data["error"]
        code = error.get("code", "unknown")
        message = error.get("message", "MCP error")
        raise RuntimeError(f"tools/list thất bại ({code}): {message}")

    tools = data.get("result", {}).get("tools", [])
    return [t["name"] for t in tools if "name" in t]


def parse_tool_index(path: str) -> set[str]:
    names = set()
    try:
        with open(path, "r", encoding="utf-8") as fp:
            for line in fp:
                # Table layout is | # | tool name | risk | permission | args | description |.
                # Only the second data column is a tool identifier; permission
                # and parameter columns also contain backticks and must not be
                # interpreted as tools.
                if not line.startswith("|"):
                    continue
                parts = [part.strip() for part in line.split("|")]
                if len(parts) < 4:
                    continue
                candidate = parts[2]
                if candidate.startswith("`") and candidate.endswith("`"):
                    name = candidate[1:-1]
                    if name:
                        names.add(name)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy {path}", file=sys.stderr)
        sys.exit(1)
    return names


def main():
    args = parse_args()
    print(f"Đang kết nối MCP server: {args.url}")

    live_tools = set(fetch_tool_list(args.url))
    index_tools = parse_tool_index(args.tool_index)

    print(f"  Tool trong phiên: {len(live_tools)}")
    print(f"  Tool trong index: {len(index_tools)}")
    print()

    missing_from_live = index_tools - live_tools
    extra_in_live = live_tools - index_tools

    if not missing_from_live and not extra_in_live:
        print("✔ Danh sách tool khớp hoàn toàn!")
    else:
        if missing_from_live:
            print("⚠️  Tool có trong index nhưng KHÔNG thấy trong phiên (có thể thiếu quyền IAM):")
            for t in sorted(missing_from_live):
                print(f"    - {t}")
        if extra_in_live:
            print("ℹ️  Tool có trong phiên nhưng KHÔNG có trong index (server mới hơn plugin):")
            for t in sorted(extra_in_live):
                print(f"    + {t}")
        print()
        print("👉 Nếu có tool lạ: Chạy lại sync_from_code.py để cập nhật plugin.")


if __name__ == "__main__":
    main()
