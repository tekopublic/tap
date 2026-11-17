# TAP Tenant Ops — Claude App và ChatGPT App

Playbook an toàn và điều phối quy trình vận hành cấu hình tenant qua MCP Server của TAP (`phongvu-tap-mcp` hoặc `agentic-storefront-mcp` chạy local). Một bộ skills dùng chung cho Claude App/Cowork và ChatGPT App; host adapter/manifest tách riêng.

## Yêu cầu tiên quyết
- Claude: MCP connector TAP đã được cấu hình trong `~/.claude.json` (user-level) hoặc trên môi trường Anthropic Cowork.
- ChatGPT: cài plugin `tap` từ local marketplace. Package khai báo `agentic-storefront-mcp` qua portable `mcp.json`, nên skills và 59 TAP tools được nạp trong cùng Work chat.
- Plugin không tự chứa thông tin bí mật, OAuth credential hay endpoint public; skills phân giải trực tiếp tools MCP đã được host kết nối trong phiên.
- Hướng dẫn cài từng bước cho ChatGPT: [`../doc/tap-chatgpt-local-install.md`](../doc/tap-chatgpt-local-install.md).

## Cổng vào duy nhất

Mọi yêu cầu TAP phải đi qua `tap-orchestration`. Các slash command bên dưới chỉ là alias tương thích: chúng chuyển nguyên yêu cầu và ngữ cảnh alias vào gateway, không gọi skill nghiệp vụ hay MCP tool trực tiếp. `tap-core` và các skill nghiệp vụ là dependency nội bộ của gateway.

Giỏ hàng/promotion/checkout được hỗ trợ bằng các skill sẵn có (`tap-screen`, `tap-flow`, `tap-chat-display`, `tap-core`) sau khi discover capability qua MCP, không có skill riêng. Gặp lỗi thì gateway báo rõ lỗi ở đâu, nguyên nhân, cách khắc phục và kèm báo cáo gửi team TAP.

## Tính năng chính
- Agent orchestration gateway: Leader tạo/resume work item, phân loại intent; mọi yêu cầu có ghi (kể cả config) đi quy trình cứng B0 tiếp nhận → B1 làm rõ (1-3 câu có phương án + đề xuất, kèm câu địa chỉ web tenant) → B1.5 chạy thử use case trên web tenant → B2 đề xuất + mockup Claude Design → B2.5 rà soát độ phủ (tách yêu cầu thành R1..Rn, hỏi tối đa 5 câu) → B3 bảng Requirement 9 cột theo `usecase-rules.md` + ma trận phủ + rà độc lập bằng sub-agent, người dùng Xác nhận, lưu qua MCP `save_requirement` → B4 chốt plan → B5 ghi nháp mang `requirementId` + `declare_requirement_changes` → B6 parity theo từng dòng; ép bằng state machine `work_item_state.py` (sai bước → in bảng `progress`, quay về đúng bước). AI không Public.
- Quản lý màn hình (Screen / Display): Tạo màn hình mới, sửa màn hình live an toàn không gây gián đoạn shopper, xóa màn hình có backup.
- Interaction Flow: Quản lý biểu mẫu nhiều bước, preview với session values trước khi publish.
- Cấu hình nâng cao: Tinh chỉnh persona (giọng nói, brand), parameter presets chip, runtime config và 5 tokens màu sắc của theme.
- Báo lỗi: khi gặp sự cố, plugin giải thích bằng tiếng Việt và đưa sẵn nội dung để copy gửi nhóm Google Chat TAP (không tự gửi, đã che dữ liệu nhạy cảm).
- Cổng an toàn (Safety Gates): Kiểm tra kết nối MCP TAP khi bắt đầu, người dùng chọn MCP một lần (được lưu lại), ghi lên PROD/LOCAL đều cần plan approval và backup trước khi ghi live.

## Các lệnh hỗ trợ (alias vào gateway)
- `/tap:status`, `/tap:screen`, `/tap:flow`, `/tap:config`, `/tap:chat-display`, `/tap:orchestrate` → `tap-orchestration`.

Trên ChatGPT, slash aliases không phải contract portable. Hãy chọn plugin TAP trong Work chat rồi dùng prompt tự nhiên, ví dụ: “Dùng TAP để kiểm tra theme tenant”. Skill `tap-orchestration` là entrypoint chung.

## Quy tắc orchestration
- Mọi yêu cầu có ghi phải qua B0 → B1 → B1.5 → B2 → B2.5 → B3 trước khi chốt plan. Chưa có xác nhận Requirement + Mockup của người dùng thì không sửa code, không save/publish, không ghi gì lên hệ thống; script `work_item_state.py` từ chối chuyển trạng thái sai thứ tự (lệnh `record-clarification`, `approve-mockup`, `record-coverage`, `record-requirement`, `record-independent-review`, `confirm-requirement`).
- Yêu cầu ghi dữ liệu chỉ có một lần duyệt plan. Các ghi reversible đã liệt kê trong plan được tự thực hiện sau khi duyệt.
- Xóa/không thể đảo ngược, thanh toán thật, gửi dữ liệu ra ngoài hoặc thiếu dữ liệu bắt buộc vẫn cần hỏi lại đúng tại điểm phát sinh.
- Plugin chỉ dùng MCP tools được kết nối trong phiên. Không phụ thuộc hoặc truy cập source directory bên ngoài plugin.
- Đây là routing contract kiểm chứng được ở lớp plugin, không phải security boundary của host; permission MCP và `tap-core` vẫn là lớp thực thi cuối.

## Changelog

### 3.3.1 (2026-11-17)
- Bổ sung `skills/tap-orchestration/references/usecase-rules.md` (lấy từ `src/backend/bff/plugins` trên main agentic-storefront, kèm mục "Tự kiểm trước khi in bảng"); B3 bắt buộc đọc và áp bộ quy tắc này.
- Bước mới B2.5 Rà soát độ phủ: tách yêu cầu thành R1..Rn, hỏi tối đa 5 câu (Khung hỏi), lệnh `record-coverage`.
- B3: `record-requirement --coverage-map` bắt buộc mọi R có ID case hoặc nằm trong "Chưa phủ" kèm lý do; từ chối Điều kiện trước chỉ ghi `Sau <ID>`.
- B3: rà độc lập bằng sub-agent trước khi hỏi Xác nhận (`record-independent-review`), tối đa 2 vòng; `confirm-requirement` bị chặn khi chưa rà đúng bảng hoặc còn lỗi chặn ở vòng 1. Ma trận phủ và phần rà còn tồn lưu trong work item và in dưới bảng; payload `save_requirement` giữ nguyên.

### 3.3.0 (2026-11-17)
- Bảng Requirement 9 cột (`ID | Scope | Trigger | Điều kiện trước | Chat panel | Display panel | Hệ thống | Không được làm | Pass rate`), kiểm Scope / Pass rate / quy tắc ID ổn định.
- Lưu Requirement qua MCP `save_requirement`; B5 khai thay đổi bằng `declare_requirement_changes`; resume bằng `get_requirement` / `list_requirements`.
- B1 hỏi thêm địa chỉ web tenant; bước mới B1.5 chạy thử use case trên web, kết quả gộp vào đề xuất trước mockup.
- Bắt buộc B0–B6 cho mọi yêu cầu có ghi (kể cả config); lệnh `progress`; lỗi cổng trả JSON `currentStep / missingGates / nextAction / progress`.
- Mọi câu hỏi / vấn đề theo Khung hỏi: phương án + giải thích + đề xuất.

## Layout host adapters

- `.claude-plugin/plugin.json`: manifest Claude/Cowork; giữ đường chạy Claude tương thích.
- `plugin.json`: portable Agent Plugins identity.
- `mcp.json`: portable MCP descriptor `type: stdio` gọi `npx -y mcp-remote http://localhost:8931/mcp`. Agent Plugins chỉ cho phép executable trần hoặc `./` path chứa trong package; không chứa implementation tool hay secret.
- `.codex-plugin/plugin.json`: compatibility manifest để discovery skills ở host cũ; root portable manifest là canonical với ChatGPT Desktop.
- Không có `.app.json`: mapping app kỹ thuật không cần thiết cho local STDIO package này.
