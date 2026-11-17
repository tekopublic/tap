---
name: tap-screen
description: Tạo, sửa, gỡ lỗi hoặc gỡ một màn hình (display, renderer mount) của tenant qua MCP TAP. Dùng khi người dùng nói về màn hình/panel/display/giao diện một trạng thái của storefront, binding, preview.
user-invocable: false
---

# TAP Screen — Internal Worker

**Delegated-by: tap-orchestration.** Không nhận request trực tiếp, không tạo/resume work item hoặc tự hỏi clarification/approval. Chỉ thực hiện subtask có `workItemId`, resolved scope/capability và phase từ gateway; thiếu context thì trả `BLOCKED`/route lại gateway trước mọi MCP write.

**Cổng ghi (plugin 3.3.0):** trước MỌI MCP write chạy `python3 scripts/work_item_state.py show <workItemId>` và kiểm `state == IMPLEMENTING` (đã qua B0–B4) và `savedRequirement.requirementId` có giá trị. Thiếu một trong hai → trả `BLOCKED` về gateway kèm output `progress <workItemId>`, không gọi tool ghi. Mọi tool ghi nháp truyền `requirementId`. Không bao giờ gọi `publish_*` (Public chỉ trên Tenant Admin web). Báo vấn đề cho người dùng theo Khung hỏi của gateway (phương án + đề xuất).

Skill chuyên biệt cho vòng đời màn hình (Display Component / Renderer Mount) trên storefront của tenant. Khi được `tap-orchestration` gọi, dùng mockup contract và plan approval theo `tap-core`; không tạo gate lặp lại cho publish reversible đã nằm trong plan.

## 1. Nguyên Tắc Cốt Lõi
- Đọc `tap-core` trước khi thực hiện bất kỳ thao tác nào.
- Luôn kiểm tra danh sách màn hình qua `list_screens` để xác định trạng thái màn hình (`code`) là **MỚI**, **DRAFT** hay **ĐANG PUBLISHED (LIVE)**.

## 2. Bảng Quyết Định Luồng Thao Tác

| Hiện Trạng `code` | Hành Động Phù Hợp | Tài Liệu Chi Tiết |
|---|---|---|
| `code` chưa tồn tại | Tạo mới hoàn toàn (Khám phá $\rightarrow$ Viết JS $\rightarrow$ `preview_screen` $\rightarrow$ `save_screen(..., requirementId)` (chỉ ghi nháp) $\rightarrow$ `preview_screen(screenCode)`). Không `publish_screen`. | [create.md](file://skills/tap-screen/references/create.md) |
| `code` đang `published` | **SỬA MÀN ĐANG LIVE**: `get_screen` (backup) $\rightarrow$ `preview_screen(blobContent)` $\rightarrow$ `save_screen(..., requirementId)` (từ #327 chỉ ghi nháp, bản live không đổi) $\rightarrow$ `preview_screen(screenCode)`. Không `publish_screen`. | [edit-live.md](file://skills/tap-screen/references/edit-live.md) |
| `code` đang `draft` | Tiếp tục hoàn thiện: Sửa $\rightarrow$ `preview_screen` $\rightarrow$ Promote hoặc Publish đầy đủ. | [create.md](file://skills/tap-screen/references/create.md) |
| Gỡ màn hình live | `get_screen` (backup) $\rightarrow$ Cổng R3 (gõ lại `DELETE <code>`) $\rightarrow$ `delete_screen`. | [edit-live.md](file://skills/tap-screen/references/edit-live.md) |

## 3. Các Bẫy Nguy Hiểm Cần Tránh
1. **Bẫy P3 (`save_screen` làm mất bản live)**: `save_screen` luôn ghi đè `status='draft'`. Chỉ dùng `save_screen` cho màn hình mới hoặc nháp.
2. **Bẫy P4 (Shape Check của nháp)**: Public trên Tenant Admin promote nháp; vì vậy sau `save_screen` phải gọi `preview_screen(screenCode=code)` và đạt `shapeCheck.ok == true` trước khi báo xong B5. AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10).
3. **Bẫy DISP-4 (`binding_conflict`)**: Trùng điều kiện `conditions` với một màn hình đã published khác trong cùng theme. Đổi conditions hoặc archive màn hình cũ.
4. **Bẫy DISP-5 (`shape_check_failed`)**: JS blob chứa mã cấm (`fetch(`, `window.location`, `eval`). Mọi tương tác mạng phải đi qua `ctx.execute`. Xem chi tiết tại [renderer-pitfalls.md](file://skills/tap-screen/references/renderer-pitfalls.md).
5. **Bẫy `forbidden_session_value_key`**: Chỉ được gán session value cho các key có `writable: true` trong catalog `list_session_values`.

Xem các mẫu code Javascript renderer chuẩn tại [examples.md](file://skills/tap-screen/references/examples.md).
