# Nexo Market — T007 Authentication and Persistence Decision

**Status:** Selected for the local FastAPI + vanilla HTML/CSS/JavaScript prototype.

## Decision

Use a small, same-origin FastAPI application with:

- **SQLite** for application-owned accounts, OAuth identities, server sessions, and mock orders.
- **SQLAlchemy 2.x** as the database access layer, using its synchronous API for this low-volume prototype. Keep persistence behind repositories/services so SQLite can be replaced later.
- **Email/password authentication owned by the application.** Hash passwords with `pwdlib[argon2]`; never store plaintext passwords or reversible password values.
- **Google OpenID Connect sign-in through Authlib** (`authlib` Starlette integration), using the authorization-code flow and server-side client secret. Google is an additional identity linked to a local user; Google access/ID tokens are used only to complete sign-in and are not retained as application credentials.
- **Opaque server-side sessions** in SQLite. Give the browser a cryptographically random session identifier in an `HttpOnly` cookie; store only a cryptographic hash of that identifier in the session table. This supports persistent sign-in and server-side revocation on sign-out.
- **Anonymous cart in `localStorage`**, containing product identifiers and quantities only. The cart is not an authentication mechanism and is not synchronized between browsers/devices. Its contents survive sign-in redirects in the same browser. Do not put passwords, session identifiers, OAuth state/tokens, or other credentials in `localStorage` or `sessionStorage`.
- **Orders in SQLite, owned by the authenticated user.** Each order stores immutable item/price snapshots and delivery details. Reads and writes derive the owner from the validated server session, never from a client-supplied user ID.

This is intentionally a modest local prototype architecture. It avoids requiring a hosted auth/database service or cross-origin setup, while allowing real password and Google sign-in. It is not a claim that a single local SQLite file is ready for horizontally scaled production hosting.

## Packages and patterns

Add these backend dependencies during project bootstrap (T010); this decision does not install them:

| Package | Use |
|---|---|
| `sqlalchemy>=2,<3` | ORM, SQLite engine, unit-of-work/transaction boundaries |
| `pwdlib[argon2]` | Argon2 password hashing and verification |
| `authlib` | Google OAuth/OIDC authorization-code flow and ID-token validation |
| `itsdangerous` | Optional signing of short-lived OAuth flow state if Authlib's session integration requires a signer; never use it as a substitute for revocable login sessions |

FastAPI already brings Starlette and Pydantic. Use FastAPI dependency injection for `get_current_user`, which validates the cookie session, checks expiry/revocation, and loads the account. Use SQLAlchemy sessions per request and explicit transactions for order creation. Keep auth and persistence modules separate from route handlers and static page code.

### Minimal records

- `users`: `id` (UUID/string primary key), normalized unique `email`, display name, created timestamp, active flag.
- `password_credentials`: `user_id` unique foreign key, `password_hash`, changed timestamp. A Google-only user can have no password credential.
- `oauth_identities`: `id`, `user_id`, provider (`google`), provider subject (`sub`), provider email at sign-in, created timestamp; unique constraint on `(provider, provider_subject)`. Do not use a mutable email address as the durable Google identity key.
- `sessions`: `id`, `user_id`, unique `token_hash`, created/last-seen/expiry timestamps, revoked timestamp. Store no raw bearer token.
- `orders`: `id`, unique human-readable order number, `user_id`, created timestamp, prototype order/payment status, totals in integer bani, and a snapshot of recipient/address fields.
- `order_items`: `order_id`, product ID/reference, product name and image snapshot, unit price in bani, quantity, and line total in bani.

Use database constraints for unique normalized email, unique Google subject per provider, foreign keys, and unique order number. Store money as integer bani; do not use floating point. Product/catalog data can remain a seed/static source as defined in later catalog tasks; order snapshots preserve what the customer confirmed if that catalog changes.

## Sign-in and session lifecycle

### Email/password

1. Registration validates and normalizes email, validates the password policy, hashes the password with Argon2, and creates the user and password credential in one transaction.
2. Sign-in looks up the normalized email and verifies the hash. Return a generic failure for unknown email and wrong password to avoid account enumeration.
3. On successful registration/sign-in, issue a fresh random session ID, persist only its SHA-256 hash, and set the opaque ID in the cookie. Rotate/revoke any prior session as appropriate.
4. Sign-out revokes the server-side session and expires the cookie. A copied/replayed old cookie then fails validation.

### Google OAuth

1. Redirect to Google using the configured client ID, exact callback URL, `openid email profile` scopes, and authorization-code flow. Use and validate OAuth `state` (and OIDC `nonce` where supported).
2. On callback, Authlib validates the response/ID token; require a verified email and use Google `sub` as the identity key.
3. Find an existing `(google, sub)` identity or create a local user and identity. If the verified email already belongs to a password user, do not silently merge identities based on email alone; require the user to sign in to that account and explicitly link Google in a later account-linking flow. For this MVP, report a clear sign-in conflict and keep the accounts separate until a safe linking path is implemented.
4. Issue the same kind of opaque local session cookie as email/password. Do not retain Google tokens after callback.

## Cookie, browser, and request protections

Set the cookie with `HttpOnly`, `SameSite=Lax`, `Path=/`, and `Secure` in HTTPS environments. Use a configurable cookie name and session lifetime; clear it on sign-out. Because the UI and API share one origin, do not enable permissive CORS. For state-changing authenticated requests, require a same-origin `Origin` (or `Referer` fallback) and a custom CSRF header/token; reject cross-origin mutation requests. OAuth callback is the intentional cross-site navigation and is protected by OAuth state/nonce rather than the app's ordinary mutation check.

Never expose password hashes, raw session IDs, OAuth tokens, or secrets in API responses or logs. A frontend auth status endpoint may return only safe profile fields. Browser JavaScript sends cookies automatically for same-origin `fetch`; it cannot read the `HttpOnly` session cookie.

## Order ownership and checkout integrity

- Every account/order endpoint requires `get_current_user`.
- Order list queries include `WHERE orders.user_id = current_user.id`; order detail lookup includes both order identifier and owner ID. Return not-found for another user's order rather than revealing its existence.
- Order creation ignores any `user_id` supplied by the browser and assigns the owner from the session. Recalculate price, availability, and totals from server catalog data; treat the submitted cart and displayed total as untrusted.
- Insert the order and item snapshots atomically. Clear browser cart only after the API confirms the transaction committed. A failed insert leaves the cart intact.
- No card data or payment processor is involved. Persist only the selected mock payment label/status required by the prototype.

## Configuration contract

Private server settings (names for T009/T019 to implement consistently):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL; local default may be `sqlite:///./data/nexo-market.db` |
| `SESSION_SECRET` | High-entropy secret for OAuth/session-related signing where required; required outside an explicitly local development default |
| `SESSION_COOKIE_NAME` | Cookie name, e.g. `nexo_session` |
| `SESSION_MAX_AGE_SECONDS` | Server-side session expiry |
| `SESSION_COOKIE_SECURE` | Set `true` in HTTPS/deployed environments; may be `false` only for local HTTP development |
| `GOOGLE_CLIENT_ID` | Public OAuth client identifier used by the backend redirect |
| `GOOGLE_CLIENT_SECRET` | Private OAuth client secret; never expose to browser or commit |
| `GOOGLE_REDIRECT_URI` | Exact registered callback, e.g. `http://localhost:8000/api/v1/auth/google/callback` locally |
| `APP_BASE_URL` | Canonical same-origin URL for safe post-auth redirects |

Add placeholders only to `.env.example`; keep actual `.env`, database files, and secrets out of version control. Validate required Google variables at startup or disable the Google button with a clear Romanian explanation when they are absent. Never use arbitrary user-provided `return_to` URLs; accept only known same-origin application paths.

## Local persistence and tradeoffs

SQLite is easy to run and inspect locally, requires no separate service, and is adequate for a single-process prototype. Enable foreign keys and use a single-writer-friendly transaction pattern. Add schema migrations (Alembic) when bootstrap establishes the migration workflow; for the earliest local iteration, a deterministic `create_all` bootstrap is acceptable only if later schema evolution is handled explicitly.

The tradeoff is that SQLite on one local disk does not provide shared durable storage across multiple app instances and can have write contention. Before production or multi-instance deployment, move to managed PostgreSQL and run migrations; preserve the repository/service boundary and SQLAlchemy models. Do not migrate session semantics into browser storage during that change.

## Downstream impact and sequencing

- **T009:** uses the environment names and separates public UI values from server-only OAuth/session/database secrets.
- **T019–T025:** implement the SQLite schema, password flow, Google callback, opaque sessions, safe profile endpoint, and sign-out based on this decision. Google's external consent/callback configuration remains an environment setup dependency.
- **T026–T027:** persist anonymous cart only in browser storage; preserve it through auth redirects. No server-side cart merge/sync is included.
- **T028–T029:** implement order schema and atomic creation with integer-bani totals, snapshots, and session-derived ownership.
- **T043–T045, T050, T054–T055:** profile, guards, return-to-checkout, order history, and details use the same session dependency and owner-scoped queries.
- **T059–T061:** review data boundaries, document the SQLite deployment limit, and configure secrets/callbacks without committing credentials.

Changing from this design later affects password/account migration, OAuth identity linking, cookie/session handling, T009 configuration, and order repository queries. Changing the cart from browser-local to account-synced would require a new server cart model and explicit merge rules; it is not an implicit consequence of sign-in.
