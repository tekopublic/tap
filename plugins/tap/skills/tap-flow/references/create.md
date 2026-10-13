# Quy Trình Tạo Interaction Flow Mới (Create Flow)

## Quy Trình 6 Bước

### Bước 1: Khám Phá Định Dạng & Tránh Trùng Lặp
- Gọi `describe_interaction_flow_format` để lấy schema chuẩn của flow (các loại field, thuộc tính step, validation).
- Gọi `list_interaction_flows` để xem danh sách flow hiện có, tránh trùng `title`.
- Nếu flow có submit action: Gọi `describe_endpoint(operationId)` để xác định đúng tham số payload gửi đi.

### Bước 2: Soạn Thảo Schema
- Xây dựng object `parsedSchema` chứa `title`, `steps`, `fields`, `actions`.
- Không gửi chuỗi Markdown thô; phải gửi trực tiếp JSON object đã parse.

### Bước 3: Lưu Bản Nháp Đầu Tiên (Save Draft)
- Gọi `save_interaction_flow(parsedSchema)` **KHÔNG truyền `flowId`**.
- Server sẽ cấp một `flowId` mới (số nguyên). **Ghi lại `flowId` này** để dùng cho toàn bộ các bước tiếp theo.

### Bước 4: Preview Từng Bước (Simulation)
- Khởi tạo preview: Gọi `preview_interaction_flow(flowId)`.
- Nhận về `previewSessionId` và trạng thái bước đầu tiên.
- Lần lượt gửi hành động điều khiển:
  - Điền giá trị: `control = {"op": "setValue", "fieldId": "...", "value": "..."}`
  - Chuyển bước: `control = {"op": "nextStep"}`
  - Gửi dữ liệu: `control = {"op": "submit"}`
- Khi nhận được `terminal: true`: Luồng kết thúc, ngừng gửi lệnh control.

### Bước 5: Cổng Xác Nhận Gate `G`
- Trình bày thẻ xác nhận R2 (xem `gate-templates.md`).
- Nêu rõ: `flowId`, `title`, số bước đã test qua preview, endpoint submit.
- Chờ người dùng trả lời "yes".

### Bước 6: Publish & Kiểm Chứng
- Gọi `publish_interaction_flow(flowId)`.
- Nếu gặp `validation_error`: Đọc mảng `issues[]` $\rightarrow$ sửa `parsedSchema` $\rightarrow$ gọi `save_interaction_flow(parsedSchema, flowId)` $\rightarrow$ publish lại.
- Gọi `get_interaction_flow(flowId)` để kiểm chứng `publishedVersion`.
