# Quy Trình Tạo Màn Hình Mới (Create Screen)

Áp dụng khi màn hình `code` chưa từng tồn tại hoặc đang ở trạng thái `draft`.

## Quy Trình 6 Bước

### Bước 1: Khám Phá API & Catalog (Discovery)
- Gọi `describe_display_format` (1 lần mỗi phiên để nắm hợp đồng renderer).
- Nếu màn hình cần dữ liệu hoặc tương tác:
  - `list_services` $\rightarrow$ `list_endpoints(serviceCode)` $\rightarrow$ `describe_endpoint(operationId)`.
  - Tuyệt đối không tự bịa `operationId` trong `dataSources` hoặc `ctx.execute`.

### Bước 2: Rà Soát Binding & Điều Kiện Hiển Thị (Grounding)
- Gọi `list_screens` để kiểm tra các binding hiện có trong theme, tránh xung đột `binding_conflict` (DISP-4).
- Gọi `list_modules` và `list_entities` để lấy đúng module/entity cho tham số `conditions`.
- Gọi `list_session_values` để lấy các key được phép ghi qua `ctx.setSessionValue`.

### Bước 3: Soạn Thảo JS Renderer (Authoring)
- Viết Javascript ES module xuất hàm `export function mount(root, ctx)`.
- Nếu có dữ liệu backend: Xuất thêm `export const dataSources = {...}` khớp đúng định nghĩa `describe_endpoint`.
- Không sử dụng import bên ngoài, không gọi `fetch` trực tiếp.

### Bước 4: Preview & Shape Check (Bắt buộc)
- Gọi `preview_screen(blobContent, ctx)`:
  - Kiểm tra `shapeCheck.ok == true`.
  - Đảm bảo `consoleErrors` rỗng.
  - Đối chiếu mảng `executeCalls` với endpoint mong muốn.
  - Nếu `shapeCheck.ok == false`: Sửa lại JS blob và gọi preview lại cho đến khi sạch lỗi.

### Bước 5: Cổng Xác Nhận (Gate `G`)
- Trình bày thẻ xác nhận R2 (xem mẫu trong `gate-templates.md`).
- Nêu rõ: Target (LOCAL), `code`, `conditions`, số lỗi console = 0, shape check đạt.
- Chờ người dùng trả lời "yes".

### Bước 6: Publish & Kiểm Chứng (Verify)
- Gọi `publish_screen(code, name, blobContent, conditions)`.
- Gọi ngay `get_screen(code)` để xác nhận `status == "published"` và nội dung blob đã được lưu.
- Gọi `list_screens` để kiểm tra binding đã nhận diện thành công.
