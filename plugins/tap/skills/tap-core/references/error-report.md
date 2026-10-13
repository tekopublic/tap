# Báo Cáo Lỗi Cho Team TAP (Giai đoạn 1: người dùng tự gửi)

Dùng khi gateway chuyển `BLOCKED`, hoặc gặp lỗi không tự xử lý được. Plugin không gửi mạng; chỉ tạo nội dung để người dùng copy vào nhóm Google Chat TAP.

## Phân loại → `--category`

| Tình huống | category |
|---|---|
| Không thấy server TAP nào / connector lỗi, hết hạn | `mcp-not-connected` |
| JSON-RPC `-32003 Permission denied` | `permission-denied` |
| Tool cần dùng bị ẩn khỏi danh sách | `tool-hidden` |
| Thiếu `operationId`/API cho tenant | `missing-api` |
| Thiếu theme/runtime config/dữ liệu nguồn | `missing-config` |
| `ok:false` do lỗi nội bộ, exception server (vd `'str' object has no attribute 'get'`) | `server-error` |
| Không tạo được Claude Design | `claude-design-unavailable` |
| Còn lại | `other` |

Không tạo báo cáo cho lỗi do người dùng thiếu thông tin (hỏi lại được trong 1 lượt clarification).

## Cách dùng

Chạy `python3 scripts/build_error_report.py --category <loại> --server <tên> --env <LOCAL|PROD> --tenant <t> --step "<bước>" --tool <tool> --code <mã> --message "<lỗi gốc>" --work-id <id> --phase <phase> --writes "<đã ghi gì>"` rồi **in nguyên văn kết quả cho người dùng** (không tóm tắt, không bỏ khung copy). Script tự che token/secret/email/sđt; không đưa thêm payload hay nội dung chat khách.

Mỗi lỗi một báo cáo; cùng một lỗi lặp trong phiên thì chỉ nhắc lại "đã có báo cáo ở trên".
