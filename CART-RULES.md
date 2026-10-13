# Nexo Market — Shared Cart Rules (T017)

**Status:** Contract for cart state, cart UI, checkout validation, and mock order creation.
**Source contracts:** `app/domain/models.py`, `app/domain/money.py`, `app/catalog/taxonomy.py`, `DATA-AUTH-ARCHITECTURE.md`, and `SPEC.md`.

## 1. Cart line identity and shape

- A cart line is identified only by the product's stable `Product.id` UUID. SKU, name, category, and translated text are not identity keys.
- A cart contains at most one line per product ID. Adding the same product again increments that line's quantity; it does not create a duplicate line.
- The client-persisted line contains only `product_id` and `quantity`, matching `CartLine`. Do not persist or trust client-supplied price, name, SKU, image, stock, or totals.
- Product details shown with a line are resolved from the current catalog. The server resolves them again for checkout and order creation.
- Unknown product IDs found during cart hydration are discarded because they cannot be resolved against the catalog. An existing but inactive or out-of-stock product remains visible in the cart with its current unavailable state so the customer can remove it or correct the cart.

## 2. Quantity and stock rules

- Quantity is a whole integer from **1 through 99**, inclusive, as required by `CartLine.quantity` and `OrderItemSnapshot.quantity`.
- An add or increment that would exceed 99 is rejected with a clear Romanian message; do not silently wrap, overflow, or create another line.
- Availability is derived using `availability_for(is_active, stock_quantity)`: inactive means `unavailable`; active with zero stock means `out_of_stock`; active with positive stock means `in_stock`.
- Customers may add or increment only an active, in-stock product. The resulting quantity must not exceed the product's current `stock_quantity`; reject an increment that would exceed it and explain the current limit. The customer can always decrement or remove a line.
- Revalidate availability and stock whenever the cart is hydrated/reconciled, before checkout review, and on the server when creating an order. Catalog state can change after a line was added.
- If a line becomes inactive, reaches zero stock, or has quantity greater than current stock, keep the line visible but mark it unavailable/over the current limit, prevent order submission, and require removal or a valid quantity adjustment. Do not silently delete it or silently reduce its quantity.
- An order is valid only when every line refers to an active product, every quantity is between 1 and 99, and every quantity is at most the current stock. The prototype does not reserve stock when a product is placed in the cart. If stock changes between review and confirmation, order creation revalidates and returns the customer to review with a Romanian explanation; it must not create an invalid order.

## 3. Price, subtotal, delivery, and total

- Store and calculate all amounts as non-negative integer bani. One RON is 100 bani. Use `multiply_bani(unit_price_bani, quantity)` for each line and `add_bani(...)` to sum amounts; never use floating-point arithmetic.
- Current catalog `Product.price_bani` is the source of truth for cart display and checkout. Recompute each line amount as current unit price × quantity; do not trust a browser-submitted line total or retain a stale price as authoritative.
- `subtotal_bani` is the sum of all valid line totals.
- No delivery price or shipping rule is specified for this MVP. Therefore set `shipping_bani` to **0 bani** and `total_bani = subtotal_bani + shipping_bani` (which equals the subtotal). In the UI, identify delivery cost as not included/not configured in this prototype; do not label it “free delivery” or imply a real delivery quote.
- The order's stored `shipping_bani` must be zero under this contract. If an explicit shipping policy is decided later, revise this contract and all cart, checkout, and order consumers together.
- Format RON for Romanian UI with the shared `format_ron` helper (for example `1.234,56 RON`). Formatting is presentation only and never feeds arithmetic.
- The cart may be empty, in which case subtotal and total are zero and checkout cannot begin. The `Order` contract requires at least one item.

## 4. Unavailable items and checkout eligibility

- The cart can represent a line that became unavailable after it was added, but that line blocks checkout until removed or made valid again by a permitted quantity change.
- If an item is unavailable or exceeds stock, do not include it in a silently adjusted total and do not create a partial order from the remaining lines. Show the affected product and the action needed.
- Current product name, SKU, image, and unit price are copied into immutable `OrderItemSnapshot` values only when a valid mock order is created. The order line total is recalculated from the snapshot unit price and quantity. Later catalog edits must not change historical order values.
- The selected payment method/status is a non-transactional mock value from `MockPaymentState`; cart rules never collect or store payment credentials.

## 5. Persistence and sign-in expectations (T026/T027)

- Persist the anonymous cart in same-browser `localStorage` as product IDs and quantities only, following `DATA-AUTH-ARCHITECTURE.md`. Do not put passwords, session identifiers, OAuth data, or account credentials in browser storage.
- Hydrate by parsing defensively, validating each line against the `CartLine` bounds and catalog IDs, dropping malformed/unknown lines, and reconciling known products against current availability/stock. A corrupt cart must recover as a usable empty/partially valid cart rather than break storefront routes.
- The cart remains in that browser through registration, email sign-in, Google OAuth navigation/callback, and sign-out. Authentication alone does not clear or replace it.
- This MVP has no server-side or per-account cart and no cross-device synchronization. Thus sign-in does **not** merge an account cart with the browser cart: there is no account cart to merge. Preserve the current anonymous browser cart exactly, then continue applying catalog/stock validation. Do not add account-scoped cart persistence without a new product decision.
- Write the updated line set after each successful add, quantity change, removal, or clear. On confirmed order creation, clear the cart only after the server confirms the order transaction committed. If order creation fails, keep the cart intact.

## 6. Shared consumer obligations

- T026 implements the identity, quantity, hydration, persistence, and auth-retention behavior above.
- T027 preserves this exact browser cart across auth transitions; it must not invent account-cart merge behavior.
- T039 uses the same add operation and must surface quantity/availability rejection.
- T040/T041 display and edit only this contract's calculated values and unavailable states.
- T046/T050/T051 checkout review must show the same valid items, subtotal, zero prototype shipping amount with the stated limitation, and total.
- T029 re-resolves products, validates stock, calculates bani totals server-side, and snapshots current catalog facts before persistence. Cart/browser values are untrusted input.

