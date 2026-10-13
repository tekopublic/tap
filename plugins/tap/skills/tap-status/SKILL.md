---
name: tap-status
description: Kiểm tra trạng thái tổng quan của tenant (màn hình, flow, persona, preset, runtime config, theme) theo chế độ chỉ đọc và đối chiếu danh sách công cụ MCP khả dụng. An toàn chạy cả trên PROD.
user-invocable: false
---

# TAP Status — Internal Worker (Chỉ Đọc)

**Delegated-by: tap-orchestration.** Không nhận request trực tiếp, không tạo/resume work item, không hỏi clarification/approval. Chỉ thực hiện khi có `workItemId`, resolved capability và phase từ gateway; thiếu context thì trả `BLOCKED` để gateway xử lý.

Skill đọc trạng thái toàn diện của tenant mà không thực hiện bất kỳ thao tác ghi nào. An toàn để chạy trên cả môi trường PROD.

## Quy Trình 9 Bước Đọc (≤ 9 Lời Gọi Tool)

1. **`ping`** → Xác nhận phiên đăng nhập, lấy email và tên service.
2. **`list_screens`** → Đếm màn hình theo trạng thái (`published`, `draft`, `archived`).
3. **`list_interaction_flows`** → Kiểm tra flow có `hasDraft: true` nào đang treo chưa publish.
4. **`get_persona`** → Lấy bản persona đang published.
5. **`get_persona_draft`** → Kiểm tra có bản nháp nào khác bản published không.
6. **`get_runtime_config`** → Xem cấu hình runtime hiện tại.
7. **`list_parameter_presets`** → Đếm số preset chip đang active.
8. **`get_theme`** → Xem theme token và layout hiện tại.

## Bảng Tổng Hợp Trạng Thái

Xuất bảng tổng hợp cuối phiên với các thông tin:

| Hạng Mục | Giá Trị Hiện Tại | Cảnh Báo |
|---|---|---|
| Màn hình published | N | - |
| Màn hình draft (chưa publish) | N | ⚠️ nếu > 0 |
| Interaction flow có draft treo | N | ⚠️ nếu > 0 |
| Persona có draft khác published | Có/Không | ⚠️ nếu Có |
| Số preset chip | N | - |
| Theme layout hiện tại | `layoutCode` | - |
| Theme token màu chủ đạo | `color.primary` | - |

## MCP Đang Dùng

In thêm bảng: server đang chọn (`scripts/mcp_pref.py get`) và môi trường LOCAL/PROD; các server TAP khác khả dụng; connector TAP đang lỗi (Reconnect/Connect) nếu thấy. Người dùng muốn đổi thì nói tên server, gateway lưu lại.

## Đối Chiếu Danh Sách Công Cụ MCP

Sau khi đọc xong, so sánh danh sách tool đang thấy trong phiên với `tool-index.md`:
- **Tool thiếu** (có trong `tool-index.md` nhưng không thấy trong phiên): Cảnh báo có thể do thiếu quyền IAM — in tên tool và chuỗi quyền tương ứng.
- **Tool lạ** (có trong phiên nhưng không có trong `tool-index.md`): Cảnh báo server có thể mới hơn plugin — đề nghị chạy lại `sync_from_code.py`.
