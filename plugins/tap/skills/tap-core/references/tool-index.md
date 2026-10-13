# Danh Mục 59 Tools MCP TAP (Generated)

> Tự động sinh từ source tree được chỉ định (0dd7353f, sạch: True) ngày 2026-10-12.

| # | Tên Tool | Lớp | Quyền IAM | Tham số | Mô tả tóm tắt |
|---|---|---|---|---|---|
| 1 | `add_parameter_preset` | **R2** | `mcp-server:tap:update:add_parameter_preset` | `triggers`, `params` | Append one preset to the tenant's runtime config (#238). |
| 2 | `archive_report` | **R3** | `mcp-server:mcp:update:archive_report` | `reportId`, `tenantId?` | Archive one of your BI reports. |
| 3 | `create_preview_session` | **R1** | `mcp-server:tap:update:create_preview_session` | `sessionValues?`, `moduleStates?` | Mint a durable preview session — the per-user "simulated |
| 4 | `delete_interaction_flow` | **R3** | `mcp-server:tap:update:delete_interaction_flow` | `flowId`, `tenantId?` | Soft-retire a flow — hidden from ``list_interaction_flows`` |
| 5 | `delete_preview_session` | **R1** | `mcp-server:tap:update:delete_preview_session` | `previewSessionId` | Explicit teardown. Idempotent — unknown ids (or ids you |
| 6 | `delete_screen` | **R3** | `mcp-server:tap:update:delete_screen` | `code`, `themeId?`, `tenantId?` | Archive a display — immediately removed from selection; the row |
| 7 | `describe_display_format` | **R0** | `mcp-server:tap:read:describe_display_format` | - | Return the renderer contract a display panel must satisfy. |
| 8 | `describe_endpoint` | **R0** | `mcp-server:tap:read:describe_endpoint` | `operationId` | Return the full request/response shape of one operation. |
| 9 | `describe_interaction_flow_format` | **R0** | `mcp-server:tap:read:describe_interaction_flow_format` | - | Return the authoring grammar a ``save_interaction_flow`` |
| 10 | `describe_parameter` | **R0** | `mcp-server:tap:read:describe_parameter` | `name`, `valuesLimit?` | Full detail for one parameter. |
| 11 | `describe_report_template` | **R0** | `mcp-server:mcp:read` | `tenantId?` | Return what a report-page `template` may contain, with an example. |
| 12 | `describe_state` | **R0** | `mcp-server:tap:read:describe_state` | `moduleId`, `stateValue` | Answer "what can a screen bound to this state do next?" |
| 13 | `describe_table` | **R0** | `mcp-server:mcp:read:describe_table` | `database`, `schema`, `tableName` | Return column definitions and sample rows for one table. |
| 14 | `get_interaction_flow` | **R0** | `mcp-server:tap:read:get_interaction_flow` | `flowId`, `version?`, `tenantId?` | Get one flow's full detail — status, title, the flow schema, |
| 15 | `get_persona` | **R0** | `mcp-server:tap:read:get_persona` | - | Read the tenant's persona (voice/brand only, #238). |
| 16 | `get_persona_draft` | **R0** | `mcp-server:tap:read:get_persona_draft` | - | Read the tenant's draft persona (#143 — lifecycle draft/publish). |
| 17 | `get_preview_session` | **R0** | `mcp-server:tap:read:get_preview_session` | `previewSessionId` | Read a preview session's current state — ``sessionValues``, |
| 18 | `get_query_history` | **R0** | `mcp-server:mcp:read:get_query_history` | `limit?` | Return the caller's own recent queries from the StarRocks audit table. |
| 19 | `get_report` | **R0** | `mcp-server:mcp:read:get_report` | `reportId`, `tenantId?` | Get one BI report of yours: title, SQL, status. |
| 20 | `get_report_snapshot` | **R0** | `mcp-server:mcp:read:get_report` | `reportId`, `tenantId?` | Run a saved report and return its columns plus a sample of rows. |
| 21 | `get_runtime_config` | **R0** | `mcp-server:tap:read:get_runtime_config` | - | Read the tenant's runtime config. |
| 22 | `get_screen` | **R0** | `mcp-server:tap:read:get_screen` | `code`, `themeId?`, `tenantId?` | Get one screen's full detail: code, name, status, binding |
| 23 | `get_theme` | **R0** | `mcp-server:tap:read:get_theme` | `themeId?`, `tenantId?` | Return the tenant's active (or specified) theme. |
| 24 | `list_endpoints` | **R0** | `mcp-server:tap:read:list_endpoints` | `serviceCode` | List operations exposed by one service. |
| 25 | `list_entities` | **R0** | `mcp-server:tap:read:list_entities` | - | List the entities available to this tenant with each entity's declared state values. |
| 26 | `list_interaction_flows` | **R0** | `mcp-server:tap:read:list_interaction_flows` | `tenantId?` | List every interaction flow for the tenant — flowId, |
| 27 | `list_layouts` | **R0** | `mcp-server:tap:read:list_layouts` | - | List the platform's code-shipped layout templates and the installed design systems. |
| 28 | `list_modules` | **R0** | `mcp-server:tap:read:list_modules` | - | List the modules available to this tenant with each module's declared state values. |
| 29 | `list_parameter_presets` | **R0** | `mcp-server:tap:read:list_parameter_presets` | - | List the tenant's parameter presets. |
| 30 | `list_parameter_values` | **R0** | `mcp-server:tap:read:list_parameter_values` | `name`, `limit?`, `offset?` | Enumerate a parameter's value catalog (paged). |
| 31 | `list_parameters` | **R0** | `mcp-server:tap:read:list_parameters` | - | List every parameter declared for this tenant's operations. |
| 32 | `list_report_channels` | **R0** | `mcp-server:mcp:read:list_report_channels` | `tenantId?` | List report publishing channels and output formats. |
| 33 | `list_reports` | **R0** | `mcp-server:mcp:read:list_reports` | `includeArchived?`, `tenantId?` | List the BI reports you authored, newest first. |
| 34 | `list_schemas` | **R0** | `mcp-server:mcp:read:list_schemas` | - | List all schemas in this tenant's datamart, with their tables. |
| 35 | `list_screens` | **R0** | `mcp-server:tap:read:list_screens` | `themeId?`, `tenantId?` | List the theme's displays: code, name, status (draft/published/ |
| 36 | `list_services` | **R0** | `mcp-server:tap:read:list_services` | - | List the API services available to this tenant. |
| 37 | `list_session_values` | **R0** | `mcp-server:tap:read:list_session_values` | - | List every declared session-value key and whether the shopper may |
| 38 | `list_state_transitions` | **R0** | `mcp-server:tap:read:list_state_transitions` | `moduleId?` | List every state-transition edge for this tenant's modules. |
| 39 | `ping` | **R0** | *(không cần)* | - | Placeholder tool — verifies connectivity and authentication. |
| 40 | `preview_interaction_flow` | **R0** | `mcp-server:tap:read:preview_interaction_flow` | `flowId`, `previewSessionId?`, `control?`, `tenantId?` | Interactively step through a flow's draft (falling back to |
| 41 | `preview_screen` | **R0** | `mcp-server:tap:read:preview_screen` | `blobContent?`, `ctx?`, `screenCode?`, `previewSessionId?` | Preview a display panel blob without saving or publishing. |
| 42 | `publish_interaction_flow` | **R2** | `mcp-server:tap:update:publish_interaction_flow` | `flowId`, `tenantId?` | Promote the existing draft to published — runs the full |
| 43 | `publish_persona` | **R2** | `mcp-server:tap:update:publish_persona` | - | Promote the tenant's draft persona to published (#143). |
| 44 | `publish_report` | **R3** | `mcp-server:mcp:update:publish_report` | `reportId`, `channels?`, `password?`, `slug?`, `externalRef?`, `template?`, `tenantId?` | Publish a saved report: run its SQL now and send the result out. |
| 45 | `publish_screen` | **R2** | `mcp-server:tap:update:publish_screen` | `code`, `name?`, `blobContent?`, `conditions?`, `themeId?`, `tenantId?` | Publish a display — it becomes selectable on the very next |
| 46 | `query_data` | **R0** | `mcp-server:mcp:read:query_data` | `sql`, `format?` | Execute a StarRocks SQL SELECT against this tenant's datamart. |
| 47 | `refresh_report` | **R3** | `mcp-server:mcp:update` | `reportId`, `channel?`, `tenantId?` | Update a report's published copies in place with fresh data. |
| 48 | `remove_parameter_preset` | **R2** | `mcp-server:tap:update:remove_parameter_preset` | `trigger` | Remove the preset whose first non-empty ``triggers[0]`` |
| 49 | `save_interaction_flow` | **R1** | `mcp-server:tap:update:save_interaction_flow` | `parsedSchema`, `flowId?`, `tenantId?` | Save a tenant-authored interaction flow as a DRAFT — stored |
| 50 | `save_persona_draft` | **R1** | `mcp-server:tap:update:save_persona_draft` | `fields` | Full-replace the tenant's draft persona with ``fields`` (#143). |
| 51 | `save_report` | **R1** | `mcp-server:mcp:update:save_report` | `title`, `sql`, `reportId?`, `tenantId?` | Save a BI report: a titled SQL query that can later be published. |
| 52 | `save_screen` | **R1** | `mcp-server:tap:update:save_screen` | `code`, `name`, `blobContent`, `conditions?`, `themeId?`, `tenantId?` | Save a display renderer as a DRAFT — stored but not selectable. |
| 53 | `search_parameter_values` | **R0** | `mcp-server:tap:read:search_parameter_values` | `query`, `parameterName?`, `limit?`, `minScore?` | Relevance-ranked search for parameter values. |
| 54 | `set_layout` | **R2** | `mcp-server:tap:update:set_layout` | `layoutCode`, `designSystem`, `tenantId?` | Set the storefront layout and the active theme's design system. |
| 55 | `set_preview_session_values` | **R1** | `mcp-server:tap:update:set_preview_session_values` | `previewSessionId`, `sessionValues?`, `moduleStates?`, `mode?` | Update a preview session's shopper state. Validated against |
| 56 | `unpublish_report` | **R3** | `mcp-server:mcp:update:unpublish_report` | `reportId`, `channel?`, `tenantId?` | Take a published report down from one channel. |
| 57 | `update_persona` | **R2** | `mcp-server:tap:update:update_persona` | `fields` | Full-replace the tenant's persona (voice/brand only, #238) |
| 58 | `update_runtime_config` | **R2** | `mcp-server:tap:update:update_runtime_config` | `fields` | Replace the tenant's whole runtime-config group with ``fields``. |
| 59 | `update_theme` | **R2** | `mcp-server:tap:update:update_theme` | `tokens`, `name?`, `tenantId?` | Merge brand color tokens into the tenant's active theme. |
