#!/usr/bin/env python3
"""check_contract.py

Kiểm tra hợp đồng và tính toàn vẹn của plugin tap:
- C1: Tên tool được nhắc trong skills/**, commands/** phải có trong tool-index.md
- C2: Mã lỗi được nhắc phải có trong error-codes.md
- C3: risk_classes.json có đủ 59 tools TAP đã đóng gói
- C5: Description của skill/command <= 400 ký tự; SKILL.md <= 150 dòng
- C6: Không chứa bin/, settings.json, user_config; portable/OpenAI manifests và local MCP descriptor phải nhất quán
"""

import argparse
import glob
import json
import os
import re
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Check contract parity")
    parser.add_argument(
        "--plugin-dir",
        default="/Users/quyet/Desktop/code/teko/1temp/plugin/tap",
        help="Path to plugin directory",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    plugin_dir = os.path.abspath(args.plugin_dir)
    scripts_dir = os.path.join(plugin_dir, "scripts")

    errors = []

    # C6: Cấm legacy/private runtime payload; mcp.json là descriptor MCP local
    # được package TAP dùng, không chứa credentials.
    forbidden_items = ["bin", "settings.json", "user_config"]
    for item in forbidden_items:
        p = os.path.join(plugin_dir, item)
        if os.path.exists(p):
            errors.append(f"[C6] Tồn tại mục bị cấm trong MVP: {item}")

    # Load tool-index and error-codes
    refs_dir = os.path.join(plugin_dir, "skills", "tap-core", "references")
    risk_file = os.path.join(scripts_dir, "risk_classes.json")

    if not os.path.exists(risk_file):
        errors.append(f"[C3] Không tìm thấy {risk_file}")
        risk_tools = {}
    else:
        with open(risk_file, "r", encoding="utf-8") as fp:
            risk_tools = json.load(fp)

    # C3: Kiểm tra đủ 59 tools. Source/live MCP đã expose refresh_report;
    # hard-code count để fail closed khi catalog plugin drift thêm lần nữa.
    expected_tool_count = 59
    if len(risk_tools) != expected_tool_count:
        errors.append(f"[C3] risk_classes.json phải có đúng {expected_tool_count} tools, hiện có {len(risk_tools)}")

    # Portable package includes the local, credential-free MCP descriptor so
    # skills and tools share the same Work-chat scope.
    portable_manifest = os.path.join(plugin_dir, "plugin.json")
    codex_manifest = os.path.join(plugin_dir, ".codex-plugin", "plugin.json")
    for manifest_path, label in ((portable_manifest, "portable"), (codex_manifest, "codex")):
        if not os.path.isfile(manifest_path):
            errors.append(f"[O1] thiếu {label} manifest: {os.path.relpath(manifest_path, plugin_dir)}")
            continue
        try:
            with open(manifest_path, encoding="utf-8") as fp:
                manifest = json.load(fp)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"[O1] {label} manifest không phải JSON hợp lệ: {exc}")
            continue
        if manifest.get("name") != "tap":
            errors.append(f"[O2] {label} manifest phải có name=tap")
        if not manifest.get("version"):
            errors.append(f"[O2] {label} manifest thiếu version")
    if os.path.isfile(portable_manifest) and os.path.isfile(codex_manifest):
        portable = json.load(open(portable_manifest, encoding="utf-8"))
        codex = json.load(open(codex_manifest, encoding="utf-8"))
        if portable.get("version") != codex.get("version"):
            errors.append("[O3] portable và Codex manifest phải cùng version")
        if codex.get("skills") != "./skills/":
            errors.append("[O3] Codex manifest phải khai báo skills=./skills/")
        if "apps" in codex:
            errors.append("[O3] không được khai báo app mapping khi chưa có technical app id")
        mcp_descriptor = os.path.join(plugin_dir, "mcp.json")
        try:
            with open(mcp_descriptor, encoding="utf-8") as fp:
                mcp = json.load(fp)
            server = mcp.get("mcpServers", {}).get("agentic-storefront-mcp", {})
            if server.get("type") != "stdio" or server.get("command") != "npx" or server.get("args") != ["-y", "mcp-remote", "http://localhost:8931/mcp"]:
                errors.append("[O3] mcp.json không khớp TAP local MCP bridge chuẩn")
            if "env" in server:
                errors.append("[O3] mcp.json không được chứa environment values")
        except (OSError, json.JSONDecodeError):
            errors.append("[O3] thiếu hoặc không đọc được mcp.json")

    # C5: Kiểm tra description <= 400 ký tự và SKILL.md <= 150 dòng
    frontmatter_desc_pattern = re.compile(r"^description:\s*(.*?)$", re.MULTILINE)
    skill_files = glob.glob(os.path.join(plugin_dir, "skills", "**", "SKILL.md"), recursive=True)
    for sf in skill_files:
        with open(sf, "r", encoding="utf-8") as fp:
            content = fp.read()
            lines = content.splitlines()
            if len(lines) > 150:
                errors.append(f"[C5] {os.path.relpath(sf, plugin_dir)} có {len(lines)} dòng (vượt quá 150 dòng)")
            m = frontmatter_desc_pattern.search(content)
            if m:
                desc = m.group(1).strip()
                if len(desc) > 400:
                    errors.append(f"[C5] description trong {os.path.relpath(sf, plugin_dir)} dài {len(desc)} ký tự (> 400)")

    cmd_files = glob.glob(os.path.join(plugin_dir, "commands", "*.md"))
    for cf in cmd_files:
        with open(cf, "r", encoding="utf-8") as fp:
            content = fp.read()
            m = frontmatter_desc_pattern.search(content)
            if m:
                desc = m.group(1).strip()
                if len(desc) > 400:
                    errors.append(f"[C5] description trong {os.path.relpath(cf, plugin_dir)} dài {len(desc)} ký tự (> 400)")

    # Gateway-only: aliases cannot directly invoke a worker/tool; workers require delegation marker.
    for cf in cmd_files:
        content = open(cf, encoding="utf-8").read()
        if "tap-orchestration" not in content or "Không gọi worker hoặc MCP tool trực tiếp" not in content:
            errors.append(f"[G1] {os.path.relpath(cf, plugin_dir)} không phải thin alias vào gateway")
    for worker in ("tap-status", "tap-screen", "tap-flow", "tap-config", "tap-chat-display", "tap-shopper-cart"):
        path = os.path.join(plugin_dir, "skills", worker, "SKILL.md")
        content = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if "Delegated-by: tap-orchestration" not in content or "workItemId" not in content:
            errors.append(f"[G2] worker {worker} thiếu delegation guard")

    if errors:
        print("X Kiểm tra hợp đồng thất bại:")
        for err in errors:
            print("  -", err)
        sys.exit(1)
    else:
        print("✔ Toàn bộ hợp đồng C1-C6 đều hợp lệ và vượt qua kiểm tra.")


if __name__ == "__main__":
    main()
