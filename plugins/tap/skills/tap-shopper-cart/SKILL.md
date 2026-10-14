---
name: tap-shopper-cart
description: Worker nội bộ cho giỏ hàng/khuyến mãi/checkout của shopper — xem, thêm, sửa, xóa giỏ hàng, áp promotion, vào checkout — qua capability MCP được discover; báo rõ lỗi, vị trí lỗi và cách khắc phục.
user-invocable: false
---

# TAP Shopper Cart — Internal Worker

**Delegated-by: tap-orchestration.** Không nhận request trực tiếp, không tạo/resume work item, không hỏi clarification/approval. Chỉ chạy khi có `workItemId`, resolved capability và phase từ gateway; thiếu context thì trả `BLOCKED` để gateway xử lý. Đọc `tap-core` trước.

Giỏ hàng là capability được hỗ trợ đầy đủ. Không giả định tên server, `operationId`, panel code hay repo nguồn; mọi thứ phải được MCP xác nhận.

## 1. Discovery bắt buộc

1. `ping`, rồi resolve tool theo hậu tố (`tap-core` §1).
2. Dùng read capability sẵn có (`list_services`, `list_endpoints`, `describe_endpoint`, `list_state_transitions`, `describe_state`, `list_session_values`, `get_screen`) để tìm operation/state/panel của cart. Mô tả endpoint trước khi dùng.
3. Chỉ tiếp tục khi operation, response shape và panel contract được MCP xác nhận.

## 2. Catalog intent

| Intent | Phân loại | Dữ liệu bắt buộc | Hành động sau discovery |
|---|---|---|---|
| `VIEW_CART` | read-only | Không | Đọc cart, mở/cập nhật panel cart đã khai báo. Không cần plan approval. |
| `ADD_TO_CART` | write reversible | SKU/item, quantity | Gọi operation add đã resolve, rồi read-back. |
| `UPDATE_CART_ITEM` | write reversible | Item duy nhất, quantity mục tiêu | Update, rồi read-back. |
| `REMOVE_CART_ITEM` | destructive | Item duy nhất | Remove; target mơ hồ thì hỏi chọn, không đoán. |
| `APPLY_PROMOTION` | write reversible | Promotion/code | Apply, rồi read-back. |
| `CHECKOUT` | exceptional | Cart/checkout context | Vào checkout capability đã plan; tạo order/payment thật phải qua Gate `G` riêng (`tap-core` §4). |

## 3. VIEW_CART

Nhận diện: "Giỏ hàng của tôi có gì?", "Hiện tôi đang mua những gì?", "show my cart", "what's in my basket". Chỉ gọi read capability đã resolve; cấm add/update/remove, apply/remove promotion, checkout, mutation và ghi session value.

Chat nêu: tổng số món; tên sản phẩm, biến thể, số lượng; tạm tính; khuyến mãi đang áp dụng; câu "Bạn muốn sửa số lượng, xoá món hay thanh toán?". Cart rỗng thì nói rõ rỗng và gợi ý tiếp tục mua sắm. Panel chỉ dùng panel cart được catalog xác nhận (danh sách, biến thể, số lượng, đơn giá, tổng tiền, khuyến mãi); không author/publish panel cho truy vấn này.

## 4. Lỗi: báo rõ ở đâu, cách khắc phục

Không bao giờ từ chối chung chung hay bịa dữ liệu. Khi một bước không chạy được, trả `BLOCKED` kèm 3 ý, rồi gateway hiển thị báo cáo theo [error-report.md](file://skills/tap-core/references/error-report.md):

1. **Lỗi ở đâu:** bước (discovery/read/write/read-back), tool/operation, mã lỗi.
2. **Nguyên nhân:** thiếu operation cart cho tenant (`missing-api`), thiếu panel/config (`missing-config`), thiếu quyền (`permission-denied`), tool bị ẩn (`tool-hidden`), lỗi server (`server-error`), thiếu SKU/quantity/item mơ hồ (hỏi lại người dùng, không phải lỗi hệ thống).
3. **Cách khắc phục:** việc người dùng làm được ngay, và việc cần team TAP làm.

Write dở dang (đã add nhưng read-back lỗi...) phải nêu đúng trạng thái giỏ hiện tại.

## 5. Kiểm chứng

Trước `COMPLETED`: output đủ trường summary; read-back khớp thao tác; VIEW_CART không có write tool trong audit trail; panel request chỉ dùng panel đã resolve. Thiếu field thì `BLOCKED` hoặc nêu unavailable.
