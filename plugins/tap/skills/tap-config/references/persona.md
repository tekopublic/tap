# Quản Lý Persona AI Của Tenant (Persona Management)

Persona là cấu hình giọng nói và tính cách của chatbot AI trên storefront, bao gồm: greeting, farewell, fallback message, tone style và 4 system prompts chuyên biệt.

## Luồng Chuẩn: Draft → Publish (An Toàn)

### Bước 1 — Backup Bản Published Hiện Tại
```
get_persona()
```
Lưu toàn bộ JSON trả về vào file `./.tap-backups/<UTC>-persona-published.json`.

### Bước 2 — Đọc Bản Nháp Hiện Tại
```
get_persona_draft()
```
- Nếu trả về `present: false` → Chưa có bản nháp: Dùng bản từ `get_persona` làm nền để chỉnh sửa.
- Nếu `present: true` → Có bản nháp chưa publish: Hỏi người dùng muốn tiếp tục bản nháp cũ hay bắt đầu từ bản published.

### Bước 3 — Soạn Bản Nháp Mới
Chuẩn bị đối tượng `fields` gồm đủ 9 trường (REPLACE toàn bộ, không được thiếu trường nào; trường không thay đổi giữ nguyên giá trị gốc, trường muốn xóa truyền `null`):
- `greeting`: Lời chào khi mở chatbot.
- `farewell`: Lời tạm biệt khi đóng chatbot.
- `fallback`: Tin nhắn mặc định khi không hiểu ý định người dùng.
- `brand_name`: Tên thương hiệu chatbot.
- `tone`: Phong cách giao tiếp (ví dụ: "professional", "friendly", "casual").
- `system_prompt_search`: Prompt cho luồng tìm kiếm sản phẩm.
- `system_prompt_support`: Prompt cho luồng hỗ trợ khách hàng.
- `system_prompt_product_detail`: Prompt cho luồng xem chi tiết sản phẩm.
- `system_prompt_checkout`: Prompt cho luồng thanh toán.

### Bước 4 — Lưu Bản Nháp
```
save_persona_draft(fields=<đối tượng 9 trường>)
```

### Bước 5 — Đối Chiếu Nháp
- Gọi lại `get_persona_draft()` để lấy giá trị đã lưu.
- So sánh từng trường quan trọng với bản published, trình bày cho người dùng.

### Bước 6 — Khai Thay Đổi, Dừng Ở Nháp
- `declare_requirement_changes` (artifact `persona`, lý do, ID dòng) → `record-change`.
- Không gọi `publish_persona`. AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10).

---

## Lưu Ý Về `update_persona` (Ghi Thẳng Bản Live)
Chỉ dùng `update_persona` khi người dùng **nói rõ** muốn "ghi thẳng" hoặc "bỏ qua bước nháp":
- Ghi đè bản published ngay lập tức, hiệu lực sau ≤ 60s.
- Cũng áp dụng cơ chế REPLACE toàn bộ.
- Bắt buộc backup (`get_persona` → lưu file) + cổng R2 mạnh hơn trước khi gọi.
