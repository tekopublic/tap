---
description: Báo cáo trạng thái tổng quan của tenant TAP (chỉ đọc, an toàn trên cả PROD).
disable-model-invocation: true
---

Delegated-by: `tap-orchestration`.

Chuyển nguyên yêu cầu `$ARGUMENTS` cùng alias context `status` vào duy nhất skill `tap-orchestration`. Không gọi worker hoặc MCP tool trực tiếp.
