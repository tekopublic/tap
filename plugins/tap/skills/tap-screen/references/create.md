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

### Bước 5: Ghi Nháp (B5, đã có plan approval)
- Gọi `save_screen(code, name, blobContent, conditions, requirementId)` — chỉ ghi nháp, shopper không thấy.
- Gọi `declare_requirement_changes` (artifact `screen:<code>` + lý do + ID dòng) rồi `work_item_state.py record-change`.

### Bước 6: Kiểm Chứng Nháp
- Gọi `preview_screen(screenCode=code)`: `shapeCheck.ok == true`, `consoleErrors` rỗng.
- Gọi `get_screen(code)` xác nhận nháp đã lưu. Không gọi `publish_screen`; AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10).
