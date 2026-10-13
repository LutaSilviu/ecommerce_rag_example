# Nexo Market configuration

This guide records the configuration contract for the local FastAPI application and its plain HTML/CSS/JavaScript frontend. Keep names aligned with [DATA-AUTH-ARCHITECTURE.md](./DATA-AUTH-ARCHITECTURE.md). The application serves the browser UI and `/api/v1/` from one origin; the frontend does not need OAuth secrets or a separate frontend environment file.

## Values and exposure

| Variable | Exposure | Local example / purpose |
|---|---|---|
| `DATABASE_URL` | Private server configuration | `sqlite:///./data/nexo-market.db`; local SQLite database URL. |
| `SESSION_SECRET` | Private server secret | Replace the example with a high-entropy value. Do not reuse a committed or shared value. |
| `SESSION_COOKIE_NAME` | Server configuration | `nexo_session`; name of the opaque session cookie. |
| `SESSION_MAX_AGE_SECONDS` | Server configuration | `604800`; maximum session lifetime in seconds. |
| `SESSION_COOKIE_SECURE` | Server configuration | `false` for local HTTP only; `true` when served over HTTPS. |
| `GOOGLE_CLIENT_ID` | Public identifier, server-configured | OAuth client identifier used to start the Google flow. It is not a password, but keep it in server configuration and do not bundle environment values into browser code. |
| `GOOGLE_CLIENT_SECRET` | Private server secret | OAuth client secret. Never send it to the browser, return it from an API, log it, or commit it. |
| `GOOGLE_REDIRECT_URI` | Server configuration | Exact OAuth callback URL registered with Google. |
| `APP_BASE_URL` | Server configuration | Canonical application origin for safe same-origin post-auth redirects. |
| `OPENAI_API_KEY` | Private server secret | Optional API key for the catalog assistant. Keep it in local `.env` or the runtime secret store; never expose it to browser code or commit it. |
| `OPENAI_MODEL` | Server configuration | Responses API model; defaults to `gpt-6-luna`. |
| `OPENAI_EMBEDDING_MODEL` | Server configuration | Embeddings model for semantic catalog retrieval; defaults to `text-embedding-3-small`. |

Treat every value in `.env` as private operational configuration, even when the OAuth client ID is technically public. The client ID is not an authentication secret, but this app's Google integration is server initiated and the frontend should not receive the server environment wholesale.

## Local setup

1. Install Python 3.13 or newer. From the project root, create and activate a virtual environment with `py -3.13 -m venv .venv` and `.\\.venv\\Scripts\\Activate.ps1` on Windows, or `python3.13 -m venv .venv` and `source .venv/bin/activate` on macOS/Linux.
2. Install the declared dependencies using `python -m pip install -e .`. No Node/npm installation or frontend build is required.
3. Set a local session secret in the current shell, for example in PowerShell: `$env:SESSION_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")`. The default SQLite URL creates its `data` parent directory and the application initializes its current tables at startup.
4. Start the app from the project root using `python -m uvicorn app.main:app --reload`, then browse to `http://localhost:8000`.

The application reads operating-system process environment variables; it does **not** automatically read `.env`. `.env.example` lists the available names and local defaults, but copying it to `.env` alone does not configure the running process. Set variables in the shell before starting the server, or use a local environment loader of your choice. Do not commit `.env` or real secrets. For the default local run, `APP_BASE_URL`, `GOOGLE_REDIRECT_URI`, `DATABASE_URL`, and insecure local cookie mode have suitable defaults; Google credentials remain placeholders and Google sign-in remains unavailable.

For a one-command Windows session secret, the PowerShell expression above generates a random value each time. Keep the same shell/server process while using the app; changing its secret invalidates existing signed session cookies.

Google sign-in can remain unavailable until valid OAuth client values are supplied. Missing Google configuration should disable or clearly explain the unavailable Google option without preventing unrelated storefront pages from loading.

The floating product assistant is available on all customer pages. It retrieves semantically matching active products from the live catalog with OpenAI embeddings and supplies only those current catalog records to the Responses API. Product vectors are cached in SQLite and refreshed when product text or the embedding model changes; price and stock are always read fresh. Until `OPENAI_API_KEY` is supplied, the chat endpoint returns a clear configuration message and the rest of the storefront continues to work. Configure the key locally in the ignored `.env` file for Docker Compose, or export it in the shell for a direct local server. Never place it in HTML, JavaScript, an image build argument, or this documentation.

## Google OAuth provider setup — pending external input

No Google Cloud project or OAuth client has been created or registered for this
repository. The `.env.example` client ID and secret are placeholders. Real Google
sign-in remains unavailable until an authorized developer creates/configures a
Google OAuth client, supplies its values locally, and registers the URLs below.
Do not treat the URLs below as already authorized in Google's console.

For the documented local setup, the provider-side values to register are:

- **Authorized JavaScript origin:** `http://localhost:8000`
- **Authorized redirect URI:** `http://localhost:8000/api/v1/auth/google/callback`
- **Local `GOOGLE_REDIRECT_URI`:** `http://localhost:8000/api/v1/auth/google/callback`
- **Local `APP_BASE_URL`:** `http://localhost:8000`

When setting up a Google OAuth client, choose the appropriate application type for
the server-side authorization-code flow and register these exact values. The
client ID and secret must replace the placeholders in the developer's ignored
local `.env` file; never add credentials to this document, `.env.example`, or
browser JavaScript.

The application settings parser is available as `app.core.config.get_settings()`.
It reads configuration on demand, validates origin/callback consistency and
positive session lifetime, and exposes `google_oauth_enabled` as false while both
Google credential values remain placeholders. Supplying only one of the two
Google values is a configuration error. This parser does not create a provider
project or initialize an OAuth client.
- Set `GOOGLE_REDIRECT_URI` to that exact registered redirect URI, including scheme, host, port, and path.
- Set `APP_BASE_URL` to `http://localhost:8000`.

Google treats `localhost` and `127.0.0.1` as different hosts. If using the latter, consistently change the origin, callback, and both environment values to use `127.0.0.1`. Do not mix hosts or ports between the browser, callback registration, and application settings. For deployment, register the production HTTPS origin and its exact callback separately, and set `APP_BASE_URL` and `GOOGLE_REDIRECT_URI` to those production URLs. Never accept arbitrary post-login redirect URLs from a request; redirects must remain on known application paths on the configured origin.

## Container runtime and deployment contract

The repository includes a provider-neutral [Dockerfile](./Dockerfile), [Compose file](./compose.yaml), and [.dockerignore](./.dockerignore). The image serves the static HTML/CSS/JavaScript and FastAPI API from the same origin, listens on `0.0.0.0` at the `PORT` supplied by the runtime (default `8000`), and runs as an unprivileged user. Compose maps the host port and stores SQLite data in a named volume. Build and start locally with `docker compose up --build`; Compose requires `SESSION_SECRET` in the invoking environment. For a non-container host, install the project and run `uvicorn app.main:app --host 0.0.0.0 --port "$PORT"` (adjust quoting for the host shell).

For any HTTPS preview or production runtime, configure these server-side variables in the host's environment/secret settings. Never put real values in source files or build arguments:

| Variable | Runtime requirement |
|---|---|
| `PORT` | Use the port assigned by the host; the container honors it. |
| `APP_BASE_URL` | Canonical public HTTPS origin only, such as `https://shop.example.ro` (no path). |
| `SESSION_SECRET` | Unique high-entropy secret, different from local/development and every other environment. |
| `SESSION_COOKIE_SECURE` | `true` for HTTPS. |
| `DATABASE_URL` | Persistent database URL. SQLite needs a durable mounted volume; use a host-managed database for multi-instance or production use. |
| `OPENAI_API_KEY` | Secret-store value for the product assistant; keep it server-side. |
| `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL` | Optional model names; default to `gpt-6-luna` and `text-embedding-3-small`. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Set together in the server's secret store to enable Google sign-in; never expose the secret to frontend code. |
| `GOOGLE_REDIRECT_URI` | Exact public callback: `${APP_BASE_URL}/api/v1/auth/google/callback`. |
| `SESSION_COOKIE_NAME`, `SESSION_MAX_AGE_SECONDS` | Optional; default to `nexo_session` and `604800`. |

Serve the UI and `/api/v1` behind one HTTPS origin. Configure TLS at the chosen host/proxy, persist database storage, and restrict forwarded-header trust to that host's actual proxy addresses. No host, domain, database service, secret, OAuth client, or external deployment has been selected or provisioned by this repository. Register the exact production origin as Google's authorized JavaScript origin and the exact callback URL as its authorized redirect URI; configure matching `APP_BASE_URL` and `GOOGLE_REDIRECT_URI` in the runtime. Keep local and production OAuth registrations separate. A specific host's build settings, persistent storage, health checks, and secret injection remain to be mapped once a provider is chosen.

## Session cookie and HTTPS

The session cookie is `HttpOnly`, `SameSite=Lax`, and scoped to `/`; browser JavaScript cannot read it. `SESSION_COOKIE_SECURE=false` is suitable only for local plain-HTTP development because browsers will not send a Secure cookie over ordinary HTTP. Set `SESSION_COOKIE_SECURE=true` whenever the site is served over HTTPS, including production and HTTPS previews. Do not turn this off to work around a deployed sign-in problem; verify the HTTPS URL and reverse-proxy scheme instead. Use a strong, unique `SESSION_SECRET` in every non-local environment and keep OAuth state validation enabled.

## Never commit

- Real `.env` files, OAuth client secrets, session secrets, passwords, API tokens, or production environment dumps.
- SQLite database files (including `data/nexo-market.db`) or other files containing customer/session/order data.
- OAuth authorization codes, state values, ID/access tokens, raw session identifiers, or credential-bearing logs.

Commit `.env.example` only while it contains placeholder values and non-sensitive local defaults. Before staging changes, inspect them for credentials. If a secret is accidentally committed, removing it from the latest file is not sufficient: revoke/rotate the exposed value and purge it from repository history as appropriate.
