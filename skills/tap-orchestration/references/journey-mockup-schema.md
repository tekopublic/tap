# Journey Mockup Scenario v2

Mọi scenario là **fixture-only**: cấm PII, secret, MCP preview URL và payload upstream. `title`, `chat`, `display`, `transitions` của v1 vẫn hợp lệ cho journey một màn hình. V2 dùng khi có `screens` hoặc `flowMap`.

## V2 contract

- `fixtures` bắt buộc và có nhãn fixture-only.
- `assumptions[]` bắt buộc nếu model tự suy luận: `{ "id": "A1", "text": "…", "userVisible": true }`.
- `screens[]` bắt buộc khi nhiều màn hình/transition: `{ id: "screen-01", number: 1, name, goal, laneIds, chat, display, states? }`. ID phải `screen-01`… và number liên tiếp từ 1.
- `flowMap.startScreenId` trỏ chính xác một screen.
- `flowMap.lanes[]`: `{ id, label, kind, description }`, kind là `happy-path`, `empty-state`, `error-fallback`, hoặc `alternate`.
- `flowMap.transitions[]`: `{ id, fromScreenId, toScreenId, laneId, trigger, ctaLabel, expectedResult, guard?, fallback? }`; fallback, nếu có, cũng là screen ID.

Renderer hiển thị flow map trước canvas, index Screen 01…, lane legend/filter, CTA text và timeline có `screenId`, `laneId`, `transitionId`. Interactions chỉ đổi fixture state trong browser.

## Ví dụ v2: 4 screens, 3 lanes

```json
{
  "schemaVersion": 2,
  "title": "Product discovery",
  "fixtures": {"label": "fixture-only", "products": ["Laptop mẫu"]},
  "assumptions": [{"id": "A1", "text": "Dùng catalogue mẫu", "userVisible": true}],
  "screens": [
    {"id": "screen-01", "number": 1, "name": "Nhập nhu cầu", "goal": "Nhận nhu cầu", "laneIds": ["happy"], "chat": {"messages": [{"role": "assistant", "text": "Bạn cần gì?"}]}, "display": {"title": "Tìm kiếm", "cards": []}},
    {"id": "screen-02", "number": 2, "name": "Kết quả sản phẩm", "goal": "Chọn sản phẩm", "laneIds": ["happy", "empty"], "chat": {"messages": []}, "display": {"title": "Kết quả", "cards": [{"title": "Laptop mẫu", "price": "20.000.000đ", "meta": "Fixture"}]}},
    {"id": "screen-03", "number": 3, "name": "Chi tiết", "goal": "Xem chi tiết", "laneIds": ["happy", "error"], "chat": {"messages": []}, "display": {"title": "Chi tiết", "cards": []}},
    {"id": "screen-04", "number": 4, "name": "Gợi ý thay thế", "goal": "Phục hồi", "laneIds": ["empty"], "chat": {"messages": []}, "display": {"title": "Gợi ý", "cards": []}}
  ],
  "flowMap": {"startScreenId": "screen-01", "lanes": [{"id": "happy", "label": "Happy path", "kind": "happy-path", "description": "Luồng chính"}, {"id": "empty", "label": "Empty state", "kind": "empty-state", "description": "Không có kết quả"}, {"id": "error", "label": "Error/Fallback", "kind": "error-fallback", "description": "Khôi phục lỗi"}], "transitions": [{"id": "search", "fromScreenId": "screen-01", "toScreenId": "screen-02", "laneId": "happy", "trigger": "submit", "ctaLabel": "Tìm kiếm", "expectedResult": "Hiện kết quả"}, {"id": "detail", "fromScreenId": "screen-02", "toScreenId": "screen-03", "laneId": "happy", "trigger": "click", "ctaLabel": "Xem chi tiết", "expectedResult": "Hiện chi tiết"}, {"id": "empty", "fromScreenId": "screen-02", "toScreenId": "screen-04", "laneId": "empty", "trigger": "no-results", "ctaLabel": "No results", "expectedResult": "Hiện gợi ý"}, {"id": "retry", "fromScreenId": "screen-03", "toScreenId": "screen-02", "laneId": "error", "trigger": "retry", "ctaLabel": "Thử lại", "expectedResult": "Quay lại kết quả", "fallback": "screen-02"}]}
}
```
