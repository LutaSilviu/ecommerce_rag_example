"""FastAPI page-route skeleton for Nexo Market.

Customer pages deliberately share one static shell until their feature tasks
replace the placeholders. JSON endpoints belong under ``/api/v1``.
"""

from html import escape
from pathlib import Path

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.catalog.routes import router as catalog_router
from app.orders.routes import router as orders_router
from app.core.config import get_settings
from app.persistence.base import Base
from app.persistence.database import get_engine
from app.persistence.models import OAuthIdentity, PasswordCredential, SessionRecord, User
from app.persistence.order_models import OrderConfirmationRecord, OrderItemRecord, OrderRecord
from app.persistence.catalog_seed import seed_catalog_data

app = FastAPI(title="Nexo Market", version="0.1.0")
_settings = get_settings()
app.add_middleware(
    SessionMiddleware,
    secret_key=_settings.session_secret,
    session_cookie="nexo_oauth_state",
    max_age=600,
    same_site="lax",
    https_only=_settings.session_cookie_secure,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
SHELL_PATH = STATIC_DIR / "index.html"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(catalog_router)
app.include_router(orders_router)


@app.on_event("startup")
def initialize_local_auth_schema() -> None:
    """Apply catalog migrations, preserve/create auth-order tables, and seed catalog."""
    migration_config = AlembicConfig(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    migration_config.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "migrations"))
    alembic_command.upgrade(migration_config, "head")
    Base.metadata.create_all(
        bind=get_engine(),
        tables=[
            User.__table__,
            PasswordCredential.__table__,
            OAuthIdentity.__table__,
            SessionRecord.__table__,
            OrderRecord.__table__,
            OrderItemRecord.__table__,
            OrderConfirmationRecord.__table__,
        ],
    )
    seed_catalog_data()


def render_page(title: str, page: str, *, subtitle: str | None = None) -> HTMLResponse:
    """Render the shared Romanian placeholder shell with escaped route metadata."""
    template = SHELL_PATH.read_text(encoding="utf-8")
    values = {
        "{{PAGE_TITLE}}": escape(title),
        "{{PAGE_KEY}}": escape(page),
        "{{PAGE_SUBTITLE}}": escape(subtitle or "Conținutul acestei pagini va fi disponibil în etapa următoare."),
    }
    for marker, value in values.items():
        template = template.replace(marker, value)
    return HTMLResponse(template)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def storefront() -> HTMLResponse:
    return render_page("Bine ai venit la Nexo Market", "home", subtitle="Tot ce-ți trebuie, într-un singur loc.")


@app.get("/category/{category_slug}", response_class=HTMLResponse, include_in_schema=False)
def category_page(category_slug: str) -> HTMLResponse:
    return render_page(f"Categoria: {category_slug.replace('-', ' ')}", "category")


@app.get("/search", response_class=HTMLResponse, include_in_schema=False)
def search_page(q: str = Query(default=""), category: str | None = Query(default=None)) -> HTMLResponse:
    del category  # Query parsing is part of the route contract; search behavior is a later task.
    title = f"Căutare: {q}" if q else "Caută produse"
    return render_page(title, "search")


@app.get("/product/{product_slug}", response_class=HTMLResponse, include_in_schema=False)
def product_page(product_slug: str) -> HTMLResponse:
    return render_page(f"Produs: {product_slug.replace('-', ' ')}", "product")


@app.get("/cart", response_class=HTMLResponse, include_in_schema=False)
def cart_page() -> HTMLResponse:
    return render_page("Coșul meu", "cart")


@app.get("/register", response_class=HTMLResponse, include_in_schema=False)
def register_page() -> HTMLResponse:
    return render_page("Creează un cont", "register")


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page() -> HTMLResponse:
    return render_page("Autentificare", "login")


@app.get("/account", response_class=HTMLResponse, include_in_schema=False)
def account_page() -> HTMLResponse:
    return render_page("Contul meu", "account")


@app.get("/checkout/details", response_class=HTMLResponse, include_in_schema=False)
def checkout_details_page() -> HTMLResponse:
    return render_page("Date de livrare", "checkout-details")


@app.get("/checkout/review", response_class=HTMLResponse, include_in_schema=False)
def checkout_review_page() -> HTMLResponse:
    return render_page("Revizuiește comanda", "checkout-review")


@app.get("/checkout/confirmation/{order_number}", response_class=HTMLResponse, include_in_schema=False)
def checkout_confirmation_page(order_number: str) -> HTMLResponse:
    return render_page(f"Confirmare comandă {order_number}", "confirmation")


@app.get("/account/orders", response_class=HTMLResponse, include_in_schema=False)
def account_orders_page() -> HTMLResponse:
    return render_page("Comenzile mele", "orders")


@app.get("/account/orders/{order_number}", response_class=HTMLResponse, include_in_schema=False)
def account_order_detail_page(order_number: str) -> HTMLResponse:
    return render_page(f"Comanda {order_number}", "order-detail")


@app.get("/api/v1", include_in_schema=False)
def api_namespace_root() -> JSONResponse:
    return JSONResponse({"detail": "API endpoint not found"}, status_code=404)


@app.get("/api/v1/{api_path:path}", include_in_schema=False)
def api_namespace_not_found(api_path: str) -> JSONResponse:
    del api_path
    return JSONResponse({"detail": "API endpoint not found"}, status_code=404)


@app.get("/{unmatched_path:path}", response_class=HTMLResponse, include_in_schema=False)
def customer_not_found(unmatched_path: str) -> HTMLResponse:
    """Provide a Romanian 404 shell for unsupported customer page URLs."""
    del unmatched_path
    response = render_page("Pagina nu a fost găsită", "not-found", subtitle="Pagina căutată nu există.")
    response.status_code = 404
    return response
