---
description: Soạn thảo hoặc cập nhật luồng interaction flow nhiều bước của tenant qua MCP TAP (draft, preview, xác nhận, publish).
argument-hint: "<mô tả flow mới | flowId cần sửa>"
disable-model-invocation: true
---

Delegated-by: `tap-orchestration`.

Chuyển nguyên yêu cầu `$ARGUMENTS` cùng alias context `flow` vào duy nhất skill `tap-orchestration`. Không gọi worker hoặc MCP tool trực tiếp.
