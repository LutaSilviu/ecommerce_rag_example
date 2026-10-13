"use strict";

// Client-side protection prevents confusing page flashes and sends signed-out
// shoppers through the existing auth flow. The API remains responsible for
// enforcing account and order ownership.
(() => {
  const protectedPages = new Set([
    "account",
    "orders",
    "order-detail",
    "checkout-details",
    "checkout-review",
    "confirmation",
  ]);
  const body = document.body;
  const page = body?.dataset.page;
  if (!body || !protectedPages.has(page)) {
    body?.setAttribute("data-route-auth", "ready");
    return;
  }

  const loadingPanel = document.querySelector("[data-route-auth-loading]");
  const content = document.querySelector("#main-content");
  const returnDestination = safeDestination(`${window.location.pathname}${window.location.search}`);

  function setState(state) {
    body.dataset.routeAuth = state;
    content?.setAttribute("aria-busy", String(state === "loading"));
    if (loadingPanel) {
      loadingPanel.hidden = state !== "loading" && state !== "error";
      loadingPanel.setAttribute("aria-busy", String(state === "loading"));
      if (state === "error") {
        loadingPanel.innerHTML = '<div><h2>Sesiunea nu este disponibilă</h2><p>Nu am putut verifica autentificarea. Verifică conexiunea și încearcă din nou.</p><button class="button button--secondary" type="button" data-route-auth-retry>Încearcă din nou</button></div>';
        loadingPanel.querySelector("[data-route-auth-retry]")?.addEventListener("click", () => {
          loadingPanel.innerHTML = '<span class="route-auth-loading__spinner" aria-hidden="true"></span><div><h2>Se verifică sesiunea</h2><p>Încărcăm pagina în siguranță.</p></div>';
          void window.NexoAuthState?.load();
        }, { once: true });
      }
    }
  }

  function onAuthChange(state) {
    if (!state || state.status === "loading") {
      setState("loading");
      return;
    }
    if (state.status === "authenticated" && state.user) {
      setState("ready");
      return;
    }
    if (state.status === "error") {
      setState("error");
      return;
    }

    const login = new URL("/login", window.location.origin);
    login.searchParams.set("return_to", returnDestination);
    window.location.replace(`${login.pathname}${login.search}`);
  }

  window.NexoRouteGuard = Object.freeze({ safeDestination });
  setState("loading");
  if (window.NexoAuthState) {
    window.NexoAuthState.subscribe(onAuthChange);
    onAuthChange(window.NexoAuthState.getState());
  } else {
    setState("error");
  }

  function safeDestination(value) {
    if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
      return "/account";
    }
    let parsed;
    try {
      parsed = new URL(value, window.location.origin);
    } catch {
      return "/account";
    }
    if (parsed.origin !== window.location.origin || parsed.search || parsed.hash) return "/account";

    const path = parsed.pathname;
    const allowed = path === "/account"
      || path === "/account/orders"
      || path === "/checkout/details"
      || path === "/checkout/review"
      || /^\/account\/orders\/[A-Za-z0-9-]+$/.test(path)
      || /^\/checkout\/confirmation\/[A-Za-z0-9-]+$/.test(path)
      || /^\/category\/[a-z0-9-]+$/.test(path)
      || /^\/product\/[a-z0-9-]+$/.test(path)
      || path === "/" || path === "/cart" || path === "/search";
    return allowed ? path : "/account";
  }
})();
