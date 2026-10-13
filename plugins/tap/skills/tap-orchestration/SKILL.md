---
name: tap-orchestration
description: Cổng vào duy nhất cho mọi yêu cầu TAP và alias; phân loại intent, quản lý work item, safety gate, mockup review, delegation nội bộ và handoff.
user-invocable: true
---

# TAP Orchestration Gateway

Đây là entrypoint duy nhất cho yêu cầu TAP từ chat hoặc slash alias. Đọc `tap-core` trước mọi MCP operation. Không worker nào được tự nhận yêu cầu người dùng.

## 0. MCP preflight (mỗi phiên, trước triage)

1. Đọc lựa chọn đã lưu: `python3 scripts/mcp_pref.py get`.
2. Quét tool trong phiên theo hậu tố (`*ping`, `*list_screens`, `*publish_screen`, `*describe_display_format`) rồi gom theo server. Server chỉ được coi là "server TAP" khi có đủ nhóm tool này.
3. Quyết định:
   - **Không có server TAP nào**: dừng ở `BLOCKED` và báo chủ động: "Chưa kết nối MCP TAP. Vào Connectors → Connect (hoặc Reconnect nếu hiện 'Server not responding'/'Sign-in expired'), rồi nhắn lại." Liệt kê các connector có tên gần giống nhưng chưa kết nối nếu thấy. Không gọi tool, không đoán.
   - **Có đúng 1 server TAP**: dùng luôn, lưu bằng `mcp_pref.py set <server>`.
   - **Có nhiều server TAP và chưa có lựa chọn đã lưu (hoặc server đã lưu không còn trong phiên)**: hỏi người dùng chọn một, nêu môi trường LOCAL/PROD của từng server theo `tap-core/references/targets.md`, rồi lưu bằng `mcp_pref.py set`.
   - **Đã lưu và server còn trong phiên**: dùng luôn, không hỏi lại.
4. Người dùng nói "đổi MCP" / "dùng <tên server>" ở bất kỳ lúc nào: chạy lại `mcp_pref.py set`. `/tap:status` hiển thị server đang dùng và các server TAP khác khả dụng.
5. Ghi `server` đã chọn vào work item và truyền cho mọi worker; worker không tự chọn server khác.

## 0b. Báo lỗi cho team TAP

Khi chuyển `BLOCKED`, hoặc gặp lỗi không tự xử lý được (thiếu kết nối/quyền/API/config, `ok:false` nội bộ, không tạo được Claude Design): dừng, rồi theo [error-report.md](../tap-core/references/error-report.md) chạy `scripts/build_error_report.py` và in nguyên văn kết quả: giải thích tiếng Việt dễ hiểu, khung báo cáo để copy, hướng dẫn dán vào nhóm Google Chat TAP. Không gửi mạng, không tự gửi thay người dùng, không đưa secret/PII/nội dung chat khách. Nếu đã có thao tác ghi dở dang, nêu rõ ở mục "Đã ghi gì lên hệ thống?" kèm đường dẫn backup.

## 1. Triage và retirement

1. Create/resume work item trước mọi route; ghi alias, intent, scope, target/risk, `clarificationCount` (0 hoặc 1), assumptions và phase. Chỉ gateway được transition state/phase, parse approval hay kết thúc response.
2. Với xem/thêm/sửa/xóa giỏ hàng, promotion cart hoặc checkout, dừng trước MCP discovery và trả: **“TAP plugin không còn hỗ trợ capability giỏ hàng. Tôi không gọi MCP cart capability.”** Nếu request còn storefront hợp lệ, tách riêng phần đó vào work item.
3. Read-only có thể hoàn thành qua internal worker mà không cần mockup. Storefront screen/flow/chat-display hoặc UI write phải theo lifecycle mockup dưới đây.

## 2. Một lượt clarification UX

Triage dùng context và R0 discovery trước. Nếu đủ dữ liệu, ghi assumptions có nhãn rồi dựng mockup ngay. Nếu lần đầu thiếu dữ liệu material, gửi đúng một message, tối đa ba nhóm: (1) mục tiêu/người dùng, (2) screen/flow và điểm bắt đầu, (3) nội dung/brand/fixture; nêu default cho từng nhóm và tăng `clarificationCount` lên 1.

Sau câu trả lời, không hỏi UX clarification lần hai: hợp nhất câu trả lời/default, công bố assumptions và tạo mockup. Feedback như “sửa Screen 02/lane Empty state/CTA” là iteration mockup, không tăng count. Thiếu target, delete mơ hồ, payment/order thật, external disclosure hoặc permission failure vẫn BLOCKED theo `tap-core`; không được suy đoán.

## 3. Mockup, plan và delegation

Với UI route, chuyển `PLANNING/MOCKUP_REVIEW`, tạo fixture-only scenario theo [schema](references/journey-mockup-schema.md) làm contract, rồi dựng mockup trực quan từ contract đó:

- **Đầu ra DUY NHẤT hợp lệ: Claude Design (canvas)** (source `claude-design`). Đây là loại artifact "Claude Design" hiển thị trong chat (thẻ ghi "Claude Design"), KHÔNG phải file `.html`/"Code · HTML". Mỗi screen là một artboard đánh số `01 · <tên>` trên canvas; có flow map, lanes, CTA/transition, assumptions; bám layout storefront thật (header, chat sidebar, display panel) và token `get_theme` của tenant; dữ liệu fixture có nhãn.
- **Không chờ người dùng yêu cầu.** Không được tạo file HTML, HTML artifact (tool Artifact), Markdown hay ảnh làm mockup rồi hỏi "bạn có muốn Claude Design không". Tạo thẳng Claude Design ngay lượt đầu của `MOCKUP_REVIEW`.
- **Không có fallback HTML.** Nếu môi trường không có khả năng tạo Claude Design (ví dụ Claude Code CLI/VS Code, không thấy tool/skill Claude Design), dừng ở `BLOCKED`: báo rõ "cần chạy trong Claude Desktop/claude.ai để tạo Claude Design canvas", không tự thay bằng HTML.
- **Cấm** dùng `scripts/build_journey_mockup.py` (legacy) hoặc template HTML dựng sẵn. Không gọi MCP preview/save/publish để tạo mockup. V1 single-screen vẫn hợp lệ.

Sau review, record artifact path/URL, fingerprint, schema version, screen/lane/transition IDs trong work item. Với write, tạo plan gồm objective, operations, target, backup/rollback, tests và fingerprint; chuyển `WAITING_FOR_PLAN_APPROVAL`. Chỉ **Đồng ý triển khai** gắn approval fingerprint. Không approval lại write reversible đã liệt kê; R3/không đảo ngược/payment/external/missing identifier vẫn gate riêng.

Gateway delegate worker với `workItemId`, resolved scope/capability và phase. Worker thiếu cả ba phải trả `BLOCKED`/route lại gateway, không gọi MCP write. Worker chỉ làm subtask; gateway giữ tool discovery intent, work-state, clarification, approval, parity và final response.

## 4. Handoff

Tester replay fixture trace; parity chỉ passed khi chat, display, screen/lane/transition trace khớp mockup. Gateway báo delivered behavior, data writes, evidence, state và blocker. Guard này là policy plugin có thể kiểm chứng, không phải hard authorization boundary; MCP permission và `tap-core` vẫn là enforcement cuối.
