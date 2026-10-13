# Bảng Ánh Xạ Tên Server & Phân Vùng Môi Trường (Target Guard)

## 1. Cấu Hình Quy Định
- `prod_writes`: **cho phép** (đã bỏ chặn). Người dùng chọn server một lần ở MCP preflight; ghi lên PROD vẫn bắt buộc plan approval + backup, không hỏi lại từng thao tác.

## 2. Ánh Xạ Tiền Tố Server Trong Phiên Làm Việc

| Tên Server (Tiền Tố) | Phân Loại Môi Trường | URL Kết Nối | Ghi Chú An Toàn |
|---|---|---|---|
| `phongvu-tap-mcp` | **PROD** | `https://phongvu-tap-mcp.tekoapis.com/mcp` | Cho phép ghi khi đã chọn server và có plan approval + backup. |
| `agentic-storefront-mcp` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường dev/test. Cho phép ghi sau khi xác nhận. |
| `agentic-storefront-mcp-agent-shell` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường dev/test shell. |
| `tap-mcp-agent-shell` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường dev/test shell. |
| `tap4-datamart-mcp` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường datamart local (ngoài phạm vi tùy biến UI). |
| *(Tên bất kỳ khác)* | **LẠ (Coi như PROD)** | *(Không xác định)* | Coi như PROD: chỉ dùng khi người dùng đã chọn server này ở preflight. |

## 3. Quy Tắc Xử Lý Đa Server
Nếu phát hiện nhiều hơn 1 server TAP cùng xuất hiện trong một phiên làm việc:
1. Dùng server đã lưu qua `scripts/mcp_pref.py get` nếu còn trong phiên.
2. Chưa có lựa chọn: liệt kê server, hỏi người dùng chọn đích danh một lần, rồi lưu.
3. Chưa chọn thì chỉ dùng công cụ đọc.
