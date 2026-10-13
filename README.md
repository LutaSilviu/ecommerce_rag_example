# Nexo Market

The storefront includes a floating Romanian product assistant grounded only in
active catalog records. Set `OPENAI_API_KEY` in the server environment to enable
semantic retrieval and Responses API answers; see [CONFIGURATION.md](./CONFIGURATION.md).

Romanian ecommerce prototype built with FastAPI and plain HTML, CSS, and JavaScript. It demonstrates product browsing, account flows, a cart, checkout, and prototype orders. Payments are simulated; this project is not configured for real transactions.

## Run locally

Prerequisites: Python 3.13 or newer. There is no Node.js install, frontend build, or separate database server required for the default local setup.

From the repository root, create a virtual environment and install the project:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

The application applies database migrations automatically during startup. To
inspect or apply schema changes manually, run `python -m alembic upgrade head`
from the repository root with the same environment variables as the app. A
legacy SQLite database receives the catalog tables and Alembic version marker;
existing account and order tables/data are left in place.

Set a per-shell session secret, then start the development server:

```powershell
$env:SESSION_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")
python -m uvicorn app.main:app --reload
```

Open <http://localhost:8000>. The default SQLite database is `data/nexo-market.db`. Stop the server with Ctrl+C.

## Deploy a free demo on Render

The repository includes a Render Blueprint in [`render.yaml`](./render.yaml).
In Render, create a new Blueprint Instance, connect this GitHub repository, and
apply the Blueprint. Render creates a free web service in Frankfurt and asks
for `OPENAI_API_KEY`; enter the key as a secret in Render, never in this file.
The generated service URL is used automatically as `APP_BASE_URL`, so the
Google callback becomes `<service-url>/api/v1/auth/google/callback`.

This free demo uses SQLite on Render's temporary filesystem. Accounts, orders,
and catalog changes can be lost when the service restarts, redeploys, or sleeps.
The free web service also sleeps after 15 minutes without traffic. Before
enabling Google sign-in, add the Render service URL as an authorized origin and
its callback URL as an authorized redirect URI in the Google OAuth client.

Settings are read from process environment variables; the app does **not** automatically load `.env`. `.env.example` is a reference template. Set values in your shell or use your own environment loader. See [CONFIGURATION.md](./CONFIGURATION.md) for the complete settings contract and Google OAuth setup.

For bash/zsh, the equivalent setup is:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python -m uvicorn app.main:app --reload
```

## Google sign-in

Google sign-in stays unavailable while `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are placeholders. To enable it locally, create/configure your own Google OAuth client, register `http://localhost:8000` as the authorized JavaScript origin and `http://localhost:8000/api/v1/auth/google/callback` as the authorized redirect URI, then set both credentials in your local environment. Never commit real credentials. The origin, redirect URI, and address used in the browser must match exactly.

## Prototype limits

- The catalog contains 40 Romanian sample products across eight categories. Product IDs, descriptions, prices, image links, and stock are stored in the catalog tables. Startup inserts missing bundled demo rows but never overwrites persisted catalog edits; existing rows survive restarts. SQLite is intended for local development.
- Checkout records a demonstration order. No payment is processed and no card details are requested.
- Google sign-in needs credentials supplied by the developer; no project credentials are included.
- Run the development server only for local development. Production deployment needs HTTPS, a strong private session secret, production database/operations, and deployment-specific OAuth URLs.
