# Các Bẫy Renderer & Quy Tắc Kiểm Tra Shape Check (DISP-5)

Mọi mã nguồn Javascript renderer của màn hình (`blobContent`) đều phải vượt qua bộ kiểm tra tĩnh và kiểm tra runtime của TAP Renderer.

## 1. Các Cú Pháp Bị Cấm Tuyệt Đối (DISP-5 `shape_check_failed`)

Nếu vi phạm bất kỳ điều nào dưới đây, `preview_screen` sẽ trả `shapeCheck.ok = false` và `publish_screen` sẽ từ chối:
* ❌ **Không gọi API mạng trực tiếp**: Cấm `fetch(...)`, `XMLHttpRequest`, `axios`, `WebSocket`, `EventSource`, `navigator.sendBeacon`.
  * 👉 **Cách đúng**: Sử dụng `ctx.execute(operationId, payload)` hoặc khai báo `export const dataSources = {...}`.
* ❌ **Không điều hướng trang**: Cấm `window.location`, `location.href`, `location.replace()`, `window.open()`.
  * 👉 **Cách đúng**: Gửi sự kiện hoặc điều hướng qua state machine của storefront.
* ❌ **Không thực thi mã động**: Cấm `eval(...)`, `new Function(...)`, `setTimeout(string, ...)`.
* ❌ **Không thao tác DOM bên ngoài root container**: Cấm `document.body.appendChild(...)`, `document.head...`.
  * 👉 **Cách đúng**: Chỉ render và gắn element vào phần tử `root` được truyền vào trong hàm `mount(root, ctx)`.

## 2. Quản Lý Vòng Đời & Dọn Dẹp (Cleanup)
Nếu bạn đăng ký event listener (như `window.addEventListener('resize', ...)`) hoặc bộ đếm thời gian (`setInterval`):
* Hàm `mount(root, ctx)` **bắt buộc phải trả về một hàm cleanup**:
```javascript
export function mount(root, ctx) {
  const timer = setInterval(() => { ... }, 1000);
  // ... render giao diện ...

  return () => {
    clearInterval(timer); // Dọn dẹp khi màn hình bị unmount
  };
}
```

## 3. Quản Lý CSS
* Hãy sử dụng class name có tiền tố riêng biệt hoặc CSS-in-JS để tránh ảnh hưởng đến các thành phần khác của storefront.
* Ưu tiên sử dụng các biến CSS theme được cung cấp trong `ctx.theme` (ví dụ `var(--color-primary)`).
