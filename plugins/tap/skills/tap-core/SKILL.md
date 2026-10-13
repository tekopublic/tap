---
name: tap-core
description: Quy tắc an toàn và tra cứu cho MCP TAP (tenant customization). Dùng TRƯỚC mọi thao tác ghi lên màn hình, interaction flow, persona, preset, runtime config, theme, layout; và khi tool bị thiếu, bị "Permission denied", hoặc trả ok:false.
user-invocable: false
---

# TAP Core — Quy Tắc Điều Phối Và An Toàn

Skill nền tảng nội bộ cho mọi tương tác với TAP MCP Server. Mọi yêu cầu người dùng phải bắt đầu ở `tap-orchestration`; worker chỉ được gateway delegate. Bắt buộc đọc trước khi thực hiện bất kỳ thao tác thay đổi nào.

## 1. Tìm Và Gọi Tool MCP
- Không hard-code tiền tố server (như `mcp__phongvu-tap-mcp__...`).
- Luôn phân giải tool theo hậu tố: ví dụ cần gọi `publish_screen`, hãy tìm tool có dạng `*publish_screen` trong phiên làm việc hiện tại.

## 2. Target Guard (Bảo Vệ Môi Trường)
- **Bước 0**: Luôn gọi `ping` để xác thực phiên, lấy thông tin account/caller và ghi `server name + ping evidence` vào work item/plan.
- Tra cứu tiền tố tên server trong [targets.md](file://skills/tap-core/references/targets.md):
  - **PROD** (`phongvu-tap-mcp` hoặc domain prod) và **LOCAL** (`agentic-storefront-mcp` hoặc `localhost:8931`): đều cho phép ghi. Việc chọn server do người dùng quyết một lần ở MCP preflight của `tap-orchestration` và được lưu lại; không hỏi lại "có ghi lên PROD không" cho mỗi thao tác. An toàn vẫn do plan approval + backup (mục 4) và thẻ môi trường nêu rõ PROD/LOCAL trong plan.
- **TÊN LẠ**: Không suy diễn LOCAL/PROD từ alias hoặc desktop bridge; ghi nhãn PROD trong plan. Chỉ write khi target evidence từ `ping` khớp server người dùng đã chọn.
- Nếu phát hiện $\ge 2$ server TAP: dùng server đã lưu bằng `scripts/mcp_pref.py`; chưa có lựa chọn thì hỏi người dùng chọn một lần (xem MCP preflight ở `tap-orchestration`).

## 3. Phân Lớp Rủi Ro (R0 - R3)
Tra cứu 59 tools trong [tool-index.md](file://skills/tap-core/references/tool-index.md):
- **R0 (Đọc)**: Gọi tự do (lưu ý tránh gọi lặp lại các tool trả payload lớn như `describe_display_format`).
- **R1 (Ghi nháp)**: Thông báo 1 dòng cho người dùng trước khi ghi.
- **R2 (Ghi live)**: Bắt buộc Backup (`BK`) + Cổng xác nhận Gate `G` (chờ người dùng trả lời "yes").
- **R3 (Xóa/Khó hoàn tác)**: Bắt buộc Backup (`BK`) + Cổng xác nhận Gate `G` (người dùng phải gõ lại từ khóa xác nhận).

## 4. Plan Approval, Gate `G` & Backup (`BK`)
- Khi `tap-orchestration` đang điều phối, một approved Implementation Plan thay thế gate lặp lại cho **mọi write reversible đã liệt kê chính xác** trong `plannedOperations`. Approval gắn với work item, target và operation list; không phải xác nhận gộp cho cả phiên.
- Trước mọi thao tác ghi, lưu snapshot hiện tại vào `.tap-backups/<UTC>-<tool>-<id>.json` (hoặc in nguyên văn vào chat nếu môi trường không cho phép ghi file).
- Snapshot phải chứa nguyên payload `get_*`/read response trước ghi, target/server evidence, SHA-256 và rollback operation; file note hoặc transcript tóm tắt không phải backup hợp lệ.
- Vẫn dùng Gate `G` riêng, dù plan đã approved, nếu thao tác không nằm trong plan hoặc là R3/không thể đảo ngược, thanh toán/tạo order thật, gửi dữ liệu ra ngoài, hay thiếu định danh bắt buộc. Xem mẫu tại [gate-templates.md](file://skills/tap-core/references/gate-templates.md).
- Không có delegation context hợp lệ thì worker không thực hiện MCP write và route lại gateway; không có đường business entrypoint thay thế gateway.

## 5. Xử Lý Lỗi & Thiếu Quyền
- **Tool trả JSON `{"ok": false, "error": {...}}`**: Bóc tách `error.code` và tra cứu tại [error-codes.md](file://skills/tap-core/references/error-codes.md). Tối đa sửa 1 lần nếu là lỗi cú pháp rõ ràng, không retry mù.
- **Lỗi JSON-RPC `-32003 Permission denied`**: Dừng ngay lập tức, báo rõ quyền bị thiếu từ [permissions.md](file://skills/tap-core/references/permissions.md).
- **Tool bị ẩn khỏi danh sách**: Server tự động ẩn tool khi user thiếu quyền IAM. Dừng lại, in tên quyền cần thiết và mẫu tin nhắn gửi IAM Admin. Tuyệt đối KHÔNG tìm đường vòng.

## 6. Phạm Vi Loại Trừ
- Các công cụ Datamart (`query_data`, `describe_table`...) thuộc phạm vi phân tích dữ liệu DWH riêng, không dùng trong tùy biến giao diện storefront.
