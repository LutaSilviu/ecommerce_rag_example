# Nexo Market — Route and Navigation Plan

**Decision for T006:** Use clean, same-origin browser URLs served by FastAPI. The customer UI is build-free vanilla HTML, CSS, and JavaScript; pages call the `/api/v1/` JSON API with `fetch`. This is a multi-page route plan, not a client-side single-page router. FastAPI serves the corresponding HTML page (or shared page shell where appropriate) and static assets. No frontend framework or compilation step is introduced.

## Customer-facing URL map

| URL | Page and purpose | Access | Main navigation/actions |
|---|---|---|---|
| `/` | Storefront: discovery content, featured products, category links, and search entry | Public | Brand link returns here; category/product cards open their routes; search submits to `/search?q=…`; header links to account, cart, and categories. |
| `/category/{category_slug}` | Product listing filtered to a known category slug, such as `/category/electronice` | Public | Category navigation links here; product cards open product details; search remains available. Unknown slugs show a Romanian not-found/empty state with a link to the catalog. |
| `/search?q={term}` | Search results for the URL-encoded query; category filter may be represented by optional `category={slug}` | Public | Search form submits with GET so the query is shareable and survives refresh; result cards open products; clear-search returns to `/search` or `/`. |
| `/product/{product_slug}` | Product detail: images, description, price, availability, and add-to-cart | Public | Breadcrumb/category links lead back to listings; add-to-cart updates shared cart state and provides a cart link. |
| `/cart` | Cart review and quantity/remove controls, with totals and checkout action | Public | Continue shopping returns to `/` or previous catalog location; checkout action navigates to `/checkout/details` and preserves cart. Empty cart links to storefront. |
| `/register` | Email/password account creation and Google sign-up entry point | Public when signed out | Link to `/login`; after success return to validated `return_to`, otherwise default `/account`. If already signed in, redirect to validated `return_to` or `/account`. |
| `/login` | Email/password sign-in and Google sign-in entry point | Public when signed out | Link to `/register`; after success return to validated `return_to`, otherwise default `/account`. If already signed in, redirect to validated `return_to` or `/account`. |
| `/account` | Basic signed-in profile and links to order history | Authenticated | Links to `/account/orders`; sign-out returns to `/`. Unauthenticated visitors are sent to `/login` with `return_to=/account`. |
| `/checkout/details` | Contact and Romanian delivery-address form (including county, locality, street, postal code) | Authenticated; cart must contain purchasable items | Continue validates and saves checkout details for this flow, then navigates to `/checkout/review`. Signed-out visitors go to `/login?return_to=%2Fcheckout%2Fdetails`. Empty carts return to `/cart`. |
| `/checkout/review` | Final item, address, total, and clearly labeled mock-payment review | Authenticated; valid checkout details and non-empty cart required | Back returns to `/checkout/details`; edit cart returns to `/cart`; confirmation submits once and, on success, navigates to the order confirmation URL. Missing prerequisites redirect to the appropriate earlier step. |
| `/checkout/confirmation/{order_number}` | Confirmation for the newly created mock order | Authenticated owner of the order | Links to order detail/history and continue shopping (`/`). Direct refresh is supported by loading the persisted order; invalid or non-owned order numbers receive a not-found response/state. |
| `/account/orders` | Newest-first order history for the signed-in customer | Authenticated | Each order links to its detail route. Empty state links to storefront. Signed-out visitors go to `/login?return_to=%2Faccount%2Forders`. |
| `/account/orders/{order_number}` | Saved order detail with item/price snapshots, totals, delivery summary, date, and mock status | Authenticated owner of the order | Back link to `/account/orders`; order data is read from persisted order record, not reconstructed from current catalog. |

The route segments are stable identifiers/slugs, not localized display labels. Customer-visible titles and navigation text remain Romanian. Product/category slugs and order numbers must be URL-safe; missing or unknown resources use a Romanian not-found state and must not disclose whether another customer's order exists.

## Navigation and state rules

- The shared header appears on storefront, category, search, product, cart, and account browsing pages. It exposes storefront, category navigation, search, account/sign-in, and cart with current item count. Checkout may use a reduced header while retaining a clear path back to cart.
- Catalog navigation uses ordinary links and GET search URLs. Add-to-cart and quantity changes use JavaScript/API actions without requiring a full page navigation; updated cart state is reflected in the header and after refresh.
- The cart is available to anonymous shoppers. Sign-in must not discard or silently replace it; reconciliation follows T026–T027. Starting checkout while signed out preserves the cart through authentication.
- `return_to` is a local path, never an arbitrary URL. Login/register and OAuth completion accept only a validated same-origin path beginning with one `/`, reject protocol-relative paths (`//…`), schemes, backslashes, and paths outside the supported customer route set, and fall back to `/account` when absent or invalid.
- The checkout return target is `/checkout/details`. On successful authentication, restore that target and the cart, then continue through details and review. For account-only access, return to the requested account route. Do not use a user-controlled return target as an OAuth redirect URI; the provider callback remains a configured fixed callback and the validated app path is carried through protected state/session data.
- After order creation succeeds, clear the cart and navigate to `/checkout/confirmation/{order_number}`. If order creation fails, keep the cart and review data so the shopper can retry. Confirmation refresh loads the persisted order rather than submitting again.
- Browser Back should move between normal pages and checkout steps without losing cart contents. Unsaved checkout form data should be retained for the current flow according to the persistence choice in T007; credentials and OAuth tokens must not be put in browser storage.

## Route guards and redirect behavior

1. Public pages (`/`, category, search, product, cart, register, and login) render without an authenticated session.
2. Protected pages (`/account`, checkout details/review, confirmation, order history, and order detail) wait for auth state to resolve before rendering protected data. While auth state is loading, show a neutral loading state rather than briefly exposing protected content.
3. When a visitor opens a protected route unauthenticated, redirect to `/login?return_to=<encoded-local-path>`. Registration remains available from the login page and must preserve the same validated return path.
4. Checkout routes additionally require a non-empty, valid cart. `/checkout/review` requires valid details saved by the preceding step. Redirect to `/cart` or `/checkout/details` respectively when those prerequisites are missing.
5. The backend enforces order ownership for confirmation and order-detail reads. Frontend route guards improve navigation only and are not an authorization boundary.
6. A stale/expired session encountered during a protected API request returns the shopper to login with the current supported path as `return_to`; after reauthentication the original cart and safe path are restored.

## FastAPI page/API boundary

- FastAPI serves customer HTML routes and static assets from the chosen static directory. Since the frontend has no build step or client router, each listed browser path must resolve directly on refresh/deep link; route handlers may serve distinct HTML files or a shared shell with page selection, as settled during T010–T011.
- JSON endpoints use the same origin under `/api/v1/` and are separate from browser page URLs. Keep page handlers focused on serving pages; API handlers own catalog reads, auth integration, cart/order operations, validation, and ownership checks.
- FastAPI's development `/docs` is for API inspection and is not a customer navigation destination.
- T007 may alter the auth/session mechanism and where checkout draft/cart state lives, but should preserve these customer URLs and observable redirect rules unless this route contract is explicitly revised.

## Dependency and change impact

T006 depends on the FastAPI + vanilla HTML/CSS/JS decision in T005. T011 uses this map to build the route skeleton and shared layout. Authentication tasks T021–T027 and T043–T045 depend on the public/protected distinction and safe `return_to` behavior. Catalog tasks T034–T039 use the storefront, category, search, and product routes. Cart tasks T040–T042 use `/cart`; checkout tasks T046–T052 depend on the ordered details → review → create sequence; T053–T055 depend on confirmation, order history, and detail URLs plus server-side ownership checks.

Changing a path after implementation affects header links, product/category links, browser bookmarks, OAuth return restoration, redirect tests/manual acceptance, and cross-links in confirmation and account pages. Changing a guard or checkout redirect affects cart preservation and can strand shoppers in the authentication flow. Keep route constants/links centralized in frontend navigation helpers where practical, and mirror authorization in backend API checks.
