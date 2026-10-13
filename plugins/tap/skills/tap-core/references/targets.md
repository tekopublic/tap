# Bảng Ánh Xạ Tên Server & Phân Vùng Môi Trường (Target Guard)

## 1. Cấu Hình Quy Định
- `prod_writes: blocked`: **BẬT (Mặc định trong MVP)**. Mọi thao tác ghi lớp R1-R3 nhắm vào môi trường PROD đều bị từ chối và đề nghị diễn tập trên LOCAL.

## 2. Ánh Xạ Tiền Tố Server Trong Phiên Làm Việc

| Tên Server (Tiền Tố) | Phân Loại Môi Trường | URL Kết Nối | Ghi Chú An Toàn |
|---|---|---|---|
| `phongvu-tap-mcp` | **PROD** | `https://phongvu-tap-mcp.tekoapis.com/mcp` | Chặn mọi thao tác ghi (R1-R3). Chỉ cho phép đọc (R0). |
| `agentic-storefront-mcp` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường dev/test. Cho phép ghi sau khi xác nhận. |
| `agentic-storefront-mcp-agent-shell` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường dev/test shell. |
| `tap-mcp-agent-shell` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường dev/test shell. |
| `tap4-datamart-mcp` | **LOCAL** | `http://localhost:8931/mcp` | Môi trường datamart local (ngoài phạm vi tùy biến UI). |
| *(Tên bất kỳ khác)* | **LẠ (Coi như PROD)** | *(Không xác định)* | Coi như PROD: Chặn ghi, hỏi ý kiến người dùng trước. |

## 3. Quy Tắc Xử Lý Đa Server
Nếu phát hiện nhiều hơn 1 server TAP cùng xuất hiện trong một phiên làm việc:
1. Thông báo cho người dùng danh sách các server đang có.
2. Yêu cầu người dùng chọn đích danh server cần thao tác.
3. Mặc định chỉ dùng các công cụ đọc cho đến khi người dùng làm rõ.
