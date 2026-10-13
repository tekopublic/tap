---
description: Điều phối yêu cầu tự nhiên theo Leader, Implementer và Tester với một lần duyệt plan cho thao tác ghi.
argument-hint: "<yêu cầu tự nhiên>"
disable-model-invocation: true
---

Delegated-by: `tap-orchestration`.

Chuyển nguyên yêu cầu `$ARGUMENTS` cùng alias context `orchestrate` vào duy nhất skill `tap-orchestration`. Gateway tự quản lý triage, safety gate, mockup, plan và delegation. Không gọi worker hoặc MCP tool trực tiếp.
