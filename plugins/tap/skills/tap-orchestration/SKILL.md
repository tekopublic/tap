---
name: tap-orchestration
description: Cổng vào duy nhất cho mọi yêu cầu TAP và alias; phân loại intent, quản lý work item, safety gate, mockup review, delegation nội bộ và handoff.
user-invocable: true
---

# TAP Orchestration Gateway

Đây là entrypoint duy nhất cho yêu cầu TAP từ chat hoặc slash alias. Đọc `tap-core` trước mọi MCP operation. Không worker nào được tự nhận yêu cầu người dùng.

## 0. MCP preflight (mỗi phiên, trước triage)

1. Đọc lựa chọn đã lưu: `python3 scripts/mcp_pref.py get`.
2. Quét tool trong phiên theo hậu tố (`*ping`, `*list_screens`, `*save_screen`, `*describe_display_format`) rồi gom theo server. Server chỉ được coi là "server TAP" khi có đủ nhóm tool này.
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
3. **Chỉ đọc** (xem trạng thái, liệt kê màn, xem giỏ): `create --read-only`, trả lời qua internal worker, không cần B1–B6; kết thúc bằng `progress --short`. **Mọi yêu cầu có ghi** — screen, flow, chat-display **và config** (theme, persona, preset, runtime config, layout) — phải đi đủ B0 → B6 ở mục 2. Không có đường tắt cho thay đổi "nhỏ" (đổi màu, sửa chữ).

## 2. Quy trình cứng B0 → B6 (mọi yêu cầu có ghi)

Thứ tự bắt buộc, không đảo, không bỏ bước. Trong B0–B4 chỉ MCP read-only (ngoại lệ duy nhất: `save_requirement` ở B3); cấm code chi tiết và thay đổi hiện trạng thật. Ghi nháp chỉ ở B5. AI **không bao giờ** gọi `publish_*` — Public do người có quyền làm trên Tenant Admin web.

### Cổng cứng (`scripts/work_item_state.py`, script từ chối nếu sai thứ tự)

| # | Bước | state / phase | Lệnh bắt buộc | Điều kiện qua cổng |
|---|---|---|---|---|
| B0 | Tiếp nhận | PLANNING / `INTENT_ANALYSIS` | `create` (sửa Requirement cũ: `--requirement-id --requirement-status --baseline-table-file --retired-ids` từ `get_requirement`) | có work item |
| B1 | Làm rõ | `INTENT_ANALYSIS` | `record-clarification --questions --tenant-url` | 1-3 câu UX theo khung hỏi + địa chỉ web (hoặc `skipped:<lý do>`) |
| B1.5 | Chạy thử web | `INTENT_ANALYSIS` | `record-live-probe --file` | `done` hoặc `skipped` kèm lý do |
| B2 | Đề xuất + mockup | `MOCKUP_REVIEW` | `record-proposal` → `record-mockup` → `approve-mockup --quote` | người dùng nhắn đồng ý Mockup |
| B3 | Bảng 9 cột + lưu | `REQUIREMENT_CONFIRMATION` | `record-requirement` → `confirm-requirement` → MCP `save_requirement` → `record-saved-requirement` | người dùng **Xác nhận** + có `requirementId` |
| B4 | Chốt plan | `PLAN_FINALIZATION` → `WAITING_FOR_PLAN_APPROVAL` | `approve-plan --fingerprint <fingerprint bảng>` → `transition IMPLEMENTING` | người dùng duyệt plan |
| B5 | Triển khai | `IMPLEMENTING` | ghi nháp mang `requirementId` → MCP `declare_requirement_changes` → `record-change`; `record-review-link` → `transition TESTING` | ≥1 thay đổi đã khai + link review |
| B6 | Kiểm thử | `TESTING` → `COMPLETED` | `record-parity --row-ids <mọi ID>` → `transition COMPLETED` | parity passed phủ mọi dòng |

Đổi đề xuất, mockup hoặc bảng sau khi đã duyệt làm mất hiệu lực mọi bước phía sau (script tự đánh `Bị mất hiệu lực`, phải làm lại theo thứ tự). Không nhảy thẳng `PLANNING → IMPLEMENTING`. Cuối mỗi bước in `progress --short` (1 dòng: bước hiện tại — việc tiếp theo).

### B0 — Tiếp nhận

- Tạo work item. Nếu người dùng muốn sửa/tiếp tục một Requirement: `list_requirements` / `get_requirement` trước, truyền `requirementId`, trạng thái và bảng hiện tại vào `create` để giữ nguyên ID dòng.

### B1 — Làm rõ yêu cầu, hỏi địa chỉ web

- Kiểm tra hiện trạng thật bằng MCP read-only (`list_screens`, `get_screen`, `list_services`/`list_endpoints`, `list_state_transitions`, `get_theme`...), kèm R0 discovery.
- Hỏi người dùng tối thiểu 1 và tối đa 3 câu UX, gộp trong đúng một message, mỗi câu theo **Khung hỏi** (mục 2b). Chỉ một lượt: sau câu trả lời không hỏi UX lần hai, hợp nhất câu trả lời/đề xuất và công bố assumptions.
- **Luôn hỏi thêm 1 câu bắt buộc** (không tính vào trần 3 câu, cùng message): "Địa chỉ web storefront đang chạy cho tenant này là gì? AI sẽ dùng địa chỉ đó để tự chạy các yêu cầu (dạng use case) và gộp kết quả thực tế vào phân tích trước khi vẽ mockup." Phương án: A. địa chỉ đề xuất từ `tap-core/references/targets.md` theo tenant/server đang dùng (Đề xuất); B. địa chỉ khác do người dùng nhập; C. bỏ qua (mockup sẽ ghi rõ chưa đối chiếu web thật).
- Ghi bằng `record-clarification --tenant-url <url | skipped:<lý do>>` (`clarificationCount` = 1). Thiếu target, delete mơ hồ, payment/order thật, external disclosure hoặc permission failure vẫn BLOCKED theo `tap-core`, không suy đoán.

### B1.5 — Chạy thử use case trên web tenant

1. Từ yêu cầu đã làm rõ, sinh danh sách use case (câu chat mẫu, CTA cần bấm, kỳ vọng). In danh sách ra chat rồi chạy luôn — không chờ duyệt.
2. Dùng công cụ trình duyệt có trong môi trường (Claude in Chrome, computer use, Playwright MCP — tự phát hiện) mở địa chỉ web, chạy từng use case: gõ chat, bấm CTA, ghi lại chat panel + display panel thực tế, chụp màn khi có thể.
3. Chỉ đọc/thử: **cấm** đặt hàng, thanh toán, gửi form thật, đăng nhập bằng tài khoản thật của người dùng. Gặp bước có tác dụng phụ thì dừng use case đó, ghi `not-run`.
4. Ghi `record-live-probe --file` với JSON `{"status":"done","tool":"...","useCases":[{"id","input","expected","actual","result":"pass|diff|not-run","note"}]}`.
5. Không có công cụ trình duyệt hoặc người dùng chọn bỏ qua: `{"status":"skipped","reason":"..."}`; vẫn sang B2 nhưng đề xuất và mockup phải ghi "chưa đối chiếu web thật".
6. Cần chạy lại probe sau này: `set-phase INTENT_ANALYSIS` (không mở lượt hỏi thứ 2), mọi bước sau mất hiệu lực.

### B2 — Đề xuất + Claude Design (sau B1.5)

- Chuyển `MOCKUP_REVIEW`. **In ra chat bản đề xuất trước**, gộp ba nguồn: hiện trạng MCP (B1), kết quả live probe (B1.5), câu trả lời người dùng. Cấu trúc: *Hiện trạng thật* (dẫn use case khớp/lệch) / *Khoảng trống* / *Thay đổi đề xuất* (mỗi điểm có phương án + đề xuất theo Khung hỏi nếu còn lựa chọn). Ghi bằng `record-proposal --file`.
- Sau đó tạo fixture-only scenario theo [schema](references/journey-mockup-schema.md) làm contract, rồi dựng mockup từ contract đó:
- **Đầu ra DUY NHẤT hợp lệ: Claude Design (canvas)** (source `claude-design`), loại artifact "Claude Design" trong chat, KHÔNG phải file `.html`/"Code · HTML". Bám layout storefront thật (header, chat sidebar, display panel) và token `get_theme`; dữ liệu fixture có nhãn.
- **Journey map đầy đủ** (khung Flow map đầu canvas): mọi bước, đường đi, tình huống (happy / empty / error-fallback / alternate); mỗi màn đánh dấu CÓ SẴN (giữ nguyên) / SỬA / LÀM MỚI. Màn CÓ SẴN dẫn bằng chứng từ live probe.
- **Mockup chi tiết từng màn:** mỗi artboard `01 · tên`, `02 · tên`… có đủ **chat panel + display panel**, thể hiện tương tác qua lại giữa hai bên; số thứ tự khớp Journey map. Màn có sẵn phải đối chiếu dữ liệu thật qua MCP (`list_screens`/`get_screen`), ghi `mcpRef` vào contract; màn mới ghi chú rõ "MỚI".
- **Thay đổi config không có giao diện** (persona, preset, runtime config, theme): vẫn Claude Design, vẽ các màn chat/display chịu ảnh hưởng ở dạng **trước – sau** (vd cùng một đoạn chat với giọng persona cũ và mới; chip preset trước/sau).
- **Sơ đồ nối màn hình:** mỗi `transition` là một mũi tên có hướng, nhãn `T<số bước> · "<ctaLabel>"` (T1, T2… theo thứ tự `flowMap.transitions`); happy-path nét liền xanh lá, empty-state nét đứt vàng, error-fallback nét đứt đỏ nối về screen fallback, alternate nét liền xám/tím; có legend. Màn đã có và không sửa vẽ khung mờ "giữ nguyên", vẫn nối mũi tên. Số mũi tên = số `transitions`; nếu thiếu đối tượng nối chuẩn thì dùng đường kẻ + đầu mũi tên, vẫn đủ màu, nhãn, số bước.
- **Không chờ người dùng yêu cầu:** tạo thẳng Claude Design ngay sau đề xuất, không tạo HTML/Markdown/ảnh rồi hỏi lại. Không có fallback HTML. Nếu môi trường không tạo được Claude Design (Claude Code CLI/VS Code), dừng `BLOCKED` và báo "cần chạy trong Claude Desktop/claude.ai để tạo Claude Design canvas". Cấm `scripts/build_journey_mockup.py` (legacy), cấm MCP preview/save/publish để làm mockup.
- Mọi yêu cầu sửa của người dùng ("sửa Screen 02/lane Empty state/CTA") là iteration: cập nhật mockup, `record-mockup` lại, không tăng clarificationCount, lặp đến khi người dùng nhắn đồng ý Mockup, rồi `approve-mockup --quote "<nguyên văn>"`.

### B3 — Bảng Requirement 9 cột + lưu qua MCP

Chuyển `REQUIREMENT_CONFIRMATION`, tổng hợp toàn bộ chat + đề xuất + live probe + mockup đã chốt thành bảng markdown, **in thẳng ra ô chat** (không chỉ ghi file/dẫn link), rồi lưu cùng nội dung bằng `record-requirement --table-file`:

- **9 cột đúng thứ tự:** `ID | Scope | Trigger | Điều kiện trước | Chat panel | Display panel | Hệ thống | Không được làm | Pass rate` (key khi lưu: `id, scope, trigger, precondition, chatPanel, displayPanel, system, mustNot, passRate`). Ô không để trống.
- **ID:** `<MODULE>-<FAMILY>-<nnn><X>` (vd `CART-DEL-017C`). ID ổn định từ lần lưu đầu: sửa ô/đổi thứ tự giữ ID; usecase mới lấy số lớn nhất (tính cả ID đã xoá) + 1; case mới lấy chữ cái kế tiếp của usecase; ID đã xoá không dùng lại. Script kiểm, sai thì sửa bảng.
- **Scope:** bắt đầu bằng `issue <số>`, `Change`, `Proposed` hoặc `Deferred post-MVP` (viết `issue 319`, không `#319`).
- **Trigger:** bắt đầu bằng channel tag `[Chat]`, `[Chat chip]`, `[Chat click]`, `[Display click]`, `[System]`, kèm `(T<n>)` của transition (mọi transition trong mockup phải có dòng).
- **Điều kiện trước / Hệ thống:** điền từ hiện trạng thật (MCP + live probe): trạng thái/dữ liệu cần có; lưu/đọc, đổi state, thứ mang sang bước sau. **Chat panel / Display panel** đúng như mockup. **Không được làm** = các điều cấm.
- **Pass rate:** `100%` hoặc `80%`; `80%` chỉ cho Trigger `[Chat]` không gắn chip (AI phải phán đoán: hỏi lại, nhiều yêu cầu, tư vấn).
- Dưới bảng: assumptions còn hiệu lực, phần "giữ nguyên", điểm còn chưa rõ (theo Khung hỏi); kết thúc bằng đúng một câu: "Bảng trên đã đúng là Yêu cầu (requirement) và Mockup bạn muốn chưa? Trả lời **Xác nhận** để tiếp tục, hoặc nêu dòng cần sửa."
- Người dùng sửa bảng: sửa, in lại, `record-requirement` lại, hỏi xác nhận lại (đổi UI/flow thì quay B2). Chỉ khi có xác nhận rõ ràng mới `confirm-requirement --fingerprint --quote`. Im lặng, "mockup đẹp" ở B2 hay approval cũ không thay thế bước này.
- **Lưu:** ngay sau `confirm-requirement`, lấy `saveRequirementPayload` trong output script và gọi MCP `save_requirement` với `title`, `requestSummary`, `originalRequest`, `assumptions`, `requirementTable` (9 key), `mockupContract`, `mockupCanvasUrl`, `idempotencyKey`, `fingerprint`; có `requirementId` (sửa bản draft/implementing) hoặc `supersedesId` (sửa bản đã Public) thì truyền đúng như payload. Thành công → `record-saved-requirement --requirement-id <id trả về> --fingerprint <fp>`.
- `save_requirement` lỗi (`ok:false`, permission, tool không có) → BLOCKED theo `tap-core` + báo lỗi mục 0b, theo Khung hỏi. **Không** lưu file local thay thế, không đi tiếp B4.

### B4 — Chốt plan

`set-phase PLAN_FINALIZATION`. Tạo plan gồm objective, operations, target, backup/rollback, tests, `requirementId` và fingerprint bảng; chuyển `WAITING_FOR_PLAN_APPROVAL`. Chỉ **Đồng ý triển khai** mới `approve-plan --fingerprint <fingerprint bảng> --quote` rồi `transition IMPLEMENTING`. Không approval lại write reversible đã liệt kê; R3/không đảo ngược/payment/external/missing identifier vẫn gate riêng.

### B5 — Triển khai vào bản nháp

- Mọi tool ghi nháp mang `requirementId`. Bản đang chạy không đổi.
- Sau mỗi artifact ghi xong: gọi MCP `declare_requirement_changes` (artifact + lý do + ID dòng bảng), rồi `record-change --artifact --row-ids --reason`.
- Lấy link review do hệ thống tạo (`get_requirement`), `record-review-link --url`, đưa link cho người dùng, rồi `transition TESTING`.

### B6 — Kiểm thử

Tester replay fixture trace; parity chỉ passed khi chat, display, screen/lane/transition trace khớp mockup và **từng dòng** bảng 9 cột đã lưu (kể cả cột Không được làm). `record-parity --status --evidence --row-ids <mọi ID đã kiểm>` rồi `transition COMPLETED`. Gateway báo delivered behavior, data writes, evidence, state và blocker, rồi dẫn người dùng sang **Tenant Admin web** để Public (AI không Public).

## 2a. Phát hiện sai bước

Áp dụng khi: script trả `ok:false` (exit 2), AI định nhảy bước, người dùng đòi bỏ bước ("sửa nhanh luôn, khỏi mockup"), sửa đề xuất/mockup/bảng sau khi đã duyệt, hoặc tool MCP lỗi giữa chừng.

1. **Dừng ngay**, không làm tiếp hành động đang định làm.
2. Chạy `progress <workId>` (hoặc lấy trường `progress` trong JSON lỗi) và **in nguyên bảng tiến trình** ra chat — đủ 8 bước, trạng thái `Xong / Đang ở đây / Chưa làm / Bị mất hiệu lực`. Không chỉ dẫn file/link.
3. Nói một câu: đang ở bước nào (`currentStep`), sai ở đâu (`error`), thiếu cổng nào (`missingGates`).
4. Theo Khung hỏi: nêu phương án (vd A. quay về làm đúng bước `currentStep` — Đề xuất; B. huỷ yêu cầu), rồi quay về đúng bước đó và làm lại theo thứ tự. Người dùng đòi bỏ bước: giải thích ngắn mọi yêu cầu có ghi phải đi đủ B0–B6, không có ngoại lệ.

## 2b. Khung hỏi / nêu vấn đề

Mọi chỗ AI hỏi hoặc báo vấn đề (câu hỏi B1 kể cả câu địa chỉ web, lệch ở live probe, điểm chưa rõ trong mockup/bảng, lỗi MCP/permission, bị chặn do sai bước, xung đột với Requirement đã Public) — **không bao giờ chỉ nêu vấn đề hoặc hỏi trống**:

- **Vấn đề / câu hỏi:** 1 câu.
- **Phương án:** 2–4 phương án A, B, C…, mỗi phương án 1 dòng giải thích hệ quả (UX, dữ liệu, rủi ro, công sức).
- **Đề xuất:** 1 phương án, ghi "(Đề xuất)" + lý do ngắn dựa trên hiện trạng thật (MCP, live probe, theme...).
- Người dùng trả lời bằng chữ cái; ở B1 không chọn thì dùng phương án đề xuất và ghi vào assumptions.
- Chỉ có một hướng hợp lệ (vd thiếu quyền chỉ có thể xin quyền): vẫn nêu hướng đó + việc cụ thể người dùng cần làm.
- Câu hỏi B1 ghi vào script dạng `{"q","options":[...],"recommended","reason"}`; thiếu thì script từ chối.

## 3. Delegation

Gateway delegate worker với `workItemId`, `requirementId`, resolved scope/capability và phase; với write thì gateway chỉ delegate khi work item đang `IMPLEMENTING` (đã qua B4) và truyền kèm `requirementFingerprint`. Worker thiếu `workItemId`/`requirementId`/scope/phase phải trả `BLOCKED`/route lại gateway, không gọi MCP write. Worker chỉ làm subtask; gateway giữ tool discovery intent, work-state, clarification, approval, parity và final response.

## 4. Handoff

Gateway báo delivered behavior, data writes, `requirementId`, link review, evidence, state và blocker, kèm `progress` cuối. Guard này là policy plugin có thể kiểm chứng, không phải hard authorization boundary; MCP permission và `tap-core` vẫn là enforcement cuối.
