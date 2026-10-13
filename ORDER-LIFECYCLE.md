# Nexo Market — Order Lifecycle (T018)

**Status:** Contract for order creation, confirmation, history, and detail views.
**Depends on:** `SPEC.md`, `TASKS.md` T002/T012/T013/T017, `CART-RULES.md`, and `MOCK-PAYMENT-COPY.md`.

## 1. Meaning of an order

An order is a durable prototype record created when an authenticated customer confirms a valid checkout review. It records what the customer submitted, but is not evidence of a real purchase, charge, payment authorization, or delivery booking. The UI must consistently call it a **comandă demonstrativă** and say it was **înregistrată**.

The API and persistence layer use stable machine values; Romanian labels are presentation copy. Do not derive machine state from translated text.

## 2. Lifecycle and allowed transitions

For this MVP, an order has one successful lifecycle state:

| Machine state | Romanian presentation | Meaning |
|---|---|---|
| `registered` | `Înregistrată` | The prototype order record and its item/address snapshots were committed successfully. No payment was processed. |

Creation is atomic: the order and all its items are inserted in one database transaction. The state becomes `registered` only when that transaction commits. A validation or persistence failure creates no visible order and must leave the browser cart intact. A retry after a failed request may create one order; retrying after a successful response must not create a duplicate for the same confirmation action.

There is no customer cancellation, fulfillment, shipment, return, refund, or post-creation status transition in this MVP. Do not invent these flows. If a later feature adds them, define separate explicit transitions and timestamps. Do not show `pending`, `confirmed`, `completed`, or `cancelled` as if those states already have agreed customer-facing meanings in this prototype. In particular, never use an order status to imply that payment settled.

## 3. Mock payment state and copy alignment

Payment state is distinct from order lifecycle state and remains non-transactional for the entire lifetime of an order:

| Stored concept | Value for every created order | Romanian UI label |
|---|---|---|
| Payment method | `simulated` | `Plată simulată (prototip)` |
| Payment status | `not_processed` | `Plată simulată — neprocesată` |

The method/status values describe a simulation, not a card or cash transaction. Keep the T002 wording from `MOCK-PAYMENT-COPY.md` visible at method selection, final review, confirmation, order history, and order details. The pre-submit review says no payment will be processed and the customer will not be charged; confirmation says the test record was saved and no payment occurred. Do not use `completed`, `paid`, `approved`, `settled`, `payment successful`, or equivalent wording or state for any mock order.

The present domain model's `MockPaymentStatus.COMPLETED` and payment methods `card` / `cash_on_delivery` are not valid values for a T018 order. T029 and the persistence/API implementation must represent the mock-only method/status above (or use a different internal representation with exactly the same semantics). Do not collect card fields, cash collection details, processor identifiers, authorization results, or payment credentials.

## 4. Creation eligibility and source of truth

Order creation uses the authenticated account from the server session as owner. The server re-resolves every cart product and validates the active/in-stock status and quantity against current catalog data. It ignores client-supplied user IDs, names, images, prices, line totals, subtotal, shipping, and total.

Only a non-empty, fully valid cart can be committed. Calculate each item amount from the current catalog price in integer bani multiplied by quantity. Sum with the shared money helpers. Under `CART-RULES.md`, `shipping_bani` is zero because no shipping policy is defined, and `total_bani = subtotal_bani + shipping_bani`. The UI must identify the delivery amount as not configured for this prototype; it must not imply a real delivery quote or free delivery.

If catalog availability or stock changed since review, reject the entire submission, create no order, explain the issue in Romanian, and return the customer to review. Never create a partial order or silently alter its contents or quantity.

## 5. Immutable order snapshots

At successful creation, persist an immutable snapshot of:

- The owning customer ID and order ID.
- Each line's stable product ID, SKU, Romanian product name, image URL (if present), unit price in bani, whole quantity, and line total in bani.
- The submitted Romanian delivery address fields.
- Subtotal, zero shipping amount, total, selected mock method, and fixed unprocessed payment status.
- The unique human-readable order number and creation timestamp.

For each line, `line_total_bani = unit_price_bani × quantity`; `subtotal_bani` equals the sum of snapshot line totals; `total_bani = subtotal_bani + shipping_bani`. All stored values are integer bani. Order screens read these stored snapshots rather than joining current product details or recalculating historical prices from the mutable catalog. Later changes to a product name, image, SKU, or price must not rewrite an existing order. Address changes in the customer's account likewise must not rewrite an order's address.

Treat snapshots as append-only after commit. This MVP does not implement edits, cancellations, refunds, or payment-state changes. Any administrative repair capability would require a separately designed audit trail and is out of scope.

## 6. Timestamps

- `created_at` is assigned by the server at order creation in UTC, with timezone information; it represents the time the order transaction is committed, not when the cart was first populated or review opened.
- Serialize API timestamps as ISO 8601/RFC 3339 UTC (for example, `2026-10-12T10:30:00Z`). Persist timezone-aware UTC values consistently.
- Render dates in the Romanian locale and `Europe/Bucharest` timezone for customers. Formatting is presentation only; retain the UTC instant in storage and API data.
- Do not add `paid_at`, `payment_completed_at`, `shipped_at`, or similar timestamps: no such event occurs in this prototype. Do not add `updated_at` unless a later lifecycle transition is introduced and its semantics are defined.

## 7. Unique human-readable order number

Use the format `NX-YYYYMMDD-XXXXXXXX`, where the date is the UTC creation date and `XXXXXXXX` is eight uppercase base-32 characters generated from a cryptographically secure random source (alphabet `0123456789ABCDEFGHJKMNPQRSTVWXYZ`, excluding ambiguous letters). The date aids customer support; the random suffix is not a secret or authorization token.

Enforce a database unique constraint on the complete order number. On the extremely unlikely collision, generate a fresh suffix and retry the transaction a small bounded number of times; if retries are exhausted, fail creation safely and retain the cart. Never rely on a process-local counter, timestamp alone, or a check-then-insert without the database constraint. Order access still requires authenticated owner scoping; knowing an order number does not grant access.

Display the exact same order number in confirmation, account history, and order detail. The opaque UUID remains the internal/API identity where appropriate; the human-readable number is for display and support.

## 8. Effects on dependent tasks

- **T028** persists owner-scoped orders and immutable child item/address snapshots; it must enforce unique order numbers and atomic writes.
- **T029** applies the eligibility checks, recomputes bani totals, assigns the UTC timestamp and order number, and stores `registered` plus `simulated` / `not_processed` semantics exactly once per successful action.
- **T051–T053** must keep the review warning, registered confirmation, and order number consistent with `MOCK-PAYMENT-COPY.md`; clear the cart only after successful commit.
- **T054–T055** show snapshot values, `Comandă demonstrativă`, and `Plată simulată — neprocesată`; list newest orders first by `created_at`.
- **T056** preserves the Romanian labels and localized time display without changing machine state or implying payment settlement.
- **T059** verifies that no payment credentials or processor data are stored and that all order reads are owner-scoped.

If T012's current `OrderStatus` or `MockPaymentStatus` enums cannot encode this contract, update those domain/API types as part of their owning implementation task before consumers rely on them. Do not weaken the lifecycle semantics to fit an enum value that suggests payment completion.
