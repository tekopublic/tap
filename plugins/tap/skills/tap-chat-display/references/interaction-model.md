# Chat ↔ Display Interaction Model

## Mục đích

Mô hình này giúp thiết kế một journey có chat ở một bên và display panel ở bên kia mà không bịa liên kết runtime.

```text
Chat / interaction flow
  └─ session_values, module_states, form values
       ├─ conditions chọn display panel
       └─ renderer nhận context (ctx)

Display renderer
  ├─ ctx.setSessionValue(key, value) → shared state
  └─ ctx.execute(operationId, payload) → backend đã khai báo
```

`screenCode` và `flowId` là hai artifact độc lập. Liên hệ chỉ hợp lệ khi có state/key/operation được discovery trong phiên.

## Ma trận thiết kế

| Tình huống | Cơ chế hợp lệ | Discovery / kiểm thử |
|---|---|---|
| Chat làm panel xuất hiện | `conditions` khớp `moduleStates` hoặc context được server cung cấp | `list_modules`, `list_entities`, `list_screens`, `preview_screen(ctx)` |
| Chat prefill dữ liệu vào form hoặc panel | key trong `session_values` | `list_session_values`; preview với cùng `sessionValues` |
| Nút panel đổi lựa chọn dùng chung | `ctx.setSessionValue` trên key `writable: true` | `list_session_values`; preview state sau action |
| Nút panel gọi nghiệp vụ | `ctx.execute` với `operationId` đã tra cứu | `list_services` → `list_endpoints` → `describe_endpoint`; đối chiếu `executeCalls` |
| Chat thu thập dữ liệu nhiều bước | interaction-flow `parsedSchema`, tham chiếu `session_values` / `module_states` theo format server trả về | `describe_interaction_flow_format`, `preview_interaction_flow` |

## Checklist trước publish

1. Không dùng `fetch`, URL tự chế, key session tự đặt, hay `operationId` tự đoán.
2. `preview_screen`: `shapeCheck.ok == true`, không console error, action quan sát được khớp bảng thiết kế.
3. `preview_interaction_flow`: field/branch mong muốn xuất hiện với cùng state test.
4. Backup và xác nhận R2 riêng cho panel và flow.
5. Sau publish, `get_screen` và `get_interaction_flow` phải xác nhận artifact đúng trạng thái.
