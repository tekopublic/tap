#!/usr/bin/env python3
"""sync_from_code.py

Trích xuất thông tin metadata từ một source tree được chỉ định tường minh:
1. AST phân tích toàn bộ công cụ MCP -> `tool-index.md`
2. Đọc TOOL_PERMISSIONS từ consts.py -> `permissions.md`
3. Tìm kiếm các mã lỗi trong code -> `error-codes.md`
4. Ghi metadata git và ngày sinh -> `_generated.json`
"""

import argparse
import ast
import datetime
import json
import os
import re
import runpy
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Sync MCP metadata from a_tap code")
    parser.add_argument(
        "--source-root",
        required=True,
        help="Source root dùng để sinh metadata (không có đường dẫn mặc định)",
    )
    parser.add_argument(
        "--out",
        default="/Users/quyet/Desktop/code/teko/1temp/plugin/tap/skills/tap-core/references",
        help="Output directory for generated markdown references",
    )
    return parser.parse_args()


def get_git_info(source_root):
    try:
        sha = (
            subprocess.check_output(
                ["git", "-C", source_root, "rev-parse", "HEAD"], text=True
            )
            .strip()
        )
        status = (
            subprocess.check_output(
                ["git", "-C", source_root, "status", "--porcelain"], text=True
            )
            .strip()
        )
        clean = len(status) == 0
    except Exception as e:
        sha = "unknown"
        clean = False
    return sha, clean


def extract_tools(mcp_server_dir, tool_perms, risk_classes):
    tools_dir = os.path.join(mcp_server_dir, "tools")
    found_tools = {}

    for fname in sorted(os.listdir(tools_dir)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        fpath = os.path.join(tools_dir, fname)
        with open(fpath, "r", encoding="utf-8") as fp:
            try:
                tree = ast.parse(fp.read(), filename=fname)
            except Exception:
                continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_mcp_tool = False
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "tool":
                        is_mcp_tool = True
                    elif isinstance(dec, ast.Attribute) and dec.attr == "tool":
                        is_mcp_tool = True
                if is_mcp_tool:
                    doc = ast.get_docstring(node) or ""
                    first_doc = doc.strip().split("\n")[0] if doc else ""
                    args = []
                    # parse arg names and defaults
                    non_self_args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
                    defaults = [None] * (len(non_self_args) - len(node.args.defaults)) + list(node.args.defaults)
                    for a_name, d_node in zip(non_self_args, defaults):
                        if d_node is not None:
                            args.append(f"{a_name}?")
                        else:
                            args.append(a_name)

                    risk = risk_classes.get(node.name, "R0")
                    found_tools[node.name] = {
                        "name": node.name,
                        "file": fname,
                        "args": args,
                        "doc": first_doc,
                        "risk": risk,
                        "perms": tool_perms.get(node.name, ()),
                    }

    return found_tools


def extract_errors(mcp_server_dir, error_handling):
    error_defs = {}
    pattern_err = re.compile(r'(\w+Error)\([^\)]*?code\s*=\s*[\"\x27]([a-z0-9_]+)[\"\x27]', re.DOTALL)
    pattern_direct = re.compile(r'(\w+Error)\(\s*[\"\x27]([a-z0-9_]+)[\"\x27]')
    pattern_tool_err = re.compile(r'tool_error\(\s*[\"\x27]([a-z0-9_]+)[\"\x27]')

    for root, _, files in os.walk(mcp_server_dir):
        for f in files:
            if f.endswith(".py"):
                p = os.path.join(root, f)
                rel_p = os.path.relpath(p, mcp_server_dir)
                with open(p, "r", encoding="utf-8") as fp:
                    content = fp.read()
                    lines = content.splitlines()

                    for idx, line in enumerate(lines, 1):
                        for m in pattern_tool_err.finditer(line):
                            code = m.group(1)
                            error_defs.setdefault(code, []).append((rel_p, idx))
                        for m in pattern_direct.finditer(line):
                            code = m.group(2)
                            error_defs.setdefault(code, []).append((rel_p, idx))

                    for m in pattern_err.finditer(content):
                        code = m.group(2)
                        # approximate line
                        pos = m.start()
                        line_num = content[:pos].count("\n") + 1
                        error_defs.setdefault(code, []).append((rel_p, line_num))

    # Deduplicate and sort
    results = {}
    all_codes = set(error_defs.keys()) | set(error_handling.keys())
    for code in sorted(all_codes):
        locs = error_defs.get(code, [])
        uniq_locs = sorted(list(set(f"{f}:{l}" for f, l in locs)))
        desc = error_handling.get(code, "Lỗi được trả về từ hệ thống backend.")
        results[code] = {
            "locations": uniq_locs,
            "remediation": desc,
        }
    return results


def main():
    args = parse_args()
    source_root = os.path.abspath(args.source_root)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    risk_file = os.path.join(scripts_dir, "risk_classes.json")
    err_file = os.path.join(scripts_dir, "error_handling.json")

    with open(risk_file, "r", encoding="utf-8") as fp:
        risk_classes = json.load(fp)
    with open(err_file, "r", encoding="utf-8") as fp:
        error_handling = json.load(fp)

    mcp_server_dir = os.path.join(source_root, "src", "backend", "bff", "mcp_server")
    consts_path = os.path.join(mcp_server_dir, "utils", "consts.py")

    consts = runpy.run_path(consts_path)
    tool_perms = consts["TOOL_PERMISSIONS"]

    sha, clean = get_git_info(source_root)
    tools = extract_tools(mcp_server_dir, tool_perms, risk_classes)
    errors = extract_errors(mcp_server_dir, error_handling)

    # 1. tool-index.md
    tool_index_md = os.path.join(out_dir, "tool-index.md")
    with open(tool_index_md, "w", encoding="utf-8") as fp:
        fp.write(f"# Danh Mục {len(tools)} Tools MCP TAP (Generated)\n\n")
        fp.write(f"> Tự động sinh từ source tree được chỉ định ({sha[:8]}, sạch: {clean}) ngày {datetime.date.today().isoformat()}.\n\n")
        fp.write("| # | Tên Tool | Lớp | Quyền IAM | Tham số | Mô tả tóm tắt |\n")
        fp.write("|---|---|---|---|---|---|\n")
        for idx, (t_name, t_data) in enumerate(sorted(tools.items()), 1):
            perms_str = ", ".join(f"`{p}`" for p in t_data["perms"]) if t_data["perms"] else "*(không cần)*"
            args_str = ", ".join(f"`{a}`" for a in t_data["args"]) if t_data["args"] else "-"
            doc_str = t_data["doc"].replace("|", "\\|")
            fp.write(f"| {idx} | `{t_name}` | **{t_data['risk']}** | {perms_str} | {args_str} | {doc_str} |\n")

    # 2. permissions.md
    all_perms = set()
    for perms in tool_perms.values():
        for p in perms:
            all_perms.add(p)

    perms_md = os.path.join(out_dir, "permissions.md")
    with open(perms_md, "w", encoding="utf-8") as fp:
        fp.write("# Danh Sách Quyền IAM Cho MCP TAP (Generated)\n\n")
        fp.write(f"> Tổng cộng {len(all_perms)} chuỗi quyền IAM cấu hình trong `consts.py`.\n\n")
        fp.write("## Quyền Tap Core (`mcp-server:tap:*`)\n\n")
        for p in sorted([p for p in all_perms if ":tap:" in p]):
            fp.write(f"- `{p}`\n")
        fp.write("\n## Quyền MCP / Datamart / Report (`mcp-server:mcp:*`)\n\n")
        for p in sorted([p for p in all_perms if ":tap:" not in p]):
            fp.write(f"- `{p}`\n")

    # 3. error-codes.md
    err_md = os.path.join(out_dir, "error-codes.md")
    with open(err_md, "w", encoding="utf-8") as fp:
        fp.write("# Tra Cứu Mã Lỗi MCP TAP (Generated)\n\n")
        fp.write(f"> Tổng hợp {len(errors)} mã lỗi định danh từ source tree được chỉ định.\n\n")
        fp.write("| Mã Lỗi | Vị Trí Code Xuất Hiện | Ý Nghĩa & Hướng Xử Lý |\n")
        fp.write("|---|---|---|\n")
        for code, data in sorted(errors.items()):
            loc_str = ", ".join(f"`{l}`" for l in data["locations"][:3]) if data["locations"] else "*(từ catalog)*"
            remediation = data["remediation"].replace("|", "\\|")
            fp.write(f"| `{code}` | {loc_str} | {remediation} |\n")

    # 4. _generated.json
    gen_json = os.path.join(out_dir, "_generated.json")
    with open(gen_json, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "sha": sha,
                "clean": clean,
                "generated_at": datetime.datetime.now().isoformat(),
                "tools_count": len(tools),
                "permissions_count": len(all_perms),
                "error_codes_count": len(errors),
            },
            fp,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Sync complete:")
    print(f"- {len(tools)} tools written to {tool_index_md}")
    print(f"- {len(all_perms)} permissions written to {perms_md}")
    print(f"- {len(errors)} error codes written to {err_md}")
    print(f"- Metadata written to {gen_json}")


if __name__ == "__main__":
    main()
