---
name: tap-orchestration
description: Cổng vào duy nhất cho mọi yêu cầu TAP và alias; phân loại intent, quản lý work item, safety gate, mockup review, delegation nội bộ và handoff.
user-invocable: true
---

# TAP Orchestration Gateway

Đây là entrypoint duy nhất cho yêu cầu TAP từ chat hoặc slash alias. Đọc `tap-core` trước mọi MCP operation. Không worker nào được tự nhận yêu cầu người dùng.

## 1. Triage và retirement

1. Create/resume work item trước mọi route; ghi alias, intent, scope, target/risk, `clarificationCount` (0 hoặc 1), assumptions và phase. Chỉ gateway được transition state/phase, parse approval hay kết thúc response.
2. Với xem/thêm/sửa/xóa giỏ hàng, promotion cart hoặc checkout, dừng trước MCP discovery và trả: **“TAP plugin không còn hỗ trợ capability giỏ hàng. Tôi không gọi MCP cart capability.”** Nếu request còn storefront hợp lệ, tách riêng phần đó vào work item.
3. Read-only có thể hoàn thành qua internal worker mà không cần mockup. Storefront screen/flow/chat-display hoặc UI write phải theo lifecycle mockup dưới đây.

## 2. Một lượt clarification UX

Triage dùng context và R0 discovery trước. Nếu đủ dữ liệu, ghi assumptions có nhãn rồi dựng mockup ngay. Nếu lần đầu thiếu dữ liệu material, gửi đúng một message, tối đa ba nhóm: (1) mục tiêu/người dùng, (2) screen/flow và điểm bắt đầu, (3) nội dung/brand/fixture; nêu default cho từng nhóm và tăng `clarificationCount` lên 1.

Sau câu trả lời, không hỏi UX clarification lần hai: hợp nhất câu trả lời/default, công bố assumptions và tạo mockup. Feedback như “sửa Screen 02/lane Empty state/CTA” là iteration mockup, không tăng count. Thiếu target, delete mơ hồ, payment/order thật, external disclosure hoặc permission failure vẫn BLOCKED theo `tap-core`; không được suy đoán.

## 3. Mockup, plan và delegation

Với UI route, chuyển `PLANNING/MOCKUP_REVIEW`, tạo fixture-only scenario theo [schema](references/journey-mockup-schema.md) làm contract, rồi dựng mockup trực quan từ contract đó:

- **Bắt buộc Claude Design** (source `claude-design`): tạo artifact Claude Design dạng canvas, mỗi screen là một artboard đánh số `01 · <tên>`; artboard đầu hoặc tiêu đề canvas thể hiện flow map, lanes, CTA/transition và assumptions. Giao diện bám layout storefront thật (header, chat sidebar, display panel) và token `get_theme` của tenant; dữ liệu là fixture/placeholder có nhãn.
- **Fallback chỉ khi môi trường không có Claude Design** (Claude Code CLI/VS Code): publish HTML artifact bằng tool Artifact (source `html-artifact`), load skill `artifact-design` trước, cùng chuẩn thiết kế như trên (artboard theo screen, theme tenant). Phải ghi `--fallback-reason` khi record.
- **Cấm** dùng `scripts/build_journey_mockup.py` (legacy, không dùng nữa) hoặc template HTML dựng sẵn để sinh mockup. Không gọi MCP preview/save/publish để tạo mockup. V1 single-screen vẫn hợp lệ.

Sau review, record artifact path/URL, fingerprint, schema version, screen/lane/transition IDs trong work item. Với write, tạo plan gồm objective, operations, target, backup/rollback, tests và fingerprint; chuyển `WAITING_FOR_PLAN_APPROVAL`. Chỉ **Đồng ý triển khai** gắn approval fingerprint. Không approval lại write reversible đã liệt kê; R3/không đảo ngược/payment/external/missing identifier vẫn gate riêng.

Gateway delegate worker với `workItemId`, resolved scope/capability và phase. Worker thiếu cả ba phải trả `BLOCKED`/route lại gateway, không gọi MCP write. Worker chỉ làm subtask; gateway giữ tool discovery intent, work-state, clarification, approval, parity và final response.

## 4. Handoff

Tester replay fixture trace; parity chỉ passed khi chat, display, screen/lane/transition trace khớp mockup. Gateway báo delivered behavior, data writes, evidence, state và blocker. Guard này là policy plugin có thể kiểm chứng, không phải hard authorization boundary; MCP permission và `tap-core` vẫn là enforcement cuối.
