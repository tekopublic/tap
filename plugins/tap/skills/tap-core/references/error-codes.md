# Tra Cứu Mã Lỗi MCP TAP (Generated)

> Tổng hợp 72 mã lỗi định danh từ source tree được chỉ định.

| Mã Lỗi | Vị Trí Code Xuất Hiện | Ý Nghĩa & Hướng Xử Lý |
|---|---|---|
| `admin_writer_unavailable` | `tools/create_preview_session.py:89`, `tools/delete_preview_session.py:63`, `tools/get_preview_session.py:70` | Dịch vụ Admin Writer tạm thời không phản hồi. Thử lại sau ít phút. |
| `auth_scope` | `tools/_report_common.py:52` | Thiếu phạm vi xác thực IAM tương ứng với tenant hiện tại. |
| `bad_blob` | *(từ catalog)* | Nội dung JS blob không hợp lệ hoặc thiếu export hàm mount(root, ctx). |
| `bad_condition` | `services/screen_service.py:165` | Điều kiện conditions không đúng định dạng mảng JSON hoặc sai cấu trúc module/state. |
| `bad_data_sources` | *(từ catalog)* | Khai báo export const dataSources không hợp lệ. |
| `bad_input` | *(từ catalog)* | Tham số đầu vào không đúng định dạng hoặc thiếu trường bắt buộc. |
| `bad_limit` | *(từ catalog)* | Tham số limit vượt quá ngưỡng cho phép. |
| `bad_offset` | *(từ catalog)* | Tham số offset không hợp lệ. |
| `bad_operation` | *(từ catalog)* | Operation ID không hợp lệ trong preview dispatch. |
| `bad_payload` | *(từ catalog)* | Payload không đúng định dạng mong đợi. |
| `bad_placeholder` | *(từ catalog)* | Placeholder trong dataSources không khớp với tham số yêu cầu. |
| `bad_preset` | *(từ catalog)* | Cấu trúc parameter preset không hợp lệ. |
| `bad_query` | *(từ catalog)* | Chuỗi tìm kiếm tham số không hợp lệ. |
| `bad_session_value_type` | *(từ catalog)* | Kiểu dữ liệu gán cho session value không khớp định nghĩa catalog. |
| `bad_token_value` | *(từ catalog)* | Giá trị màu sắc token không hợp lệ (cần mã hex hoặc CSS color hợp lệ). |
| `bad_trigger` | *(từ catalog)* | Trigger không hợp lệ khi xóa hoặc sửa preset. |
| `binding_conflict` | *(từ catalog)* | Xung đột binding DISP-4: Đã có màn hình published khác chiếm binding này trong theme. Đổi conditions hoặc archive màn hình cũ. |
| `custom_form_service_unavailable` | `tools/_interaction_flow_common.py:55`, `tools/preview_interaction_flow.py:90` | Dịch vụ Custom Form tạm thời không khả dụng. |
| `data_source_not_read` | `services/data_sources_service.py:19` | DataSource được khai báo nhưng không được đọc trong hàm mount. |
| `display_spec_invalid` | *(từ catalog)* | Admin Writer từ chối spec hiển thị (DISP-5). Kiểm tra lại mảng errors/warnings trả về. |
| `empty_tokens` | `services/theme_service.py:62` | Mảng tokens cập nhật không được rỗng. |
| `forbidden_key` | *(từ catalog)* | Khóa session value bị cấm thao tác. |
| `forbidden_session_value_key` | *(từ catalog)* | Khóa session value không có quyền ghi (writable: false). Chỉ được ghi các khóa writable. |
| `metadata_store_unavailable` | `tools/describe_table.py:168`, `tools/list_schemas.py:91` | Kho metadata tạm thời không khả dụng. |
| `missing_name` | *(từ catalog)* | Tên màn hình (name) là bắt buộc khi publish màn hình mới. |
| `no_active_theme` | *(từ catalog)* | Tenant chưa có theme nào đang kích hoạt. |
| `no_draft` | `services/persona_service.py:156` | Không tìm thấy bản nháp (draft) để publish. Hãy lưu bản nháp trước. |
| `no_intent_set` | *(từ catalog)* | Tenant chưa được gắn IntentSet tương ứng trong registry. |
| `no_value_catalog` | *(từ catalog)* | Tham số không có catalog giá trị cố định để liệt kê. |
| `not_found` | `tools/describe_table.py:171` | Bản ghi yêu cầu không tồn tại trên hệ thống. |
| `parse_error` | *(từ catalog)* | Lỗi cú pháp schema flow JSON không thể parse. |
| `partial_payload` | *(từ catalog)* | Thiếu khóa trong payload. update_runtime_config yêu cầu đủ 4 khóa: targetStates, contextDefaults, parameterPresets, preferredParams (truyền null nếu muốn xóa). |
| `permission_check_unavailable` | `tools/describe_table.py:134`, `tools/list_schemas.py:84` | Dịch vụ kiểm tra quyền IAM tạm thời không khả dụng. |
| `permission_denied` | `tools/describe_table.py:161` | Từ chối quyền truy cập do tài khoản không có quyền IAM tương ứng. |
| `preset_conflict` | *(từ catalog)* | Trùng trigger preset đã tồn tại. Cần hỏi người dùng có muốn thay thế không. |
| `preset_not_found` | *(từ catalog)* | Không tìm thấy preset tương ứng với trigger. |
| `preview_session_not_found` | *(từ catalog)* | Phiên preview session không tồn tại hoặc đã hết hạn. |
| `renderer_rejected` | *(từ catalog)* | Dịch vụ renderer từ chối xử lý blob. |
| `renderer_unavailable` | `tools/preview_screen.py:139` | Dịch vụ renderer preview tạm thời không khả dụng. |
| `report_empty_result` | *(từ catalog)* | Báo cáo SQL trả về kết quả rỗng, không thể xuất bản. |
| `report_query_failed` | *(từ catalog)* | Truy vấn SQL của báo cáo thất bại. Kiểm tra lại cú pháp SQL. |
| `report_sql_empty` | `services/report_service.py:86` | Câu lệnh SQL của báo cáo không được để trống. |
| `report_sql_invalid` | *(từ catalog)* | Câu lệnh SQL không hợp lệ hoặc chứa cú pháp bị cấm. |
| `report_sql_too_long` | *(từ catalog)* | Câu lệnh SQL vượt quá độ dài tối đa cho phép. |
| `report_still_published` | *(từ catalog)* | Báo cáo đang ở trạng thái published, không thể archive. Cần unpublish trước. |
| `report_title_empty` | `services/report_service.py:84` | Tiêu đề báo cáo không được để trống. |
| `report_too_many_rows` | *(từ catalog)* | Số dòng trả về vượt quá giới hạn snapshot cho phép. |
| `reports_unavailable` | `services/report_service.py:396`, `services/report_service.py:573`, `tools/_report_common.py:74` | Dịch vụ báo cáo tạm thời không khả dụng. |
| `run_not_found` | *(từ catalog)* | Không tìm thấy phiên thực thi run của interaction flow. |
| `screen_not_found` | *(từ catalog)* | Màn hình với code chỉ định không tồn tại trong theme. |
| `search_unavailable` | `tools/search_parameter_values.py:90` | Tính năng tìm kiếm giá trị tham số tạm thời không khả dụng. |
| `shape_check_failed` | *(từ catalog)* | Vi phạm quy tắc an toàn Shape Check DISP-5 (sử dụng API cấm như fetch, window.location). |
| `tenant_scope` | `tools/_interaction_flow_common.py:41`, `tools/_report_common.py:49`, `tools/_screen_common.py:43` | Lỗi phạm vi tenant: Token xác thực không khớp với tenantId truyền vào. |
| `theme_not_found` | *(từ catalog)* | Theme không tồn tại trong tenant. |
| `token_not_allowed` | *(từ catalog)* | Token không nằm trong danh sách cho phép (chỉ hỗ trợ 5 token: color.primary, color.primary.hover, color.primary.contrast, color.chat.user, color.chat.assistant). |
| `unknown_design_system` | *(từ catalog)* | Design system không hợp lệ hoặc chưa được hỗ trợ. |
| `unknown_endpoint` | *(từ catalog)* | Endpoint API không tồn tại. |
| `unknown_entity` | *(từ catalog)* | Entity không tồn tại trong catalog. |
| `unknown_field` | *(từ catalog)* | Trường dữ liệu không hợp lệ đối với đối tượng này. |
| `unknown_layout` | *(từ catalog)* | Layout code không tồn tại trong danh mục layout. |
| `unknown_module` | *(từ catalog)* | Module ID không tồn tại trong hệ thống. |
| `unknown_operation` | `services/data_sources_service.py:11` | Operation ID không tồn tại trong danh mục API của dịch vụ. |
| `unknown_parameter` | *(từ catalog)* | Tham số không tồn tại trong catalog. |
| `unknown_service` | *(từ catalog)* | Dịch vụ API không tồn tại trong IntentSet. |
| `unknown_session_value_key` | *(từ catalog)* | Khóa session value không tồn tại trong catalog. |
| `unknown_state` | *(từ catalog)* | State không tồn tại trong module chỉ định. |
| `unknown_tenant` | `services/report_service.py:140`, `services/report_service.py:267`, `tools/describe_table.py:127` | Không tìm thấy tenant trong registry. |
| `upstream_unavailable` | `services/intent_api_service.py:72`, `tools/list_entities.py:41`, `tools/list_modules.py:41` | Dịch vụ upstream tạm thời không phản hồi. |
| `validation_error` | *(từ catalog)* | Dữ liệu không vượt qua kiểm tra hợp lệ logic (xem chi tiết mảng issues). |
| `viz_unavailable` | `services/report_service.py:235`, `services/report_service.py:442`, `services/report_service.py:551` | Dịch vụ trực quan hóa visualization tạm thời không khả dụng. |
| `writer_rejected` | `tools/_interaction_flow_common.py:47`, `tools/_screen_common.py:76`, `tools/preview_interaction_flow.py:82` | Admin Writer từ chối yêu cầu ghi. |
| `writer_unavailable` | `tools/_interaction_flow_common.py:49`, `tools/_screen_common.py:78`, `tools/add_parameter_preset.py:67` | Dịch vụ Admin Writer tạm thời không kết nối được. |
