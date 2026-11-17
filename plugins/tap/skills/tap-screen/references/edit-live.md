# Quy Trình Sửa & Gỡ Màn Hình Đang Live (Edit & Delete Live Screen)

## 1. Sửa Màn Hình Đang LIVE (plugin 3.3.0, sau #327)

Từ #327, `save_screen` **chỉ ghi nháp** (mang `requirementId`); bản đang live không đổi cho tới khi người có quyền Public trên Tenant Admin web. AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10).

### Luồng chuẩn (B5, đã có plan approval):
1. **Backup (`BK`)**: `get_screen(code)` → lưu `blobContent`, `name`, `conditions`, `themeId` vào `./.tap-backups/<UTC>-screen-<code>.json`.
2. **Sửa JS blob** dựa trên bản vừa backup.
3. **Preview**: `preview_screen(blobContent=new_blob, ctx=...)`; `shapeCheck.ok == true`, `consoleErrors` rỗng.
4. **Ghi nháp**: `save_screen(code, name, blobContent=new_blob, conditions, requirementId)`.
5. **Khai thay đổi**: `declare_requirement_changes` (artifact `screen:<code>`, lý do, ID dòng) → `record-change`.
6. **Kiểm chứng nháp**: `preview_screen(screenCode=code)` đạt shape check; `get_screen(code)` thấy nháp mới, bản live giữ nguyên.

---

## 2. Gỡ / Xóa Màn Hình (Delete Screen)

Xóa màn hình là thao tác R3 (phá hủy, giải phóng binding cho màn hình khác chiếm dụng).

1. **Bước 1**: Gọi `get_screen(code)` và sao lưu đầy đủ thông tin ra file backup.
2. **Bước 2**: Trình bày thẻ Cổng R3 (xem `gate-templates.md`). Yêu cầu người dùng gõ chính xác:
   > `DELETE <code>`
3. **Bước 3**: Gọi `delete_screen(code)`.
4. **Bước 4**: Gọi `list_screens` để kiểm chứng màn hình đã không còn tồn tại trong theme.
