---
description: Thiết kế hoặc sửa journey phối hợp chat/interaction flow với display panel của tenant TAP.
argument-hint: "<mô tả hành vi chat ↔ panel>"
disable-model-invocation: true
---

Delegated-by: `tap-orchestration`.

Chuyển nguyên yêu cầu `$ARGUMENTS` cùng alias context `chat-display` vào duy nhất skill `tap-orchestration`. Không gọi worker hoặc MCP tool trực tiếp.
