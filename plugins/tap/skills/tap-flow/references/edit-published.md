# Sửa Và Gỡ Interaction Flow Đã Published

## 1. Sửa Interaction Flow Đang Chạy Live

Khác với màn hình display, hệ thống Interaction Flow có cơ chế tách biệt rõ ràng giữa bản nháp (`draft`) và bản đang live (`publishedVersion`):
- Gọi `save_interaction_flow(parsedSchema, flowId)` sẽ **chỉ ghi vào bản nháp của flow đó**.
- Bản published của flow vẫn phục vụ người dùng bình thường cho đến khi người có quyền Public trên Tenant Admin web. AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10).

### Các bước thực hiện:
1. **Bước 1 — Backup**:
   - Gọi `get_interaction_flow(flowId)` để lấy bản schema hiện tại.
   - Lưu vào file backup `./.tap-backups/<UTC>-flow-<flowId>.json`.
2. **Bước 2 — Cập nhật nháp**:
   - Chỉnh sửa `parsedSchema` theo yêu cầu mới.
   - Gọi `save_interaction_flow(parsedSchema, flowId=flowId, requirementId)`. **Bắt buộc truyền `flowId`**.
3. **Bước 3 — Preview thử nghiệm**:
   - Gọi `preview_interaction_flow(flowId)` để chạy thử các nhánh mới.
4. **Bước 4 — Khai thay đổi**: `declare_requirement_changes` (artifact `flow:<flowId>`, lý do, ID dòng) → `record-change`.
5. **Bước 5 — Kiểm chứng nháp**: `get_interaction_flow(flowId)` thấy nháp mới; bản published giữ nguyên. Không gọi `publish_interaction_flow`.
6. **Khôi phục nếu nháp sai**: `save_interaction_flow(old_schema, flowId, requirementId)` từ file backup ở Bước 1.

---

## 2. Gỡ / Xóa Interaction Flow (Delete Flow)

Thao tác xóa flow là **thao tác R3 (phá hủy một chiều, không thể undo tự động)**.
1. Sao lưu schema hiện tại của flow ra file backup.
2. Trình bày thẻ Cổng R3, yêu cầu người dùng gõ xác nhận:
   > `DELETE <flowId>`
3. Gọi `delete_interaction_flow(flowId)`.
4. Gọi `list_interaction_flows` để kiểm tra flow đã bị loại bỏ.
*(Lưu ý: Các phiên tương tác của shopper đang dở dang vẫn sẽ chạy với phiên bản schema đã pin trước đó cho tới khi kết thúc).*
