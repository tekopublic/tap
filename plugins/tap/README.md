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
- Agent orchestration gateway: Leader tạo/resume work item, phân loại intent, quản lý tối đa một lượt clarification UX, dựng mockup đa màn hình bằng Claude Design canvas (bắt buộc, không fallback HTML) trước plan; Implementer và Tester chỉ làm việc theo delegation context đã duyệt.
- Quản lý màn hình (Screen / Display): Tạo màn hình mới, sửa màn hình live an toàn không gây gián đoạn shopper, xóa màn hình có backup.
- Interaction Flow: Quản lý biểu mẫu nhiều bước, preview với session values trước khi publish.
- Cấu hình nâng cao: Tinh chỉnh persona (giọng nói, brand), parameter presets chip, runtime config và 5 tokens màu sắc của theme.
- Báo lỗi: khi gặp sự cố, plugin giải thích bằng tiếng Việt và đưa sẵn nội dung để copy gửi nhóm Google Chat TAP (không tự gửi, đã che dữ liệu nhạy cảm).
- Cổng an toàn (Safety Gates): Kiểm tra kết nối MCP TAP khi bắt đầu, người dùng chọn MCP một lần (được lưu lại), ghi lên PROD/LOCAL đều cần plan approval và backup trước khi ghi live.

## Các lệnh hỗ trợ (alias vào gateway)
- `/tap:status`, `/tap:screen`, `/tap:flow`, `/tap:config`, `/tap:chat-display`, `/tap:orchestrate` → `tap-orchestration`.

Trên ChatGPT, slash aliases không phải contract portable. Hãy chọn plugin TAP trong Work chat rồi dùng prompt tự nhiên, ví dụ: “Dùng TAP để kiểm tra theme tenant”. Skill `tap-orchestration` là entrypoint chung.

## Quy tắc orchestration
- Yêu cầu ghi dữ liệu chỉ có một lần duyệt plan. Các ghi reversible đã liệt kê trong plan được tự thực hiện sau khi duyệt.
- Xóa/không thể đảo ngược, thanh toán thật, gửi dữ liệu ra ngoài hoặc thiếu dữ liệu bắt buộc vẫn cần hỏi lại đúng tại điểm phát sinh.
- Plugin chỉ dùng MCP tools được kết nối trong phiên. Không phụ thuộc hoặc truy cập source directory bên ngoài plugin.
- Đây là routing contract kiểm chứng được ở lớp plugin, không phải security boundary của host; permission MCP và `tap-core` vẫn là lớp thực thi cuối.

## Layout host adapters

- `.claude-plugin/plugin.json`: manifest Claude/Cowork; giữ đường chạy Claude tương thích.
- `plugin.json`: portable Agent Plugins identity.
- `mcp.json`: portable MCP descriptor `type: stdio` gọi `npx -y mcp-remote http://localhost:8931/mcp`. Agent Plugins chỉ cho phép executable trần hoặc `./` path chứa trong package; không chứa implementation tool hay secret.
- `.codex-plugin/plugin.json`: compatibility manifest để discovery skills ở host cũ; root portable manifest là canonical với ChatGPT Desktop.
- Không có `.app.json`: mapping app kỹ thuật không cần thiết cho local STDIO package này.
