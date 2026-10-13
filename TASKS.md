# Nexo Market — Granular Implementation Task Plan

**Source:** [SPEC.md](./SPEC.md)  
**Product:** Romanian single-store ecommerce prototype for mixed products  
**Status:** Implementation started; see current progress below.

## Planning assumptions

- This file decomposes the existing MVP specification. It does not introduce multi-vendor, real payment, shipping integration, or a full admin system.
- Stack is selected: FastAPI serves a same-origin JSON API and build-free HTML/CSS/JavaScript UI. Deployment host remains open until release preparation.
- Accounts use a real authentication provider. Email/password and Google sign-in are real flows. Google sign-in requires client configuration and registered callback/origin URLs from the project owner.
- The catalog is sample data. The cart and orders are prototype records. Any chosen persistence must not store passwords or payment credentials in application storage.
- A mock payment option is a labeled prototype selection/status only. It never asks for card number, expiry, or CVV and never calls a payment processor.
- The storefront and customer-facing copy are Romanian, and product prices are displayed in RON.
- “Done” for each implementation task means its listed output exists, fits the agreed interfaces, and has no unresolved dependency called out in that task. This plan does not itself authorize execution of tests or external service changes.

## Dependency notation

- `Depends on` names tasks that must be completed first.
- `Unblocks` names work that can start after this task is complete.
- Tasks in the same phase can proceed in parallel when their dependencies are satisfied, provided shared interfaces are agreed first.
- The dependency graph is directional: a change to an upstream contract may require updates in every listed downstream task.

## Current implementation progress

| Task | Status | Notes |
|---|---|---|
| T001 | Complete | Scope reviewed against `SPEC.md`; boundaries are consistent. |
| T004 | Complete | Python 3.13.16, Node 26.11.1, npm 11.20.0, pip 26.2.1 and Git are available. Workspace initially had no app source or manifests. FastAPI/Uvicorn are not installed. |
| T005 | Complete | See [`TECH-STACK.md`](./TECH-STACK.md): Python/FastAPI + vanilla browser UI, same-origin API/static serving, SQLite/auth decisions deferred to T007. |
| T006 | Complete | See [`ROUTES.md`](./ROUTES.md) for page routes, guards, checkout return, and API boundary. |
| T007 | Complete | See [`DATA-AUTH-ARCHITECTURE.md`](./DATA-AUTH-ARCHITECTURE.md) for SQLite, email/password + Google OIDC, secure cookie sessions, and owner-scoped orders. |
| T002 | Complete | See [`MOCK-PAYMENT-COPY.md`](./MOCK-PAYMENT-COPY.md) for Romanian prototype payment/order copy. |
| T003 | Complete | See [`BRAND.md`](./BRAND.md) for replaceable Nexo Market name and brand guidance. |
| T008 | Complete | See [`DESIGN-SYSTEM.md`](./DESIGN-SYSTEM.md) for tokens, component patterns, responsive rules, and accessibility guidance. |
| T009 | Complete | See [`.env.example`](./.env.example) and [`CONFIGURATION.md`](./CONFIGURATION.md); all values are placeholders and no secrets were added. |
| T010 | Complete | FastAPI package/static scaffold and `pyproject.toml` are in place. Dependencies have not been installed. |
| T011 | Complete | `app/main.py` serves direct customer routes and keeps `/api/v1` JSON fallbacks separate; shared shell assets are in `app/static/`. |
| T012 | Complete | Pydantic domain/API contracts are in [`app/domain/models.py`](./app/domain/models.py); ORM models remain separate. |
| T013 | Complete | Integer-bani and Romanian RON helpers are in [`app/domain/money.py`](./app/domain/money.py). |
| T014 | Complete | Stable mixed-catalog taxonomy and product rules are in [`app/catalog/taxonomy.py`](./app/catalog/taxonomy.py). |
| T015 | Complete | Forty typed Romanian products with descriptions, images, prices, and stock across eight categories are in [`app/catalog/seed.py`](./app/catalog/seed.py). |
| T015a | Complete | Alembic migrations create catalog tables and import an immutable 40-product/8-category baseline; SQLAlchemy tables, insert-missing-only startup import, and the database-backed API reader are in [`migrations/`](./migrations), [`app/persistence/catalog_models.py`](./app/persistence/catalog_models.py), and [`app/catalog/repository.py`](./app/catalog/repository.py). Persisted catalog edits plus existing auth/order records are preserved across restart. |
| T016 | Complete | Typed, read-only catalog queries and diacritic-insensitive search are in [`app/catalog/repository.py`](./app/catalog/repository.py), backed by the migrated SQLite tables. |
| T017 | Complete | [`CART-RULES.md`](./CART-RULES.md) defines quantities, stock handling, total, delivery display, and persistence behavior. |
| T018 | Complete | [`ORDER-LIFECYCLE.md`](./ORDER-LIFECYCLE.md) defines registered prototype orders, immutable snapshots, `simulated` / `not_processed` payment, UTC times, and order numbers. |
| T018a | Complete | Domain models now encode only `registered` order status, `simulated` / `not_processed` payment, and required six-digit postal code. |
| T019 | Complete | `app/core/config.py` validates environment settings; Google project/client setup is explicitly pending external configuration. |
| T020 | Complete | [`app/auth/google.py`](./app/auth/google.py) conditionally creates the Authlib OIDC client when valid Google credentials are configured. |
| T020a | Complete | [`app/persistence/`](./app/persistence) contains SQLAlchemy engine/session setup and account/OAuth/session models. |
| T021 | Complete | Server-side opaque sessions and owner profile lookup are implemented; `/api/v1/auth/me` and `app/static/auth-state.js` expose safe auth state. |
| T022 | Complete | Romanian registration form UI is in [`app/static/partials/register.html`](./app/static/partials/register.html), loaded within the shared shell. |
| T023 | Complete | Romanian sign-in UI is in [`app/static/partials/login.html`](./app/static/partials/login.html). |
| T024 | Complete | Email registration/login use Argon2, normalized emails, same-origin checks, opaque HttpOnly sessions, and safe return-path handling. |
| T025 | Complete | Google OIDC start/callback, state/nonce protection, safe identity handling, provider availability, and Romanian UI states are implemented; live sign-in requires configured Google credentials. |
| T026 | Complete | [`app/static/cart-state.js`](./app/static/cart-state.js) provides versioned, malformed-data-safe local cart state. |
| T027 | Complete | [`app/static/cart-state.js`](./app/static/cart-state.js) reconciles the canonical browser cart after auth and preserves validated return destinations without storing credentials. |
| T028 | Complete | [`app/persistence/order_models.py`](./app/persistence/order_models.py) and [`app/persistence/order_repository.py`](./app/persistence/order_repository.py) provide owner-scoped order persistence and immutable order snapshots. |
| T029 | Complete | [`app/orders/service.py`](./app/orders/service.py) and [`app/orders/routes.py`](./app/orders/routes.py) validate current catalog/stock and create authenticated immutable mock-order snapshots. |
| T029a | Complete | `app.main` registers catalog/order routers before API/page fallbacks and creates order tables with auth schema. Orders now bind a per-user UUID `Idempotency-Key` durably to the committed order; checkout clients must reuse the same key for retries of one confirmation intent. |
| T030 | Complete | Responsive header is in [`app/static/index.html`](./app/static/index.html), [`app/static/site.css`](./app/static/site.css), and [`app/static/header.js`](./app/static/header.js); account/cart state and mobile category menu are wired. |
| T031 | Complete | [`app/catalog/routes.py`](./app/catalog/routes.py) exposes taxonomy categories; [`app/static/header.js`](./app/static/header.js) renders real localized labels/slugs. |
| T032 | Complete | Reusable card in [`app/static/product-card.js`](./app/static/product-card.js), formatter in [`app/static/money.js`](./app/static/money.js), styles, and [`PRODUCT-CARD.md`](./PRODUCT-CARD.md). |
| T033 | Complete | Accessible state components are in [`app/static/status-state.js`](./app/static/status-state.js) and [`app/static/status-state.css`](./app/static/status-state.css). |
| T034 | Complete | Responsive home layout and `[data-home-product-grid]` hook are in [`app/static/index.html`](./app/static/index.html) and [`app/static/site.css`](./app/static/site.css). |
| T035 | Complete | Home grid loads products from `GET /api/v1/catalog/products`, hydrates cart catalog state, and renders shared product cards with Romanian loading/empty/error states in [`app/static/home-catalog.js`](./app/static/home-catalog.js). The endpoint supports reusable `category_slug` and `q` filters in [`app/catalog/routes.py`](./app/catalog/routes.py). |
| T036 | Complete | Category page uses taxonomy/product APIs and shared cards/states; page hooks and assets are in [`app/static/category-listing.js`](./app/static/category-listing.js) and [`app/static/category-listing.css`](./app/static/category-listing.css). |
| T037 | Complete | `/search` renders API results and result counts; [`app/catalog/repository.py`](./app/catalog/repository.py) performs case/diacritic-insensitive Romanian matching. |
| T038 | Complete | Product detail API/page resolve stable slug or UUID and display price, stock, image, description, and recoverable states in [`app/static/product-detail.js`](./app/static/product-detail.js). |
| T039 | Complete | Home/category/search/detail adds use shared cart operations; full catalog hydration enforces stock limits and detail actions announce state. |
| T040 | Complete | Responsive cart page and line-item template with stable hooks are in [`app/static/index.html`](./app/static/index.html) and [`app/static/cart-page.css`](./app/static/cart-page.css). |
| T041 | Complete | [`app/static/cart-page.js`](./app/static/cart-page.js) validates quantities/stock, persists edits, recomputes totals, and blocks invalid checkout. |
| T042 | Complete | Empty cart now links to search and all four catalog categories; delivery copy says it is unconfigured in this prototype. Unavailable lines remain visible/editable because empty state is shown only when `state.lines.length === 0`. |
| T043 | Complete | [`app/static/account-page.js`](./app/static/account-page.js) renders safe profile/session state using only exposed name/email; the provider is not guessed. |
| T044 | Complete | `POST /api/v1/auth/logout` revokes the server session; account UI refreshes auth state, preserves cart, and returns to `/`. |
| T045 | Complete | [`app/static/route-guard.js`](./app/static/route-guard.js) hides protected content until auth resolves, preserves cart, and sends signed-out users through same-origin return allowlists including confirmation pages. |
| T046 | Complete | [`CHECKOUT-ADDRESS.md`](./CHECKOUT-ADDRESS.md) and `DeliveryAddress` define contact/address fields, county entry, phone rules, and required six-digit postal code; delivery notes are excluded. |
| T047 | Complete | [`app/static/checkout-details.js`](./app/static/checkout-details.js) renders validated Romanian contact/address fields, shows the account email as read-only, and stores a temporary address draft for review navigation. |
| T048 | Complete | Checkout shows the approved prototype-only simulated payment notice; no payment credentials or processor calls are present. |
| T049 | Complete | [`app/static/checkout-review.js`](./app/static/checkout-review.js) reviews current catalog/cart totals, delivery snapshot, account email, and the persistent simulated-payment notice. |
| T050 | Complete | T045 guards preserve `/checkout/details` as a same-origin return target for email/Google auth; anonymous cart remains in versioned localStorage through auth. |
| T051 | Complete | [`app/static/checkout-safeguards.js`](./app/static/checkout-safeguards.js) refreshes stock/prices, rejects empty/invalid/stale carts, preserves the address draft, and provides a duplicate-submit lock for T052. |
| T052 | Complete | [`app/static/checkout-review.js`](./app/static/checkout-review.js) submits the reviewed items and delivery address to the authenticated idempotent order API, preserves cart/address on failures, and clears them only after a valid created-order response. Retry keys are reused only for the same reviewed intent, recorded as a digest so delivery details are not stored in session storage. The repository flushes the order snapshot before its idempotency row to satisfy SQLite foreign keys; isolated end-to-end retry verification passed. |
| T053 | Complete | [`app/static/order-confirmation.js`](./app/static/order-confirmation.js) and owner-scoped `GET /api/v1/orders/{order_number}` render the saved order, delivery summary, date, total, and mock status. |
| T054 | Complete | [`app/static/orders-history.js`](./app/static/orders-history.js) and authenticated `GET /api/v1/orders` show newest-first order history with loading, empty, and error states. |
| T055 | Complete | [`app/static/order-detail.js`](./app/static/order-detail.js) renders owner-scoped immutable order snapshots, item and shipping totals, delivery address, registration date, and explicit mock payment status. |
| T056 | Complete | Checkout and order copy is consistently Romanian, uses centralized RON formatting, and clearly identifies simulated payment and demo orders. |
| T057 | Complete | Added narrow-screen spacing at 320–360px, 44px minimum utility/category/auth targets, larger cart quantity controls, and wrapping safeguards for order identifiers/content. |
| T058 | Complete | Improved cart control names and action announcements, restored keyboard focus after cart updates/removal, and strengthened visible focus indicators on checkout fields and the global focus token. |
| T059 | Complete | Verified that browser storage holds only the anonymous product/quantity cart, temporary checkout address, and a non-secret retry key/digest; no passwords, OAuth tokens, or payment credentials are stored. Successful logout now clears the address and retry draft while preserving cart. Order list/detail reads are authenticated and owner-scoped; OAuth values remain environment-only placeholders. Auth form load errors render as text instead of interpolated HTML. |
| T060 | Complete | Added [README.md](./README.md) with Python setup/install/run steps, runtime limitations, and local Google OAuth prerequisites; corrected [CONFIGURATION.md](./CONFIGURATION.md) to describe environment-variable loading accurately and updated package metadata to use the README. No real credentials included. |
| T061 | Complete | Added provider-neutral container/deployment configuration; provider-specific deploy remains deferred until a host is selected. |
| T062 | Complete | [`ACCEPTANCE-RESULTS.md`](./ACCEPTANCE-RESULTS.md) records the passing local route, auth/order API, idempotency, and narrow viewport checks. Google OAuth and hosted deployment are documented as external setup items; the full browser click-through was not automated. |

## Phase 0 — Product decisions and project foundation

### P0.1 — Confirm prototype boundaries

- **T001 — Freeze customer journey and exclusions.** Record browsing, product details, cart, required account, Romanian checkout, mock payment, order confirmation, and order history as the MVP boundary. Explicitly exclude vendors, real payments, shipping APIs, reviews, and admin.  
  **Depends on:** none. **Unblocks:** all product and architecture work.  
  **Output:** accepted scope aligned to `SPEC.md`.
- **T002 — Define user-visible meaning of “mock order.”** Choose concise Romanian wording for the payment label, confirmation state, and any notice that an order is a prototype record. Keep it understandable and visible before order confirmation.  
  **Depends on:** T001. **Unblocks:** T018, T048, T055.  
  **Output:** copy strings and display rules.
- **T003 — Confirm temporary brand treatment.** Use “Nexo Market” as the working name; keep brand text in one configuration/content location so it can be renamed without editing every page.  
  **Depends on:** T001. **Unblocks:** T008, T034, T056.  
  **Output:** one source of brand name and basic brand assets/tokens.

### P0.2 — Choose technical foundation

- **T004 — Inspect available runtime and package tooling.** Identify supported runtime versions, package manager availability, and whether the repository has any hidden project constraints.  
  **Depends on:** none. **Unblocks:** T005–T007.  
  **Output:** recorded environment findings.
- **T005 — Select application framework and language.** Choose a maintained web stack appropriate for a responsive storefront, accessible UI, and the available environment. Record the reason and minimum runtime version.  
  **Depends on:** T004. **Unblocks:** T006–T009.  
  **Output:** framework decision.
- **T006 — Select routing and rendering approach.** Define route strategy for storefront, product, authentication, cart, checkout, account, and confirmation pages. Decide client/server rendering based on selected stack.  
  **Depends on:** T005. **Unblocks:** T009, T034–T056.  
  **Output:** route map and navigation rules.
- **T007 — Select authentication and persistence services.** Choose the auth provider and the minimal persistence option for customer profile/order records. Document where cart state lives and how it is tied to a signed-in user. Do not place secrets or passwords in browser storage.  
  **Depends on:** T005. **Unblocks:** T019–T025, T050–T054.  
  **Output:** provider and data persistence decision.
- **T008 — Define design and component conventions.** Select typography, color tokens, spacing, buttons, inputs, alerts, cards, and responsive breakpoints. Keep a restrained retail visual system suitable for a mixed catalog.  
  **Depends on:** T003, T005. **Unblocks:** T010, T034–T056.  
  **Output:** token and component plan.
- **T009 — Define environment configuration and secret handling.** List public runtime configuration separately from private server configuration; provide an example environment file with placeholders only. Document local setup and which values must never be committed.  
  **Depends on:** T005, T007. **Unblocks:** T011, T020, T024, T060.  
  **Output:** configuration contract and setup notes.
- **T010 — Bootstrap the application shell.** Create the framework project, scripts, source structure, global styles entry, and base document metadata. Avoid adding optional infrastructure outside selected stack needs.  
  **Depends on:** T005, T008. **Unblocks:** T011–T018, T034 onward.  
  **Output:** runnable empty application shell.
- **T011 — Establish route skeleton and shared layout.** Add route placeholders, page frame, header/footer slots, and not-found behavior according to T006.  
  **Depends on:** T006, T010. **Unblocks:** T034–T056.  
  **Output:** navigable empty route structure.
- **T012 — Define core domain types.** Specify product, category, cart line, customer profile, Romanian delivery address, payment mock state, and order shapes. Use stable identifiers and avoid mixing display text with domain values.  
  **Depends on:** T001, T007. **Unblocks:** T013–T018, T026–T033, T040–T054.  
  **Output:** shared domain schema/types.
- **T013 — Define money and locale rules.** Define RON storage/display rules, minor-unit arithmetic, Romanian number formatting, and rounding behavior. All totals must use one shared implementation.  
  **Depends on:** T001, T012. **Unblocks:** T015–T018, T026–T033, T042–T054.  
  **Output:** money rules and shared formatting contract.
- **T014 — Define category taxonomy and product attributes.** Choose a small seed taxonomy such as electronics, home, fashion, and personal care. Record required product fields, image ratio, availability values, and optional category-specific metadata.  
  **Depends on:** T001, T012. **Unblocks:** T015, T035–T039.  
  **Output:** catalog field and category schema.
- **T015 — Create sample catalog dataset.** Add a small but representative, realistic Romanian-language catalog with category, title, description, RON price, image reference, and availability for each item. Use images with appropriate usage rights or stable project-owned assets.  
  **Depends on:** T013, T014. **Unblocks:** T016, T035–T039.  
  **Output:** seed data with all required product fields.
- **T016 — Implement catalog data access boundary.** Expose typed product/category reads from the seed source so UI components do not hard-code catalog data. Keep a later data-source replacement localized.  
  **Depends on:** T012, T014, T015. **Unblocks:** T035–T039.  
  **Output:** catalog access module/API.
- **T017 — Define cart calculation contract.** Specify line identity, quantity limits, handling for unavailable products, subtotal, delivery display (if any), and final total. Do not invent shipping charges absent from the product decision.  
  **Depends on:** T012, T013, T014. **Unblocks:** T026–T033, T040–T047.  
  **Output:** cart rules shared by UI and order creation.
- **T018 — Define order lifecycle and order number strategy.** Specify initial prototype status, mock payment label/status, immutable order item/price snapshots, timestamp format, and unique human-readable order number strategy.  
  **Depends on:** T002, T012, T013, T017. **Unblocks:** T028, T030–T033, T050–T055.  
  **Output:** order lifecycle contract.
- **T018a — Align domain enums and required delivery fields with the finalized contracts.** Replace ambiguous pending/completed/card/cash states with the agreed `registered` order status and `simulated` / `not_processed` mock payment semantics. Make the Romanian postal code required and preserve the existing API/domain boundaries.  
  **Depends on:** T012, T018. **Unblocks:** T028–T029, T046–T055.  
  **Output:** domain models that cannot represent a misleading paid/completed order and require the agreed delivery address fields.

## Phase 1 — Authentication and persistence foundations

- **T019 — Create auth provider project/application configuration.** Set up the selected provider project, identify allowed local origins, and document callback/redirect requirements.  
  **Depends on:** T007, T009. **Unblocks:** T020–T025.  
  **Output:** provider-side project setup instructions/identifiers.
- **T020 — Add auth provider client initialization.** Initialize the SDK or auth client from environment config; handle missing configuration without crashing unrelated storefront pages.  
  **Depends on:** T009, T019. **Unblocks:** T021–T025, T050.  
  **Output:** shared initialized auth client.
- **T020a — Create the SQLite persistence substrate for auth.** Add SQLAlchemy engine/session wiring, declarative base, SQLite foreign-key setup, and minimal user, password credential, OAuth identity, and opaque-session tables. Keep schema creation local-prototype-safe and leave order tables to T028.  
  **Depends on:** T007, T010, T019. **Unblocks:** T021–T025, T028.  
  **Output:** initialized database access and auth/session ORM records.
- **T021 — Implement auth state provider.** Load the current session, expose signed-in user/loading/error state, and subscribe to provider changes. Avoid UI flicker by providing an explicit loading state.  
  **Depends on:** T020, T020a, T012. **Unblocks:** T022–T025, T041, T050–T054.  
  **Output:** application-wide auth state interface.
- **T022 — Implement registration form UI.** Add Romanian fields, password confirmation if selected, required-field validation, accessible labels, and provider error display.  
  **Depends on:** T008, T011, T021. **Unblocks:** T024, T041.  
  **Output:** registration page/form.
- **T023 — Implement email sign-in form UI.** Add email/password inputs, validation, error feedback, and links to registration.  
  **Depends on:** T008, T011, T021. **Unblocks:** T024, T041.  
  **Output:** sign-in page/form.
- **T024 — Connect email registration and sign-in actions.** Submit forms to provider, map provider errors into safe Romanian messages, and transition to the correct post-auth destination.  
  **Depends on:** T020–T023. **Unblocks:** T025, T041, T050.  
  **Output:** functional email/password account flow.
- **T025 — Implement Google sign-in action and callback handling.** Add Google button, initiate provider OAuth, handle return/cancel/failure, and restore destination after authentication. Keep client IDs in configuration, never source code.  
  **Depends on:** T019–T021, T009, T006. **Unblocks:** T041, T050.  
  **Output:** real Google OAuth flow ready for configured credentials.  
  **External gate:** live flow cannot be exercised until OAuth client values and allowed origin/callback URLs are supplied and registered.
- **T026 — Implement cart state model and persistence.** Add, update, remove, clear, and hydrate cart lines with validation against catalog IDs. Define anonymous cart persistence and merge/retain behavior when a user signs in.  
  **Depends on:** T012, T013, T016, T017. **Unblocks:** T027–T029, T035, T038–T047.  
  **Output:** shared cart state operations.
- **T027 — Handle cart reconciliation on sign-in.** Preserve the shopper's current cart through the auth redirect and merge or retain it deterministically after registration, email sign-in, or Google sign-in.  
  **Depends on:** T021, T025, T026. **Unblocks:** T041, T050.  
  **Output:** no cart loss across auth transitions.
- **T028 — Implement order persistence boundary.** Create the minimal create/read operations for an authenticated customer's prototype orders using the selected persistence service. Enforce customer ownership on reads.  
  **Depends on:** T007, T012, T018, T018a, T019. **Unblocks:** T030–T033, T050–T055.  
  **Output:** order storage adapter/API and ownership rules.
- **T029 — Implement order creation service.** Validate current product references and quantities, calculate totals with shared money/cart rules, snapshot product name/price, assign order number/time, set mock payment state, and persist exactly once per confirmation action.  
  **Depends on:** T013, T016–T018a, T028. **Unblocks:** T031–T033, T049–T055.  
  **Output:** order creation operation with a stable response.
- **T029a — Wire order creation into application startup and make retries idempotent.** Register order routes before API fallback routes, import order ORM models before metadata creation, and persist an owner-scoped idempotency key so a retried confirmation returns the original order rather than creating a duplicate.  
  **Depends on:** T011, T028, T029. **Unblocks:** T049–T055.  
  **Output:** reachable order API, initialized order schema, and replay-safe confirmation contract.

## Phase 2 — Shared storefront interface

- **T030 — Build responsive site header.** Add brand link, category entry point, search entry, account entry, and cart count; make controls keyboard accessible.  
  **Depends on:** T003, T008, T011, T021, T026. **Unblocks:** T034–T039, T056.  
  **Output:** shared header that reflects auth and cart state.
- **T031 — Build category navigation.** Render taxonomy from catalog data and support desktop and compact/mobile navigation patterns.  
  **Depends on:** T014, T016, T030. **Unblocks:** T035–T037.  
  **Output:** reusable category navigation.
- **T032 — Build shared product card.** Display image, Romanian title, formatted RON price, availability, and add-to-cart control with loading/success feedback.  
  **Depends on:** T008, T013–T017, T026. **Unblocks:** T035, T037, T039.  
  **Output:** reusable catalog card.
- **T033 — Build shared empty/loading/error states.** Create consistent Romanian states for empty results, unavailable catalog data, and pending operations.  
  **Depends on:** T008, T011. **Unblocks:** T034–T056.  
  **Output:** reusable status/empty state components.
- **T034 — Build storefront landing page layout.** Compose header, discovery content, category links, a product section, and responsive footer using the chosen design tokens.  
  **Depends on:** T008, T011, T030–T033. **Unblocks:** T035–T039.  
  **Output:** responsive storefront page shell.
- **T035 — Render initial mixed-catalog product section.** Load products via the catalog boundary and display product cards with appropriate empty/loading states.  
  **Depends on:** T015, T016, T032–T034. **Unblocks:** T037–T039.  
  **Output:** discoverable sample product grid.
- **T036 — Implement category listing route.** Route from category navigation to a category-specific grid; handle unknown/empty categories gracefully.  
  **Depends on:** T006, T014, T016, T031–T033. **Unblocks:** T037, T039.  
  **Output:** working category listing experience.
- **T037 — Implement search behavior.** Search product names (and optionally descriptions if agreed), normalize case/diacritics appropriately for Romanian, and show matching count/empty state.  
  **Depends on:** T016, T030, T032–T035. **Unblocks:** T056.  
  **Output:** functional catalog search.
- **T038 — Implement product detail route.** Load a product by stable ID/slug, show image, description, availability, price, and not-found state.  
  **Depends on:** T006, T013–T016, T033. **Unblocks:** T039.  
  **Output:** product detail page.
- **T039 — Connect add-to-cart from listings and detail.** Use the shared cart operation, give feedback, and ensure repeated clicks update quantity according to cart rules.  
  **Depends on:** T026, T032, T035–T038. **Unblocks:** T040–T047.  
  **Output:** product discovery-to-cart interaction.

## Phase 3 — Cart and account experiences

- **T040 — Build cart page layout.** Show line items, quantity controls, remove action, subtotal, total, continue shopping, and checkout entry.  
  **Depends on:** T008, T011, T013, T017, T026, T030. **Unblocks:** T041–T047.  
  **Output:** responsive cart page.
- **T041 — Implement cart quantity and removal interactions.** Validate minimum/maximum quantity, reflect unavailable product state, recalculate totals, and persist after each state change.  
  **Depends on:** T017, T026, T039, T040. **Unblocks:** T042–T047.  
  **Output:** reliable cart editing.
- **T042 — Implement cart empty state and recovery links.** Explain that the cart is empty in Romanian and link back to catalog/categories.  
  **Depends on:** T033, T040. **Unblocks:** T056.  
  **Output:** useful empty-cart experience.
- **T043 — Build account profile page.** Show provider-backed basic profile information, account state, and sign-out action. Do not show sensitive auth tokens.  
  **Depends on:** T011, T021, T024. **Unblocks:** T044, T050.  
  **Output:** account profile view.
- **T044 — Implement sign-out.** Call provider sign-out, clear auth-only UI state, preserve anonymous cart according to T026, and navigate to a safe public route.  
  **Depends on:** T021, T024, T026, T043. **Unblocks:** consistent auth lifecycle across the site.
- **T045 — Add route guard for checkout and account pages.** Redirect unauthenticated customers to sign-in with a return destination, preserve cart, and render loading state while auth is unresolved. Account pages must never flash another user's data.  
  **Depends on:** T006, T021, T027. **Unblocks:** T046–T055.  
  **Output:** authenticated-route behavior.

## Phase 4 — Checkout and mock order flow

- **T046 — Define checkout form and address schema.** Specify required contact and delivery fields for Romania, county/județ options or entry format, city, street/address details, and postal code. Decide field validation and whether delivery notes are included.  
  **Depends on:** T001, T012, T013. **Unblocks:** T047–T049.  
  **Output:** stable checkout form contract.
- **T047 — Build checkout contact/address step.** Render validated Romanian contact and delivery fields, preserve typed values during navigation, and explain errors inline.  
  **Depends on:** T008, T011, T045, T046. **Unblocks:** T048–T050.  
  **Output:** responsive checkout details form.
- **T048 — Build mock payment choice/notice.** Show the agreed mock-only payment label and clear prototype notice. Do not render any card credential inputs or call a payment provider.  
  **Depends on:** T002, T008, T011, T047. **Unblocks:** T049.  
  **Output:** explicit non-transactional payment step.
- **T049 — Build order review step.** Summarize products, quantities, item price snapshots, total, contact/address, and mock payment state. Provide a way to return and edit earlier checkout fields.  
  **Depends on:** T013, T017, T018, T029, T047, T048. **Unblocks:** T050.  
  **Output:** final review interface.
- **T050 — Implement checkout auth redirect and return.** Starting checkout while signed out sends the shopper to sign-in/registration and restores the intended checkout route and cart after successful email or Google authentication.  
  **Depends on:** T024, T025, T027, T045, T047. **Unblocks:** T051–T055.  
  **Output:** uninterrupted authenticated checkout entry.
- **T051 — Implement checkout submission safeguards.** Disable duplicate submit while pending, reject empty/invalid carts, re-evaluate current catalog availability and totals, and show recoverable errors without discarding entered data.  
  **Depends on:** T016–T018, T029, T041, T047–T049. **Unblocks:** T052.  
  **Output:** guarded confirmation action.
- **T052 — Connect confirmation to order creation.** Submit the final reviewed snapshot to the order creation service, handle persistence failures, and clear the cart only after the order is successfully created.  
  **Depends on:** T028, T029, T049, T051. **Unblocks:** T053–T055.  
  **Output:** successful mock-order creation flow. ✅ Complete
- **T053 — Build order confirmation page.** Show order number, creation time, ordered items, total, address summary, and explicit mock payment/order status. Offer account/order-history and continue-shopping links.  
  **Depends on:** T002, T006, T018, T029, T052. **Unblocks:** T055.  
  **Output:** confirmation route using the created order record. ✅ Complete
- **T054 — Build account order history list.** Load only current customer's orders, sort newest first, and show order number, date, total, and prototype status. Handle loading, empty, and error states.  
  **Depends on:** T018, T028, T033, T043, T045. **Unblocks:** T055.  
  **Output:** account order list. ✅ Complete
- **T055 — Build order detail view.** Let a signed-in owner open an order and see saved item snapshots, totals, address, created date, and mock payment status. Reject access to orders owned by other accounts.  
  **Depends on:** T018, T028, T033, T045, T053, T054. **Unblocks:** complete account-to-order journey.
  **Output:** owner-scoped order detail page. ✅ Complete

## Phase 5 — Fit, content, and release readiness

- **T056 — Apply Romanian copy and localization consistently.** Review navigation, forms, validation, errors, empty states, order/payment labels, dates, quantities, and money formatting. Keep locale rules centralized.  
  **Depends on:** T002, T003, T013, T030–T055. **Unblocks:** release review.  
  **Output:** consistent Romanian-language MVP.
- **T057 — Refine responsive behavior across key routes.** Check storefront, category, product, cart, auth, checkout, confirmation, account, and order detail layouts at narrow and wide viewports; correct overflow and tap-target issues.  
  **Depends on:** T034–T055. **Unblocks:** release review.  
  **Output:** usable mobile and desktop layouts.
- **T058 — Review accessibility and form usability.** Ensure semantic headings, keyboard operation, visible focus, accessible names, error associations, adequate contrast, and status announcements for cart/auth/checkout actions.  
  **Depends on:** T008, T030–T055. **Unblocks:** release review.  
  **Output:** accessible core journey.
- **T059 — Review privacy and security boundaries.** Confirm no passwords, OAuth tokens, or payment credentials are written to app storage; verify auth-protected order reads and safe error output. Confirm OAuth configuration is not committed.  
  **Depends on:** T009, T020–T029, T045, T048–T055. **Unblocks:** deployment configuration.  
  **Output:** documented boundary review and any fixes.
- **T060 — Prepare local setup and configuration documentation.** Document prerequisites, install/run commands, environment placeholders, auth-provider setup, Google callback/origin registration, and known prototype limitations. Never include real credentials.  
  **Depends on:** T004, T009, T019, T025, T028. **Unblocks:** another developer can run/configure the project.
- **T061 — Prepare deployment configuration. COMPLETE (provider-neutral).** Added `Dockerfile`, `compose.yaml`, and `.dockerignore`; documented server-only environment variables, same-origin hosting, assigned port, HTTPS cookie settings, durable storage, secret handling, and production Google origin/callback registration in `CONFIGURATION.md`. No hosting provider, external account, credentials, or deployment were selected or changed. Map host-specific build settings, health checks, storage, and secret injection after a provider is chosen.  
  **Depends on:** T005, T007, T009, T019, T025, T060. **Unblocks:** host-specific deployable preview after provider selection.
- **T062 — Perform end-to-end acceptance walkthrough. COMPLETE for locally testable MVP scope.** [`ACCEPTANCE-RESULTS.md`](./ACCEPTANCE-RESULTS.md) records the configured local route and API acceptance checks, narrow viewport result, the SQLite ordering issue found and fixed, and the untested external Google OAuth/hosted deployment paths.  
  **Depends on:** T034–T061; live Google scenario additionally depends on valid OAuth values. **Unblocks:** MVP handoff.  
  **Output:** acceptance notes and resolved blocking defects.

## How the work affects other work

| Upstream decision/task | Directly affected work | Effect of changing it later |
|---|---|---|
| T005–T007: framework, routes, provider, persistence | Almost all implementation tasks | Changes setup, SDK integration, data access, auth state, and route behavior; decide before feature work. |
| T012–T018: domain, money, catalog, cart, order contracts | T015–T018, T026–T029, T032, T035–T055 | Shape changes ripple into UI props, persistence records, totals, confirmation, and order history. Freeze these contracts early. |
| T013: RON arithmetic/formatting | Cards, cart, review, order records, account history | If amounts are stored as floating-point or formatted inconsistently, totals can disagree across checkout and order detail. All screens should call the same money helpers. |
| T014–T016: catalog schema/data access | Search, categories, cards, details, cart, order snapshots | Renaming fields/categories affects product displays and historical item snapshots; persist order snapshots so later catalog edits do not rewrite orders. |
| T017/T026: cart rules/state | Header badge, cart, auth redirects, review, order creation | Changes to merge behavior, quantity rules, or unavailable items can alter checkout eligibility and totals. Share one cart model across all screens. |
| T019–T025: provider configuration and auth | Account UI, route guards, checkout return, Google sign-in | Provider/callback changes can break both sign-in and checkout return. Google cannot be truly exercised until external client settings are supplied. |
| T028–T029: order storage and creation | Review submission, confirmation, order history/detail | Order record shape and duplicate-submit behavior must be settled before confirmation or history UI is finalized. |
| T002/T048: mock payment wording/state | Checkout review, order record, confirmation, history | Label/status changes need to remain consistent through every point where an order appears and must never imply a real charge. |
| T046: address schema | Checkout form, review, saved order, confirmation/detail | Adding/removing fields changes validation and persisted order addresses; update all summaries with the same address type. |
| T008 and T030–T033: design/shared components | Every page | Shared token/component changes improve consistency globally but can affect spacing and responsive layouts on all routes. |
| T050–T052: checkout transition and commit behavior | Auth return, cart retention, order creation, confirmation | Clearing cart before persistence risks losing items; redirecting without a return target strands users. Keep the sequence: authenticate → review → persist order → clear cart → confirmation. |
| T056–T058: locale, responsiveness, accessibility | Entire customer journey | These are cross-cutting; late changes may require revisiting every route, form, validation message, and status state. |

## Critical path

`T004 → T005 → T006/T007/T008 → T009/T010 → T011/T012 → T013/T014/T017/T018 → T019–T029 → T030–T045 → T046–T055 → T056–T062`

Some content and layout work can proceed in parallel after the shared contracts are agreed. The longest externally dependent path is:

`T007 → T009 → T019 → T025 → provide/register Google OAuth configuration → T050 → T062`

The app can be implemented with the Google integration in place before credentials arrive, but the real Google sign-in acceptance path remains blocked until the provider values and allowed callback/origin settings are configured.

## Acceptance walkthrough mapped to tasks

1. Open storefront and browse mixed sample products: T014–T016, T030–T035.
2. Search and filter categories: T031, T036–T037.
3. Open details and add a product: T032, T038–T039.
4. Change quantity/remove items and preserve cart: T017, T026–T027, T040–T042.
5. Register and sign in with email; sign out: T020–T024, T043–T045.
6. Sign in through Google with valid configuration: T019–T021, T025, T060–T062.
7. Start checkout signed out and return without losing cart: T027, T045, T050.
8. Enter and validate Romanian delivery details: T046–T047.
9. Select mock payment and review the total/order: T013, T017–T018, T048–T051.
10. Confirm once, persist the order, and display confirmation: T028–T029, T051–T053.
11. Reopen account and view order history/detail: T028, T043, T054–T055.
12. Confirm Romanian copy, responsive fit, accessibility, and safe data handling: T056–T062.

## Completion definition

The MVP is ready for handoff when the storefront-to-order journey is complete, the account can access only its own prototype orders, cart and totals remain coherent across auth redirects, mock payment is visibly non-transactional, the site works on mobile and desktop, Romanian locale is consistent, setup/configuration is documented, and the Google OAuth limitation is clearly recorded or valid configuration has been provided.
