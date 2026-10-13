# Mẫu Thẻ Cổng Xác Nhận Thao Tác Ghi (Gate Templates)

## Mẫu Cổng R2 — Ghi Live Hoàn Tác Được (Xác nhận "yes")

Dùng cho: `publish_screen`, `publish_interaction_flow`, `publish_persona`, `update_persona`, `update_runtime_config`, `add_parameter_preset`, `remove_parameter_preset`, `update_theme`, `set_layout`, `save_screen` (khi màn hình đang live).

```markdown
### ⚠️ CỔNG XÁC NHẬN GHI LIVE (R2)

| Thông Tin | Chi Tiết |
|---|---|
| **Môi trường** | **LOCAL** (`agentic-storefront-mcp`) *(Nếu PROD: BỊ CHẶN)* |
| **Công cụ (Tool)** | `publish_screen` |
| **Đối tượng** | Màn hình `code="cart_empty_v2"` (Theme ID: 12) |
| **Tác động trực tiếp** | Ghi đè màn hình live và phục vụ ngay lập tức cho shopper. |
| **Kết quả Preview** | `shapeCheck.ok: true` (0 console errors, 1 datasource đã bind). |
| **Sao lưu hiện tại** | Đã lưu tại: `./.tap-backups/20261008T120000Z-publish_screen-cart_empty_v2.json` |
| **Cách hoàn tác** | Gọi lại `publish_screen` với `blobContent` trong file sao lưu. |

👉 **Vui lòng trả lời `yes` nếu bạn đồng ý xuất bản thay đổi này lên hệ thống.**
```

---

## Mẫu Cổng R3 — Xóa Hoặc Khó Hoàn Tác (Gõ lại từ khóa)

Dùng cho: `delete_screen`, `delete_interaction_flow`, `archive_report`, `publish_report`, `unpublish_report`.

```markdown
### 🚨 CỔNG XÁC NHẬN THAO TÁC NGUY HIỂM / KHÓ HOÀN TÁC (R3)

| Thông Tin | Chi Tiết |
|---|---|
| **Môi trường** | **LOCAL** (`agentic-storefront-mcp`) |
| **Công cụ (Tool)** | `delete_screen` |
| **Đối tượng** | Màn hình `code="promo_banner_summer"` |
| **Tác động trực tiếp** | Màn hình bị gỡ khỏi storefront ngay lập tức. Binding bindingSignature sẽ bị thu hồi. |
| **Sao lưu hiện tại** | Đã lưu tại: `./.tap-backups/20261008T120000Z-delete_screen-promo_banner_summer.json` |
| **Rủi ro** | Thao tác xóa không thể undo tự động bằng 1 nút bấm. |

👉 **Thao tác có tính chất phá hủy! Để xác nhận, vui lòng gõ chính xác cụm từ sau:**
> `DELETE promo_banner_summer`
```
