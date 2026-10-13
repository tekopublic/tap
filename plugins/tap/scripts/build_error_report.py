#!/usr/bin/env python3
"""Dựng báo cáo lỗi TAP (giải thích tiếng Việt + nội dung để copy gửi nhóm Google Chat TAP).

Không gửi mạng. Tự che token/secret/email trước khi in.
"""
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAT_GROUP = os.environ.get("TAP_REPORT_CHAT_GROUP", "nhóm Google Chat TAP")

CATEGORIES = {
    "mcp-not-connected": ("Chưa kết nối MCP TAP",
        "Claude chưa thấy máy chủ TAP nào đang hoạt động, nên chưa làm được gì.",
        "Vào Settings → Connectors, bấm Connect (hoặc Reconnect nếu đang báo 'Server not responding' / 'Sign-in expired'), sau đó nhắn lại yêu cầu."),
    "permission-denied": ("Tài khoản thiếu quyền",
        "Máy chủ TAP từ chối vì tài khoản của bạn chưa được cấp quyền cho thao tác này.",
        "Gửi báo cáo bên dưới cho team TAP để xin cấp quyền, rồi thử lại."),
    "tool-hidden": ("Thiếu công cụ (tool) trên máy chủ TAP",
        "Máy chủ ẩn một số công cụ cần dùng, thường do thiếu quyền hoặc máy chủ chưa cập nhật.",
        "Gửi báo cáo cho team TAP để kiểm tra quyền/phiên bản máy chủ."),
    "missing-api": ("Thiếu API / operation",
        "Thao tác cần gọi một API mà máy chủ TAP chưa có hoặc chưa mở cho tenant này.",
        "Gửi báo cáo cho team TAP để bổ sung API."),
    "missing-config": ("Thiếu cấu hình",
        "Tenant chưa có cấu hình cần thiết (ví dụ theme, runtime config, dữ liệu nguồn) nên không thể tiếp tục.",
        "Gửi báo cáo cho team TAP để bổ sung cấu hình."),
    "server-error": ("Lỗi phía máy chủ TAP",
        "Máy chủ TAP gặp lỗi nội bộ. Đây không phải lỗi do bạn nhập sai.",
        "Gửi báo cáo cho team TAP. Chưa có thay đổi nào được ghi lên hệ thống trừ khi Claude nói rõ là đã ghi."),
    "claude-design-unavailable": ("Môi trường không tạo được Claude Design",
        "Mockup bắt buộc là Claude Design (canvas), nhưng môi trường hiện tại không hỗ trợ.",
        "Mở lại yêu cầu trong Claude Desktop hoặc claude.ai. Nếu đã dùng Desktop mà vẫn lỗi, gửi báo cáo cho team TAP."),
    "other": ("Lỗi khác",
        "Gặp sự cố chưa phân loại được.",
        "Gửi báo cáo cho team TAP để kiểm tra."),
}

REDACT = [
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"), "Bearer [ẩn]"),
    (re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_\-]{8,}"), "[ẩn-key]"),
    (re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization)\s*[=:]\s*\S+"), r"\1=[ẩn]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[ẩn-email]"),
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "[ẩn-chuỗi-dài]"),
    (re.compile(r"\b(?:\+?84|0)\d{9,10}\b"), "[ẩn-sđt]"),
]


def redact(text):
    for pat, rep in REDACT:
        text = pat.sub(rep, text or "")
    return text


def plugin_version():
    try:
        return json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
    except Exception:
        return "không rõ"


def build(a):
    title, why, todo = CATEGORIES[a.category]
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M (GMT+7)")
    rows = [
        ("Loại lỗi", f"{title} [{a.category}]"),
        ("Thời gian", now),
        ("Phiên bản plugin", plugin_version()),
        ("MCP đang dùng", f"{a.server or 'chưa chọn'} ({a.env or 'không rõ'})"),
        ("Tenant", a.tenant or "không rõ"),
        ("Bước đang làm", a.step or "không rõ"),
        ("Công cụ lỗi", a.tool or "không rõ"),
        ("Mã lỗi", a.code or "không có"),
        ("Thông báo lỗi gốc", redact(a.message)[:500] or "không có"),
        ("Work item", f"{a.work_id or 'không rõ'} / {a.phase or 'không rõ'}"),
        ("Đã ghi gì lên hệ thống?", a.writes or "Chưa ghi gì"),
    ]
    report = "\n".join(f"- {k}: {v}" for k, v in rows)
    return f"""## Đã xảy ra sự cố: {title}

**Chuyện gì đã xảy ra:** {why}

**Bạn nên làm:** {todo}

### Báo cáo lỗi (copy toàn bộ khung dưới)

```
[TAP - BÁO LỖI] {title}
{report}
Mô tả thêm của người dùng: (viết thêm vài dòng bạn đang muốn làm gì)
```

### Cách gửi cho team
1. Mở Google Chat, vào **{CHAT_GROUP}**.
2. Dán toàn bộ nội dung trong khung ở trên vào ô chat rồi gửi.
3. Điền thêm dòng "Mô tả thêm của người dùng" nếu có, rồi chờ team TAP phản hồi.

Báo cáo đã tự che token, mật khẩu, email và số điện thoại. Không có nội dung chat của khách hàng trong đó."""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--category", choices=sorted(CATEGORIES), default="other")
    for k in ("server", "env", "tenant", "step", "tool", "code", "message", "work-id", "phase", "writes"):
        p.add_argument(f"--{k}", default="")
    a = p.parse_args()
    a.work_id = getattr(a, "work_id")
    print(build(a))


if __name__ == "__main__":
    main()
