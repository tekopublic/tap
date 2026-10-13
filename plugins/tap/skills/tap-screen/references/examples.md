# Mã Mẫu Chuẩn Cho Renderer Mount (Examples)

## Mẫu 1: Màn Hình Đơn Giản (Thông Báo / Giỏ Hàng Trống)

```javascript
/**
 * Màn hình thông báo giỏ hàng trống và gợi ý sản phẩm
 */
export function mount(root, ctx) {
  const container = document.createElement("div");
  container.className = "tap-empty-cart-card";
  container.style.padding = "24px";
  container.style.textAlign = "center";
  container.style.backgroundColor = "#ffffff";
  container.style.borderRadius = "8px";

  const title = document.createElement("h3");
  title.innerText = "Giỏ hàng của bạn đang trống";
  title.style.color = "#333333";

  const btn = document.createElement("button");
  btn.innerText = "Tiếp tục mua sắm";
  btn.style.marginTop = "16px";
  btn.style.padding = "10px 20px";
  btn.style.backgroundColor = (ctx.theme && ctx.theme.primaryColor) || "#0052cc";
  btn.style.color = "#ffffff";
  btn.style.border = "none";
  btn.style.borderRadius = "4px";
  btn.style.cursor = "pointer";

  btn.addEventListener("click", () => {
    // Điều hướng hoặc đổi state thông qua ctx
    if (ctx.setSessionValue) {
      ctx.setSessionValue("active_tab", "home");
    }
  });

  container.appendChild(title);
  container.appendChild(btn);
  root.appendChild(container);

  return () => {
    root.innerHTML = "";
  };
}
```

## Mẫu 2: Màn Hình Có DataSource & Action Execute

```javascript
/**
 * Màn hình kèm DataSource khai báo hợp lệ
 */
export const dataSources = {
  featuredProducts: {
    operationId: "get_featured_products",
    params: { limit: 5 }
  }
};

export function mount(root, ctx) {
  const container = document.createElement("div");
  container.className = "tap-featured-panel";

  const list = document.createElement("ul");
  const products = (ctx.data && ctx.data.featuredProducts) || [];

  products.forEach(p => {
    const item = document.createElement("li");
    item.innerText = `${p.name} - ${p.price}đ`;

    const addBtn = document.createElement("button");
    addBtn.innerText = "Thêm";
    addBtn.addEventListener("click", async () => {
      addBtn.disabled = true;
      try {
        await ctx.execute("add_to_cart", { productId: p.id, quantity: 1 });
        addBtn.innerText = "Đã thêm ✓";
      } catch (err) {
        addBtn.disabled = false;
        console.error("Lỗi khi thêm giỏ hàng:", err);
      }
    });

    item.appendChild(addBtn);
    list.appendChild(item);
  });

  container.appendChild(list);
  root.appendChild(container);

  return () => {
    root.innerHTML = "";
  };
}
```
