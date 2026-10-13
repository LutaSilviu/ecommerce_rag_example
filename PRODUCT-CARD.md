# Product card component

The reusable browser component lives in `app/static/product-card.js`, with its isolated styles in `app/static/product-card.css`. Its only direct runtime dependencies are `app/static/money.js` and `app/static/cart-state.js`.

## Loading

Include the stylesheet in the document head, then load scripts in dependency order before the page-specific catalog renderer:

```html
<link rel="stylesheet" href="/static/product-card.css">
<script defer src="/static/money.js"></script>
<script defer src="/static/cart-state.js"></script>
<script defer src="/static/product-card.js"></script>
<script defer src="/static/catalog-page.js"></script>
```

Because deferred classic scripts execute in document order, the catalog renderer can call `window.NexoProductCard` after these dependencies load.

## API

```js
const card = window.NexoProductCard.create(product, { onAdd });
container.append(card);
```

`product` uses the catalog fields `id`, `name`, `image_url`, `price_bani`, `stock_quantity`, and optional `is_active`. Price is integer bani and is formatted through `window.NexoMoney.formatRon`. `onAdd(product)` may return a promise resolving to the cart result shape `{ ok, error? }`; when omitted, the component calls `window.NexoCart.add(product.id)`. The component reports pending, success, and failure accessibly and disables add-to-cart when the product is unavailable.
