# Quản Lý Parameter Presets & Runtime Config

## 1. Parameter Preset Chip

Preset chip là các chip tìm kiếm nhanh hiện trên giao diện storefront (ví dụ: "Laptop Gaming", "Điện thoại dưới 5 triệu"). Mỗi preset gồm `triggers` (danh sách từ kích hoạt) và `params` (các tham số lọc gắn theo).

### Thêm Preset Chip Mới

```
list_parameter_presets()      → Backup toàn bộ danh sách hiện tại
list_parameters()             → Xem các tham số lọc khả dụng
search_parameter_values(query, parameterName)  → Lấy giá trị thật (không tự bịa)
```

**Cổng xác nhận R2** → `add_parameter_preset(triggers, params)` → `list_parameter_presets()` (V).

**Xử lý `preset_conflict`**: Nếu trả về lỗi `preset_conflict` (trùng `triggers[0]`):
- Thông báo cho người dùng preset với trigger đó đã tồn tại.
- Hỏi người dùng: "Muốn ghi đè bằng cách xóa preset cũ rồi thêm lại, hay đặt trigger khác?"
- Tuyệt đối không tự động gọi `remove_parameter_preset`.

### Xóa Preset Chip

```
list_parameter_presets()      → Backup
```

**Cổng xác nhận R2** (nêu tên trigger và params sẽ mất) → `remove_parameter_preset(trigger)` → `list_parameter_presets()` (V).

---

## 2. Runtime Config (Cấu Hình Nâng Cao)

Runtime config chứa 4 khóa điều khiển hành vi AI trên storefront. **KHÔNG dùng `update_runtime_config` cho thao tác thêm/xóa preset** (dùng `add/remove_parameter_preset` cho việc đó).

### Quy Trình Cập Nhật Runtime Config

```
get_runtime_config()          → Backup toàn bộ config hiện tại
```

Chỉnh sửa object trả về (chỉ thay đổi giá trị cần thiết, giữ nguyên 3 khóa còn lại):

```json
{
  "targetStates": {...},       → Các state machine target mặc định
  "contextDefaults": {...},    → Giá trị context mặc định cho AI
  "parameterPresets": [...],   → KHÔNG nên sửa ở đây; dùng add/remove_parameter_preset
  "preferredParams": [...]     → Thứ tự ưu tiên các parameter
}
```

**Cổng xác nhận R2** → `update_runtime_config(fields=<đủ 4 khóa>)` → `get_runtime_config()` (V).

> ⚠️ **Lỗi `partial_payload`**: Server từ chối ngay nếu payload thiếu bất kỳ khóa nào trong 4 khóa bắt buộc trên. Truyền `null` cho khóa muốn xóa/reset, không được bỏ qua khóa.
