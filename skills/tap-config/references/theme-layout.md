# Quản Lý Theme (Màu Sắc) & Layout Storefront

## 1. Cập Nhật Theme Token Màu Sắc

Hệ thống chỉ cho phép tùy biến đúng **5 brand token** sau đây. Nếu người dùng yêu cầu thay đổi token ngoài danh sách này, hãy giải thích giới hạn và không tìm cách vòng qua.

| Token | Ý Nghĩa | Ví Dụ Giá Trị |
|---|---|---|
| `color.primary` | Màu chủ đạo (nút CTA, highlight) | `#0052CC` |
| `color.primary.hover` | Màu chủ đạo khi hover | `#0040A1` |
| `color.primary.contrast` | Màu chữ trên nền primary | `#FFFFFF` |
| `color.chat.user` | Màu bubble tin nhắn của người dùng | `#E3F0FF` |
| `color.chat.assistant` | Màu bubble tin nhắn của AI | `#F5F5F5` |

### Quy Trình Cập Nhật Theme

```
get_theme()                   → Backup toàn bộ (tokens, allowedTokens, layoutCode)
```

**Cổng xác nhận R2** (nêu token thay đổi và màu mới) → `update_theme(tokens={...}, name?)` → `get_theme()` (V).

> **Lưu ý**: Hiện chưa có tool preview trực tiếp cho thay đổi theme. Người dùng có thể dùng `preview_screen(blobContent, ctx={theme: {...}})` để xem gần đúng (chưa được xác nhận chính thức).

> **Lỗi `token_not_allowed`**: Khi gặp lỗi này, hãy giải thích danh sách 5 token được phép cho người dùng. Tuyệt đối không thử lại với cùng token đó.

---

## 2. Đổi Layout (Bố Cục Trang Storefront)

Layout quyết định bố cục tổng thể của storefront (vị trí header, sidebar, footer...).

### Quy Trình Đổi Layout

```
list_layouts()                → Xem danh sách layoutCode + designSystem khả dụng
get_theme()                   → Backup (ghi nhận layoutCode hiện tại)
```

**Cổng xác nhận R2** (nêu layoutCode mới và tác động tới toàn bộ giao diện) → `set_layout(layoutCode, designSystem)` → `get_theme()` (V, kiểm tra `layoutCode` trong kết quả).

> ⚠️ **Thao tác có tác động rộng**: Đổi layout ảnh hưởng toàn bộ giao diện của tenant. Hãy cảnh báo rõ người dùng về phạm vi tác động trước khi tiến hành.
