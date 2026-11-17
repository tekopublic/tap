# Mẫu Thẻ Cổng Xác Nhận Thao Tác Ghi (Gate Templates)

## Mẫu Cổng R2 — Ghi Live Hoàn Tác Được (Xác nhận "yes")

Dùng cho (AI không còn gọi `publish_*` từ plugin 3.3.0): `update_persona`, `update_runtime_config`, `add_parameter_preset`, `remove_parameter_preset`, `update_theme`, `set_layout`, `save_screen` (khi màn hình đang live).

```markdown
### ⚠️ CỔNG XÁC NHẬN GHI LIVE (R2)

| Thông Tin | Chi Tiết |
|---|---|
| **Môi trường** | **LOCAL** (`agentic-storefront-mcp`) *(Nếu PROD: BỊ CHẶN)* |
| **Công cụ (Tool)** | `update_runtime_config` |
| **Đối tượng** | Màn hình `code="cart_empty_v2"` (Theme ID: 12) |
| **Tác động trực tiếp** | Ghi đè màn hình live và phục vụ ngay lập tức cho shopper. |
| **Kết quả Preview** | `shapeCheck.ok: true` (0 console errors, 1 datasource đã bind). |
| **Sao lưu hiện tại** | Đã lưu tại: `./.tap-backups/20261008T120000Z-runtime_config.json` |
| **Cách hoàn tác** | Gọi lại `update_runtime_config` với nội dung trong file sao lưu. |

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

## Mẫu Khung hỏi / nêu vấn đề (plugin 3.3.0, áp dụng mọi câu hỏi và mọi vấn đề)

Không bao giờ chỉ nêu vấn đề hoặc hỏi trống.

```markdown
**<Vấn đề / câu hỏi — 1 câu>**
- **A.** <phương án> — <hệ quả: UX / dữ liệu / rủi ro / công sức> **(Đề xuất)**
- **B.** <phương án> — <hệ quả>
- **C.** <phương án> — <hệ quả>

Đề xuất A vì <lý do ngắn dựa trên hiện trạng thật: MCP, live probe, theme...>. Trả lời bằng chữ cái.
```

Chỉ có một hướng hợp lệ (vd thiếu quyền): nêu hướng đó + việc cụ thể người dùng cần làm.

## Mẫu Sai bước (plugin 3.3.1)

Khi `work_item_state.py` trả `ok:false` hoặc phát hiện nhảy bước:

```markdown
### Dừng: sai thứ tự bước

<bảng tiến trình — in nguyên output `progress <workItemId>`>

Đang ở **<currentStep> — <tên bước>**. Sai ở: <error>. Thiếu: <missingGates>.

- **A.** Quay về làm đúng <currentStep>: <nextAction> **(Đề xuất)**
- **B.** Huỷ yêu cầu này (không ghi gì thêm)

Mọi yêu cầu có ghi phải đi đủ B0 → B6 (gồm B1.5, B2.5), không có ngoại lệ.
```

## Mẫu B2.5 Rà soát độ phủ (plugin 3.3.1)

```markdown
### Danh sách yêu cầu cần phủ

| R | Nội dung | Nguồn |
|---|---|---|
| R1 | <một ý của yêu cầu> | issue |
| R2 | <...> | chat |

**Câu hỏi làm rõ (tối đa 5)** — mỗi câu theo Khung hỏi.

Trả lời bằng chữ cái; câu không trả lời sẽ dùng phương án đề xuất.
```

## Mẫu ma trận phủ dưới bảng B3 (plugin 3.3.1)

```markdown
**Ma trận phủ**

| R | Nội dung | ID case |
|---|---|---|
| R1 | <...> | CART-ADD-001A, CART-ADD-001B |

**Chưa phủ:** R5 — <lý do> (hoặc "Không có")

**Rà độc lập (vòng <n>):** <số> lỗi chặn còn tồn, <số> cảnh báo
| Ref | Lỗi | Đề xuất |
|---|---|---|
```
