# Quy Trình Sửa & Gỡ Màn Hình Đang Live (Edit & Delete Live Screen)

## 1. Sửa Màn Hình Đang LIVE (Tránh Bẫy P3)

### Vì sao không được gọi `save_screen`?
Trong hệ thống backend TAP, hàm `save_screen` luôn cập nhật trạng thái `status = 'draft'` đè lên bản ghi hiện tại. Nếu bạn gọi `save_screen` cho một màn hình đang live trên storefront, màn hình đó sẽ bị **hạ cấp thành bản nháp ngay lập tức** và shopper sẽ bị mất giao diện cho tới khi bạn publish lại.

### Luồng chuẩn để sửa bản live:
1. **Bước 1 — Backup (`BK`)**:
   - Gọi `get_screen(code)`.
   - Trích xuất toàn bộ `blobContent`, `name`, `conditions`, `themeId`.
   - Lưu vào file `./.tap-backups/<UTC>-publish_screen-<code>.json`.
2. **Bước 2 — Sửa đổi JS Blob**:
   - Chỉnh sửa logic JS hoặc CSS dựa trên `blobContent` vừa backup.
3. **Bước 3 — Preview & Kiểm Tra Lỗi**:
   - Gọi `preview_screen(blobContent=new_blob, ctx=...)`.
   - Đảm bảo `shapeCheck.ok == true` và không có lỗi trong `consoleErrors`.
4. **Bước 4 — Cổng xác nhận Gate `G`**:
   - Trình bày thẻ xác nhận R2, chỉ rõ nơi đã lưu file backup và cách rollback nếu có sự cố.
   - Chờ người dùng trả lời "yes".
5. **Bước 5 — Ghi đè nguyên tử (Atomic Publish)**:
   - Gọi `publish_screen(code, name, blobContent=new_blob, conditions)`.
   - Lệnh này sẽ ghi đè trực tiếp mà vẫn giữ nguyên trạng thái `status = 'published'`, không gây gián đoạn cho shopper.
6. **Bước 6 — Kiểm chứng (Verify)**:
   - Gọi `get_screen(code)` kiểm tra lại.
   - Nếu phát hiện lỗi ngoài ý muốn: Thực hiện rollback ngay bằng cách gọi `publish_screen` với `blobContent` từ file backup ở Bước 1.

---

## 2. Gỡ / Xóa Màn Hình (Delete Screen)

Xóa màn hình là thao tác R3 (phá hủy, giải phóng binding cho màn hình khác chiếm dụng).

1. **Bước 1**: Gọi `get_screen(code)` và sao lưu đầy đủ thông tin ra file backup.
2. **Bước 2**: Trình bày thẻ Cổng R3 (xem `gate-templates.md`). Yêu cầu người dùng gõ chính xác:
   > `DELETE <code>`
3. **Bước 3**: Gọi `delete_screen(code)`.
4. **Bước 4**: Gọi `list_screens` để kiểm chứng màn hình đã không còn tồn tại trong theme.
