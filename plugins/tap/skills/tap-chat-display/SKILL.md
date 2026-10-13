---
name: tap-chat-display
description: Điều phối trải nghiệm kết hợp chat/interaction flow với display panel của tenant TAP. Dùng khi chat làm thay đổi panel, panel cần tiếp tục hội thoại, hoặc cả hai dùng chung session values và module states.
user-invocable: false
---

# TAP Chat + Display — Internal Worker

**Delegated-by: tap-orchestration.** Không nhận request trực tiếp, không tạo/resume work item hoặc tự hỏi clarification/approval. Chỉ thực hiện subtask có `workItemId`, resolved scope/capability và phase từ gateway; thiếu context thì trả `BLOCKED`/route lại gateway trước mọi MCP write.

Dùng skill này cho một journey đi qua **chat** và **display panel**. Không dùng nó cho một panel độc lập (dùng `tap-screen`) hoặc một form/chat flow độc lập (dùng `tap-flow`). Đọc `tap-core` trước mọi thao tác. Qua `tap-orchestration`, mockup trước plan phải là artifact Claude Design có cả hai pane (canvas, không phải file HTML; không có fallback); `preview_screen` một mình không đủ.

## 1. Ranh Giới Runtime

- **Display panel** là renderer JS, được chọn bởi `conditions`, đọc context và chỉ tương tác backend qua `ctx.execute(...)`.
- **Chat / interaction flow** là form nhiều bước; nó đọc/ghi dữ liệu runtime qua `session_values`, `module_states` và form values.
- Không có liên kết trực tiếp hay được phép suy diễn giữa `screenCode` và `flowId`. Hai bề mặt phối hợp qua state đã khai báo hoặc một `operationId` có thật.

Đọc [interaction-model.md](file://skills/tap-chat-display/references/interaction-model.md) trước khi thiết kế hoặc sửa journey.

## 2. Discovery Bắt Buộc

1. `ping` và target guard. Với yêu cầu ghi, chỉ tiếp tục trên LOCAL sau xác nhận theo `tap-core`.
2. `describe_display_format`; nếu có flow, gọi thêm `describe_interaction_flow_format`.
3. Gọi `list_screens`, `list_modules`, `list_entities`, `list_session_values` để lấy binding, state và key hợp lệ trong đúng phiên.
4. Nếu panel hoặc flow gọi backend: `list_services` → `list_endpoints` → `describe_endpoint`. Không tự đặt `operationId`.
5. Nếu sửa artifact có sẵn: `get_screen(code)` và/hoặc `get_interaction_flow(flowId)` trước khi soạn thay đổi.

## 3. State Contract Trước Khi Author

Trình bày và chốt bảng sau với người dùng trước khi ghi draft:

| Vai trò | Khai báo cần có |
|---|---|
| Chat kích hoạt panel | `moduleStates` / `conditions` nào làm panel xuất hiện |
| Dữ liệu chung | key `session_values` nào panel đọc hoặc flow prefill |
| Panel tác động lại | `ctx.setSessionValue` chỉ với key `writable: true`, hoặc `ctx.execute(operationId, payload)` đã được mô tả |
| Chat tiếp tục | flow nào đọc state đó, field/nhánh nào thay đổi sau action panel |
| Kết quả kiểm chứng | trạng thái/response nào chứng minh cả chat và panel đi đúng nhánh |

Nếu có chi tiết chưa xác định, hỏi người dùng thay vì dựng link giả hoặc thêm key chưa có trong `list_session_values`.

## 4. Author, Preview, Publish

- Soạn flow bằng `parsedSchema`; tuân thủ `tap-flow` về `flowId`, validation và preview.
- Soạn panel theo `tap-screen`: không `fetch`, `window.location` hoặc `eval`; action mạng đi qua `ctx.execute`.
- Có thể lưu draft R1 sau khi báo rõ. Không publish một phía khi phía còn lại chưa preview được.
- Preview cả hai bề mặt với cùng `moduleStates`/`sessionValues`: `preview_interaction_flow` cho chat và `preview_screen` cho panel. Với panel, `shapeCheck.ok` phải là `true`, `consoleErrors` rỗng và `executeCalls` khớp state contract.
- Backup từng artifact tương ứng, rồi verify bằng `get_*`. Khi qua `tap-orchestration`, một plan approval đã ghi rõ cả hai publish reversible thay thế Gate riêng; ngoài orchestration vẫn theo Gate R2 của `tap-core`.

## 5. Phản Hồi Kết Thúc

Nêu rõ screen code, flowId (nếu có), state contract đã publish, action đã kiểm thử và phần chưa được kiểm thử. Không khẳng định storefront shopper đã nhận cache ngay lập tức.
