# Nexo Market — Ecommerce MVP Specification

## Product

Build a simple, customer-facing ecommerce website inspired by the broad shopping experience of eMAG. This is a single-store prototype with a mixed product catalog, localized for Romania. The working name is **Nexo Market**.

## Goals

- Let customers discover products across several categories, inspect product details, and manage a shopping cart.
- Support account registration and sign-in, including Google sign-in.
- Provide a complete checkout and order confirmation flow.
- Keep payment in prototype mode: show a payment choice or payment step, but do not collect card details or process real transactions.

## Audience and locale

- Customers shopping in Romania.
- Romanian-language interface.
- Display prices in Romanian lei (RON), formatted for Romanian locale.
- Checkout addresses should use Romanian fields, including county (județ), city/locality, street, and postal code.

## Core customer journey

1. **Browse:** View a storefront with search, category navigation, and product listings. Use a small sample catalog spanning categories such as electronics, home, fashion, and personal care.
2. **Find products:** Search by product name and filter by category. Selecting a product opens its details, price, availability, and add-to-cart action.
3. **Manage cart:** Add products, change quantities, remove items, and see the updated subtotal and order total.
4. **Create account or sign in:** Customers create an account with email and password or use Google sign-in. Checkout requires an authenticated account. Keep the signed-in state across page reloads.
5. **Checkout:** Collect and review contact and Romanian delivery-address details. Show an order summary and a clearly labeled mock payment step. Do not request or store payment card data.
6. **Place mock order:** Confirming checkout creates a prototype order with an order number and a success page. The customer can view their order confirmation and basic order history.

## Functional requirements

### Storefront and catalog

- Responsive layout suitable for desktop and mobile browsers.
- Product cards show image, name, price in RON, and an add-to-cart control.
- Product details show a larger image, description, price, and availability.
- Search and category filtering work against the sample catalog.
- Cart contents remain available when navigating and refreshing.

### Accounts

- Email/password registration, sign-in, and sign-out.
- Google sign-in through a real OAuth provider integration; configuration must be supplied through environment settings and must not be committed as a secret.
- Clear validation and error messages for invalid form input and failed sign-in.
- An account area shows basic profile information and placed mock orders.

### Checkout and orders

- Require sign-in before checkout; preserve the cart when redirecting to sign-in and back.
- Validate required contact and delivery-address fields.
- Show a final review of products, quantities, delivery details, and total before submission.
- Payment is a non-transactional mock step. Never collect card numbers, CVVs, or real payment credentials.
- On confirmation, create an order record with an order number, items, totals, delivery details, payment label/status indicating it is a mock, and creation time.
- Show an order confirmation page and make the order visible in the account area.

## Out of scope

- Multi-vendor seller accounts or seller dashboards.
- Real payment processing, card storage, or payment-provider integration.
- Real shipping-provider integration, label generation, and live delivery tracking.
- Production inventory management, tax/accounting workflows, and a full admin portal.
- Reviews, recommendations, loyalty programs, and advanced promotions.

## Prototype data and persistence

- Include realistic sample products and imagery suitable for a mixed catalog.
- Persist prototype cart, account/session, and mock orders using the chosen application storage/backend. Keep authentication credentials under a proper auth provider; do not store passwords directly in browser storage.
- Clearly distinguish prototype order/payment states from real purchases.

## Acceptance criteria

- A Romanian-language shopper can browse/search/filter the sample catalog, open a product, and add it to the cart.
- Cart item quantities and totals update correctly and survive navigation/refresh.
- A shopper can register and sign in with email/password, sign out, and sign in with Google when valid OAuth configuration is present.
- Checkout requires an account, validates Romanian delivery details, and presents a review step.
- Confirming checkout creates a mock order, displays an order confirmation, and makes the order visible from the account area.
- No real payment is attempted and no payment card data is collected.
- The website remains usable on narrow mobile screens and desktop screens.

## Configuration needed for live Google sign-in

Provide a Google OAuth client configuration through environment variables (or the chosen auth provider's equivalent) and register the local and deployed callback/origin URLs with Google. Until those values are supplied, the integration can be implemented but live Google authentication cannot be exercised.
