---
name: tap-orchestration
description: Cổng vào duy nhất cho mọi yêu cầu TAP và alias; phân loại intent, quản lý work item, safety gate, mockup review, delegation nội bộ và handoff.
user-invocable: true
---

# TAP Orchestration Gateway

Đây là entrypoint duy nhất cho yêu cầu TAP từ chat hoặc slash alias. Đọc `tap-core` trước mọi MCP operation. Không worker nào được tự nhận yêu cầu người dùng.

## 0. MCP preflight (mỗi phiên, trước triage)

1. Đọc lựa chọn đã lưu: `python3 scripts/mcp_pref.py get`.
2. Quét tool trong phiên theo hậu tố (`*ping`, `*list_screens`, `*publish_screen`, `*describe_display_format`) rồi gom theo server. Server chỉ được coi là "server TAP" khi có đủ nhóm tool này.
3. Quyết định:
   - **Không có server TAP nào**: dừng ở `BLOCKED` và báo chủ động: "Chưa kết nối MCP TAP. Vào Connectors → Connect (hoặc Reconnect nếu hiện 'Server not responding'/'Sign-in expired'), rồi nhắn lại." Liệt kê các connector có tên gần giống nhưng chưa kết nối nếu thấy. Không gọi tool, không đoán.
   - **Có đúng 1 server TAP**: dùng luôn, lưu bằng `mcp_pref.py set <server>`.
   - **Có nhiều server TAP và chưa có lựa chọn đã lưu (hoặc server đã lưu không còn trong phiên)**: hỏi người dùng chọn một, nêu môi trường LOCAL/PROD của từng server theo `tap-core/references/targets.md`, rồi lưu bằng `mcp_pref.py set`.
   - **Đã lưu và server còn trong phiên**: dùng luôn, không hỏi lại.
4. Người dùng nói "đổi MCP" / "dùng <tên server>" ở bất kỳ lúc nào: chạy lại `mcp_pref.py set`. `/tap:status` hiển thị server đang dùng và các server TAP khác khả dụng.
5. Ghi `server` đã chọn vào work item và truyền cho mọi worker; worker không tự chọn server khác.

## 0b. Báo lỗi cho team TAP

Khi chuyển `BLOCKED`, hoặc gặp lỗi không tự xử lý được (thiếu kết nối/quyền/API/config, `ok:false` nội bộ, không tạo được Claude Design): dừng, rồi theo [error-report.md](../tap-core/references/error-report.md) chạy `scripts/build_error_report.py` và in nguyên văn kết quả: giải thích tiếng Việt dễ hiểu, khung báo cáo để copy, hướng dẫn dán vào nhóm Google Chat TAP. Không gửi mạng, không tự gửi thay người dùng, không đưa secret/PII/nội dung chat khách. Nếu đã có thao tác ghi dở dang, nêu rõ ở mục "Đã ghi gì lên hệ thống?" kèm đường dẫn backup.

## 1. Triage và retirement

1. Create/resume work item trước mọi route; ghi alias, intent, scope, target/risk, `clarificationCount` (0 hoặc 1), assumptions và phase. Chỉ gateway được transition state/phase, parse approval hay kết thúc response.
2. Không có skill riêng cho giỏ hàng: xem/thêm/sửa/xóa giỏ, promotion và checkout là yêu cầu storefront bình thường, được xử lý bằng các skill sẵn có. Discover bằng MCP trước (`list_services`/`list_endpoints`/`describe_endpoint`, `list_state_transitions`/`describe_state`, `list_session_values`, `get_screen`) rồi route: panel/màn hình giỏ hàng → `tap-screen`; luồng nhiều bước (form, checkout, chat flow) → `tap-flow`; journey chat + display → `tap-chat-display`; persona/runtime config liên quan → `tap-config`; an toàn, risk R0-R3, backup, gate → `tap-core`. Xem giỏ (đọc) là R0, không cần plan approval; write reversible theo plan approval; tạo order/thanh toán thật vẫn qua Gate `G` riêng. Nguyên tắc chung: **không từ chối** một khả năng chỉ vì skill chưa nhắc tới; chỉ khi discovery xác nhận thiếu hoặc lỗi thì báo rõ lỗi ở đâu, nguyên nhân, cách khắc phục và hiển thị báo cáo theo mục 0b. Không bịa dữ liệu giỏ hàng.
3. Read-only có thể hoàn thành qua internal worker mà không cần mockup. Storefront screen/flow/chat-display hoặc UI write phải theo quy trình cứng B1 → B2 → B3 ở mục 2.

## 2. Quy trình cứng B1 → B2 → B3 (mọi yêu cầu storefront screen/flow/chat-display có ghi)

Thứ tự bắt buộc, không đảo, không bỏ bước. Chỉ khi xong B3 mới được sửa code, `save_screen`/`publish_screen`, lưu trữ hay bất kỳ thao tác ghi nào. Trong B1-B3 chỉ MCP read-only; cấm code chi tiết và thay đổi hiện trạng thật.

### Cổng cứng (`scripts/work_item_state.py`, gọi đúng thời điểm, script từ chối nếu sai thứ tự)

| Bước | Phase | Lệnh bắt buộc | Điều kiện qua cổng |
|---|---|---|---|
| B1 | `INTENT_ANALYSIS` | `record-clarification --questions` | 1-3 câu, mỗi câu kèm `default` |
| B2 | `MOCKUP_REVIEW` | `record-mockup` → `approve-mockup --quote` | người dùng nhắn đồng ý Mockup |
| B3 | `REQUIREMENT_CONFIRMATION` | `record-requirement --table-file` → `confirm-requirement --fingerprint --quote` | người dùng xác nhận bảng |
| Sau | `PLAN_FINALIZATION` | `transition WAITING_FOR_PLAN_APPROVAL` → `approve-plan` | requirement đã xác nhận khớp fingerprint |

Đổi mockup hoặc bảng sau khi đã duyệt làm mất hiệu lực mọi xác nhận phía sau (quay lại bước đó). Không nhảy thẳng `PLANNING → IMPLEMENTING`.

### B1 — Tiếp nhận, kiểm tra thực tế, hỏi lại

- Tạo work item, rồi kiểm tra hiện trạng thật bằng MCP read-only (`list_screens`, `get_screen`, `list_services`/`list_endpoints`, `list_state_transitions`, `get_theme`...), kèm R0 discovery.
- Hỏi người dùng tối thiểu 1 và tối đa 3 câu, gộp trong đúng một message, mỗi câu nêu đáp án mặc định đề xuất. Chỉ một lượt: sau câu trả lời không hỏi UX lần hai, hợp nhất câu trả lời/default và công bố assumptions.
- Ghi bằng `record-clarification` (`clarificationCount` = 1). Thiếu target, delete mơ hồ, payment/order thật, external disclosure hoặc permission failure vẫn BLOCKED theo `tap-core`, không suy đoán.

### B2 — Claude Design (sau khi có trả lời B1)

Chuyển `MOCKUP_REVIEW`, tạo fixture-only scenario theo [schema](references/journey-mockup-schema.md) làm contract, rồi dựng mockup từ contract đó:

- **Đầu ra DUY NHẤT hợp lệ: Claude Design (canvas)** (source `claude-design`), loại artifact "Claude Design" trong chat, KHÔNG phải file `.html`/"Code · HTML". Bám layout storefront thật (header, chat sidebar, display panel) và token `get_theme`; dữ liệu fixture có nhãn.
- **Journey map đầy đủ** (khung Flow map đầu canvas): mọi bước, đường đi, tình huống (happy / empty / error-fallback / alternate); mỗi màn đánh dấu CÓ SẴN (giữ nguyên) / SỬA / LÀM MỚI.
- **Mockup chi tiết từng màn:** mỗi artboard `01 · tên`, `02 · tên`… có đủ **chat panel + display panel**, thể hiện tương tác qua lại giữa hai bên; số thứ tự khớp Journey map. Màn có sẵn phải đối chiếu dữ liệu thật qua MCP (`list_screens`/`get_screen`), ghi `mcpRef` vào contract; màn mới ghi chú rõ "MỚI".
- **Sơ đồ nối màn hình:** mỗi `transition` là một mũi tên có hướng, nhãn `T<số bước> · "<ctaLabel>"` (T1, T2… theo thứ tự `flowMap.transitions`); happy-path nét liền xanh lá, empty-state nét đứt vàng, error-fallback nét đứt đỏ nối về screen fallback, alternate nét liền xám/tím; có legend. Màn đã có và không sửa vẽ khung mờ "giữ nguyên", vẫn nối mũi tên. Số mũi tên = số `transitions`; nếu thiếu đối tượng nối chuẩn thì dùng đường kẻ + đầu mũi tên, vẫn đủ màu, nhãn, số bước.
- **Không chờ người dùng yêu cầu:** tạo thẳng Claude Design ngay lượt đầu của B2, không tạo HTML/Markdown/ảnh rồi hỏi lại. Không có fallback HTML. Nếu môi trường không tạo được Claude Design (Claude Code CLI/VS Code), dừng `BLOCKED` và báo "cần chạy trong Claude Desktop/claude.ai để tạo Claude Design canvas". Cấm `scripts/build_journey_mockup.py` (legacy), cấm MCP preview/save/publish để làm mockup.
- Mọi yêu cầu sửa của người dùng ("sửa Screen 02/lane Empty state/CTA") là iteration: cập nhật mockup, `record-mockup` lại, không tăng clarificationCount, lặp đến khi người dùng nhắn đồng ý Mockup, rồi `approve-mockup --quote "<nguyên văn>"`.

### B3 — Bảng Requirement (sau khi người dùng đồng ý Mockup)

Chuyển `REQUIREMENT_CONFIRMATION`, tổng hợp toàn bộ chat + mockup đã chốt thành bảng markdown, **in thẳng ra ô chat** (không chỉ ghi file/dẫn link), rồi lưu cùng nội dung bằng `record-requirement`:

- **6 cột đúng thứ tự:** `Trigger | Precondition | Chat panel | Display panel | System | Must not`. Trigger ghi `[Chat] "câu mẫu"` hoặc `[Bấm · Display] <CTA>` kèm `(T<n>)` của transition. Precondition = trạng thái/dữ liệu cần có. Chat/Display = đúng như mockup. System = lưu/đọc, đổi state, thứ mang sang bước sau. Must not = các điều cấm.
- Một dòng = một cặp (trigger, precondition); cùng trigger khác precondition tách dòng riêng. Phủ happy path, mọi lane empty/error/alternate và **mọi transition** (script từ chối nếu thiếu `T<n>`). Chỉ ghi điều có trong chat/mockup; điều model suy luận gắn `(assumption Ax)`; không thêm hành vi chưa ai duyệt.
- Dưới bảng: assumptions còn hiệu lực, phần "giữ nguyên", điểm mockup chưa rõ; kết thúc bằng đúng một câu: "Bảng trên đã đúng là Yêu cầu (requirement) và Mockup bạn muốn chưa? Trả lời **Xác nhận** để tiếp tục, hoặc nêu dòng cần sửa."
- Người dùng sửa bảng: sửa, in lại, `record-requirement` lại, hỏi xác nhận lại (đổi UI/flow thì quay B2). Chỉ khi có xác nhận rõ ràng mới `confirm-requirement --fingerprint --quote`. Im lặng, "mockup đẹp" ở B2 hay approval cũ không thay thế bước này.

Sau B3: record artifact path/URL, fingerprint, schema version, screen/lane/transition IDs trong work item. Với write, tạo plan gồm objective, operations, target, backup/rollback, tests và fingerprint; chuyển `WAITING_FOR_PLAN_APPROVAL`. Chỉ **Đồng ý triển khai** gắn approval fingerprint. Không approval lại write reversible đã liệt kê; R3/không đảo ngược/payment/external/missing identifier vẫn gate riêng.

## 3. Delegation

Gateway delegate worker với `workItemId`, resolved scope/capability và phase; với write thì gateway chỉ delegate sau B3 và truyền kèm `requirementFingerprint` đã xác nhận. Worker thiếu `workItemId`/scope/phase phải trả `BLOCKED`/route lại gateway, không gọi MCP write. Worker chỉ làm subtask; gateway giữ tool discovery intent, work-state, clarification, approval, parity và final response.

## 4. Handoff

Tester replay fixture trace; parity chỉ passed khi chat, display, screen/lane/transition trace khớp mockup và từng dòng bảng requirement đã xác nhận (kể cả cột Must not). Gateway báo delivered behavior, data writes, evidence, state và blocker. Guard này là policy plugin có thể kiểm chứng, không phải hard authorization boundary; MCP permission và `tap-core` vẫn là enforcement cuối.
