#!/usr/bin/env python3
"""measure.py

Đo chỉ số hiệu suất từ transcript Claude Code:
- Số lời gọi tool MCP (tool_use events)
- Số lỗi tool (ok: false)
- Số lỗi JSON-RPC (-32003)
- Tổng chi phí USD (nếu có trong metadata)
- Thời gian wall-clock ước lượng
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Measure TAP plugin performance from transcript")
    p.add_argument("transcript", help="Path to JSONL transcript file")
    p.add_argument("--filter-tool", help="Only count calls to this tool name (partial match)")
    return p.parse_args()


def main():
    args = parse_args()
    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        print(f"Lỗi: Không tìm thấy file {transcript_path}", file=sys.stderr)
        sys.exit(1)

    tool_calls = []
    tool_errors_ok_false = []
    rpc_errors = []
    total_cost = 0.0
    timestamps = []

    with open(transcript_path, "r", encoding="utf-8") as fp:
        for line_num, line in enumerate(fp, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Collect timestamps for wall-clock
            ts = entry.get("timestamp") or entry.get("created_at")
            if ts:
                timestamps.append(ts)

            # Cost
            usage = entry.get("usage") or entry.get("costUsd")
            if isinstance(usage, dict):
                total_cost += usage.get("costUsd", 0.0)
            elif isinstance(usage, (int, float)):
                total_cost += usage

            # Tool use events
            content = entry.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        if args.filter_tool and args.filter_tool not in tool_name:
                            continue
                        tool_calls.append({
                            "name": tool_name,
                            "input": block.get("input", {}),
                        })

            # Tool results — check for ok: false
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        result_content = block.get("content", "")
                        if isinstance(result_content, list):
                            for rc in result_content:
                                if isinstance(rc, dict) and rc.get("type") == "text":
                                    txt = rc.get("text", "")
                                    if '"ok": false' in txt or '"ok":false' in txt:
                                        try:
                                            data = json.loads(txt)
                                            tool_errors_ok_false.append(data.get("error", {}).get("code", "unknown"))
                                        except Exception:
                                            tool_errors_ok_false.append("parse_error")

            # Check for JSON-RPC errors in raw content
            raw_str = json.dumps(entry)
            if "-32003" in raw_str:
                perms = re.findall(r"requires\s+([\w:\-\.]+)", raw_str)
                rpc_errors.extend(perms if perms else ["unknown_permission"])

    # Summary
    print("=" * 60)
    print("  📊 TAP Plugin Performance Report")
    print("=" * 60)
    print(f"  Tổng lời gọi tool MCP   : {len(tool_calls)}")
    print(f"  Lỗi ok:false            : {len(tool_errors_ok_false)}")
    print(f"  Lỗi JSON-RPC -32003     : {len(rpc_errors)}")
    print(f"  Chi phí ước tính        : ${total_cost:.4f}")
    print()

    if tool_calls:
        print("  Chi tiết tool calls:")
        from collections import Counter
        counts = Counter(tc["name"] for tc in tool_calls)
        for name, cnt in counts.most_common():
            print(f"    {cnt:3d}x  {name}")
        print()

    if tool_errors_ok_false:
        print("  Lỗi ok:false (mã lỗi):")
        err_counts = Counter(tool_errors_ok_false)
        for code, cnt in err_counts.most_common():
            print(f"    {cnt:3d}x  {code}")
        print()

    if rpc_errors:
        print("  Lỗi JSON-RPC permission denied:")
        for perm in rpc_errors:
            print(f"    - {perm}")
        print()


if __name__ == "__main__":
    main()
