---
name: tap-config
description: "Quản lý cấu hình tenant qua MCP TAP - persona AI (giọng, brand, fallback), parameter preset chip, runtime config, theme token màu sắc và layout storefront. Dùng khi người dùng muốn đổi giọng chatbot, chip tìm kiếm, màu chủ đạo, bố cục."
user-invocable: false
---

# TAP Config — Internal Worker

**Delegated-by: tap-orchestration.** Không nhận request trực tiếp, không tạo/resume work item hoặc tự hỏi clarification/approval. Chỉ thực hiện subtask có `workItemId`, resolved scope/capability và phase từ gateway; thiếu context thì trả `BLOCKED`/route lại gateway trước mọi MCP write.

**Cổng ghi (plugin 3.3.0):** trước MỌI MCP write chạy `python3 scripts/work_item_state.py show <workItemId>` và kiểm `state == IMPLEMENTING` (đã qua B0–B4) và `savedRequirement.requirementId` có giá trị. Thiếu một trong hai → trả `BLOCKED` về gateway kèm output `progress <workItemId>`, không gọi tool ghi. Mọi tool ghi nháp truyền `requirementId`. Không bao giờ gọi `publish_*` (Public chỉ trên Tenant Admin web). Báo vấn đề cho người dùng theo Khung hỏi của gateway (phương án + đề xuất).

Skill quản lý các tham số tùy biến cấu hình của tenant trên storefront.

## 1. Nguyên Tắc Cốt Lõi
- Đọc `tap-core` trước khi thực hiện bất kỳ thao tác nào.
- Mọi thao tác ghi phải có bước đọc + backup trước (dùng `get_*` tương ứng).
- Persona: chỉ ghi nháp (`save_persona_draft`, mang `requirementId`), không `publish_persona`; AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10). Chỉ dùng `update_persona` (ghi thẳng bản live) khi người dùng yêu cầu rõ ràng, sau B4 và qua Cổng R2.

## 2. Bảng Quyết Định Theo Loại Cấu Hình

| Loại Cấu Hình | Công Cụ Chính | Tài Liệu Chi Tiết |
|---|---|---|
| Giọng AI / Persona (safe) | `get_persona` → backup → `get_persona_draft` → `save_persona_draft` → `get_persona_draft` (đối chiếu) → dừng ở nháp (Public trên Tenant Admin) | [persona.md](file://skills/tap-config/references/persona.md) |
| Parameter Preset Chip (thêm) | `list_parameter_presets` → backup → `search_parameter_values` → Cổng R2 → `add_parameter_preset` | [presets-runtime.md](file://skills/tap-config/references/presets-runtime.md) |
| Parameter Preset Chip (xóa) | `list_parameter_presets` → backup → Cổng R2 → `remove_parameter_preset` | [presets-runtime.md](file://skills/tap-config/references/presets-runtime.md) |
| Runtime Config (các trường khác) | `get_runtime_config` → backup → mutate đủ 4 key → Cổng R2 → `update_runtime_config` | [presets-runtime.md](file://skills/tap-config/references/presets-runtime.md) |
| Theme (màu sắc 5 token) | `get_theme` → backup → Cổng R2 → `update_theme(tokens)` → `get_theme` (V) | [theme-layout.md](file://skills/tap-config/references/theme-layout.md) |
| Layout (bố cục storefront) | `list_layouts` → `get_theme` → backup → Cổng R2 → `set_layout(layoutCode, designSystem)` → `get_theme` (V) | [theme-layout.md](file://skills/tap-config/references/theme-layout.md) |

## 3. Các Bẫy Nghiệp Vụ Quan Trọng
1. **Bẫy `partial_payload` (update_runtime_config)**: Tool này yêu cầu đủ **4 khóa bắt buộc** trong payload: `targetStates`, `contextDefaults`, `parameterPresets`, `preferredParams`. Nếu thiếu bất kỳ khóa nào, server trả lỗi `partial_payload`. Cách đúng: Luôn `get_runtime_config` trước để lấy toàn bộ 4 khóa, rồi chỉ sửa đổi giá trị cần thiết.
2. **Bẫy Preset Conflict**: `preset_conflict` = trùng `triggers[0]`. Không tự `remove_parameter_preset`. Hỏi người dùng muốn ghi đè hay đặt trigger khác.
3. **Bẫy Token Bị Cấm (update_theme)**: Chỉ cho phép 5 token: `color.primary`, `color.primary.hover`, `color.primary.contrast`, `color.chat.user`, `color.chat.assistant`. Giải thích danh sách cho người dùng, không tìm cách vòng qua giới hạn này.
4. **Hiệu Lực Chậm**: Sau khi persona được Public trên Tenant Admin hoặc cập nhật preset/runtime, thay đổi có thể mất tới 60 giây mới phản ánh cho shopper trên storefront (do cache IntentSet). Kết quả từ `get_*` sẽ cập nhật ngay, nhưng trải nghiệm shopper thật sẽ chậm hơn.
