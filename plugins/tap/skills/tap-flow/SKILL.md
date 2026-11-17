---
name: tap-flow
description: Soạn thảo, preview và xuất bản luồng tương tác form nhiều bước (interaction flow) của tenant qua MCP TAP. Dùng khi người dùng nói về flow khảo sát, form đăng ký, lead capture, wizard.
user-invocable: false
---

# TAP Flow — Internal Worker

**Delegated-by: tap-orchestration.** Không nhận request trực tiếp, không tạo/resume work item hoặc tự hỏi clarification/approval. Chỉ thực hiện subtask có `workItemId`, resolved scope/capability và phase từ gateway; thiếu context thì trả `BLOCKED`/route lại gateway trước mọi MCP write.

**Cổng ghi (plugin 3.3.0):** trước MỌI MCP write chạy `python3 scripts/work_item_state.py show <workItemId>` và kiểm `state == IMPLEMENTING` (đã qua B0–B4) và `savedRequirement.requirementId` có giá trị. Thiếu một trong hai → trả `BLOCKED` về gateway kèm output `progress <workItemId>`, không gọi tool ghi. Mọi tool ghi nháp truyền `requirementId`. Không bao giờ gọi `publish_*` (Public chỉ trên Tenant Admin web). Báo vấn đề cho người dùng theo Khung hỏi của gateway (phương án + đề xuất).

Skill quản lý vòng đời biểu mẫu tương tác nhiều bước (Interaction Flow / Custom Forms) cho tenant. Gateway tạo mockup fixture-only bằng Claude Design canvas (không dùng HTML) trước plan; MCP preview chỉ diễn ra sau approval. Plan approval theo `tap-core` thay thế gate lặp lại cho các publish reversible đã liệt kê.

## 1. Nguyên Tắc Cốt Lõi
- Đọc `tap-core` trước khi gọi bất kỳ tool nào.
- Soạn thảo flow bằng object `parsedSchema` (JSON schema chuẩn, không gửi dạng Markdown).
- Luôn kiểm tra định dạng qua `describe_interaction_flow_format` trước khi soạn thảo.

## 2. Bảng Quyết Định Luồng Thao Tác

| Nhu Cầu | Quy Trình Chuẩn | Tài Liệu Chi Tiết |
|---|---|---|
| Tạo flow mới | `describe_interaction_flow_format` $\rightarrow$ `save_interaction_flow(parsedSchema)` (không `flowId`) $\rightarrow$ Ghi nhận `flowId` được cấp $\rightarrow$ `preview_interaction_flow` (dừng ở nháp, có `requirementId`). Không `publish_interaction_flow`. | [create.md](file://skills/tap-flow/references/create.md) |
| Sửa flow đã publish | `get_interaction_flow(flowId)` (backup) $\rightarrow$ `save_interaction_flow(parsedSchema, flowId)` (lưu bản nháp mới an toàn) $\rightarrow$ `preview_interaction_flow` (dừng ở nháp). Không `publish_interaction_flow`. | [edit-published.md](file://skills/tap-flow/references/edit-published.md) |
| Xóa flow | `get_interaction_flow(flowId)` (backup) $\rightarrow$ Cổng R3 (gõ `DELETE <flowId>`) $\rightarrow$ `delete_interaction_flow(flowId)`. *(Thao tác một chiều, không hoàn tác)*. | [edit-published.md](file://skills/tap-flow/references/edit-published.md) |

## 3. Các Bẫy Nghiệp Vụ Cần Tránh
1. **Bẫy P9 (Quên truyền `flowId` khi save lần 2)**: Nếu gọi `save_interaction_flow` lần 2 mà quên truyền `flowId`, server sẽ tạo ra một flow mới hoàn toàn. Luôn lưu lại `flowId` từ lần save đầu tiên.
2. **"Save OK" chưa đồng nghĩa với "Publish được"**: `save_interaction_flow` chỉ kiểm tra tính hợp lệ cục bộ (step-local anatomy). Các ràng buộc chéo (cross-references như `VisibleIf` trỏ tới field chưa tồn tại) chỉ được kiểm tra khi Public; vì vậy tự rà cross-reference trong `parsedSchema` và chạy `preview_interaction_flow` đủ các nhánh trước khi báo xong B5.
3. **Lỗi `validation_error`** (từ save/preview, hoặc người dùng báo lại khi Public trên Tenant Admin): bóc `issues[{category, path, message}]`, sửa đúng trường, `save_interaction_flow` lại (kèm `flowId`, `requirementId`). AI không Public: dừng ở bản nháp mang `requirementId`, dẫn người dùng sang **Tenant Admin web** để Public (plugin 3.3.0, Q10).
4. **Vòng lặp Preview**: Sau khi nhận kết quả `terminal: true` từ preview run, không gửi thêm lệnh `control` nữa.

Xem cấu trúc schema mẫu tại [examples.md](file://skills/tap-flow/references/examples.md).
