#!/usr/bin/env python3
"""Lưu/đọc lựa chọn MCP server TAP của người dùng (không chứa secret)."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path

DEFAULT = Path(os.environ.get("TAP_MCP_PREF", Path.home() / ".tap" / "mcp-preference.json"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", default=str(DEFAULT))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set")
    s.add_argument("server", help="Tên server MCP người dùng đã chọn, ví dụ phongvu-tap-mcp")
    sub.add_parser("get")
    sub.add_parser("clear")
    a = p.parse_args()
    f = Path(a.file)
    if a.cmd == "set":
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"server": a.server, "selectedAt": dt.datetime.now(dt.timezone.utc).isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(a.server)
    elif a.cmd == "get":
        print(f.read_text(encoding="utf-8") if f.exists() else json.dumps({"server": None}))
    else:
        f.unlink(missing_ok=True)
        print("cleared")


if __name__ == "__main__":
    main()
