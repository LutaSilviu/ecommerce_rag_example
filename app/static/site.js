"use strict";

// Keep shared navigation useful on every direct page load; page behavior is
// intentionally left to the feature tasks that follow this route skeleton.
const currentPath = window.location.pathname.replace(/\/$/, "") || "/";
for (const link of document.querySelectorAll(".category-nav a")) {
  const linkPath = new URL(link.href).pathname.replace(/\/$/, "") || "/";
  const active = linkPath === "/"
    ? currentPath === "/"
    : currentPath === linkPath || currentPath.startsWith(`${linkPath}/`);
  if (active) link.setAttribute("aria-current", "page");
}

const searchInput = document.querySelector("#site-search");
if (searchInput) {
  searchInput.value = new URLSearchParams(window.location.search).get("q") || "";
}

// Authentication forms are standalone static partials so the shared page shell
// and the other route placeholders remain independent.
const authPartialByPage = {
  register: {
    path: "/static/partials/register.html",
    unavailable: "Nu am putut încărca formularul de înregistrare. Reîncarcă pagina.",
  },
  login: {
    path: "/static/partials/login.html",
    unavailable: "Nu am putut încărca formularul de autentificare. Reîncarcă pagina.",
  },
};

const authPartial = authPartialByPage[document.body.dataset.page];
if (authPartial) {
  const pageContent = document.querySelector("#page-content");
  if (pageContent) {
    pageContent.setAttribute("aria-busy", "true");
    fetch(authPartial.path)
      .then((response) => {
        if (!response.ok) throw new Error(authPartial.unavailable);
        return response.text();
      })
      .then((markup) => {
        pageContent.outerHTML = markup;
        preserveAuthReturnPath();
        bindAuthForm(document.querySelector("[data-auth-form]"));
        bindGoogleAuthButtons();
        showGoogleAuthReturnMessage();
      })
      .catch((error) => {
        pageContent.removeAttribute("aria-busy");
        const heading = document.createElement("h2");
        heading.textContent = "Formular indisponibil";
        const message = document.createElement("p");
        message.textContent = "Nu am putut încărca formularul. Reîncarcă pagina și încearcă din nou.";
        pageContent.replaceChildren(heading, message);
      });
  }
}

// Email auth is an in-page POST while Google auth leaves and returns to the
// app. In both cases the localStorage cart stays canonical. Reconcile it once
// the restored session is known, without clearing or silently changing stock
// quantities. Catalog state is supplied by catalog consumers when available.
if (window.NexoAuthState && window.NexoCart) {
  let reconciledUserId = null;
  const reconcileAuthenticatedCart = (auth) => {
    if (auth?.status !== "authenticated" || !auth.user?.id) return;
    if (reconciledUserId === auth.user.id) return;
    reconciledUserId = auth.user.id;
    window.NexoCart.reconcileAfterAuth?.();
  };
  window.NexoAuthState.subscribe(reconcileAuthenticatedCart);
  reconcileAuthenticatedCart(window.NexoAuthState.getState());
}

function preserveAuthReturnPath() {
  const requested = safeReturnDestination();
  const currentTarget = new URLSearchParams(window.location.search).get("return_to");
  if (!currentTarget || requested === "/account") return;
  for (const link of document.querySelectorAll('.register-login a[href="/login"], .register-login a[href="/register"]')) {
    const destination = new URL(link.getAttribute("href"), window.location.origin);
    destination.searchParams.set("return_to", requested);
    link.href = `${destination.pathname}${destination.search}`;
  }
}

function bindGoogleAuthButtons() {
  const buttons = [...document.querySelectorAll("[data-google-signin], [data-google-signup]")];
  if (!buttons.length) return;
  const notice = document.querySelector("[data-google-status]");
  fetch("/api/v1/auth/google/availability", { headers: { Accept: "application/json" } })
    .then((response) => {
      if (!response.ok) throw new Error("availability");
      return response.json();
    })
    .then(({ available }) => {
      const hasGoogleReturnError = Boolean(new URLSearchParams(window.location.search).get("google_error"));
      for (const button of buttons) {
        button.disabled = !available;
        if (!available) button.setAttribute("aria-describedby", "google-auth-status");
      }
      if (notice && !hasGoogleReturnError) {
        notice.hidden = Boolean(available);
        notice.textContent = available ? "" : "Autentificarea Google nu este configurată încă. Administratorul trebuie să completeze setările OAuth.";
      }
    })
    .catch(() => {
      for (const button of buttons) button.disabled = true;
      const hasGoogleReturnError = Boolean(new URLSearchParams(window.location.search).get("google_error"));
      if (notice && !hasGoogleReturnError) {
        notice.hidden = false;
        notice.textContent = "Autentificarea Google nu este disponibilă momentan.";
      }
    });

  for (const button of buttons) {
    button.addEventListener("click", () => {
      if (button.disabled) return;
      const returnTo = safeReturnDestination();
      window.location.assign(`/api/v1/auth/google?return_to=${encodeURIComponent(returnTo)}`);
    });
  }
}

function showGoogleAuthReturnMessage() {
  const error = new URLSearchParams(window.location.search).get("google_error");
  if (!error) return;
  const notice = document.querySelector("[data-google-status]");
  if (!notice) return;
  const messages = {
    unavailable: "Autentificarea Google nu este configurată încă.",
    account_exists: "Există deja un cont cu această adresă. Autentifică-te cu parola contului.",
    unverified_email: "Google nu a confirmat adresa de e-mail. Încearcă din nou.",
    invalid_identity: "Nu am putut verifica identitatea Google. Încearcă din nou.",
    account_unavailable: "Contul nu este disponibil. Contactează administratorul.",
    failed: "Autentificarea Google nu a reușit. Încearcă din nou.",
    denied: "Autentificarea Google a fost anulată.",
  };
  notice.textContent = messages[error] || messages.failed;
  notice.hidden = false;
}

function safeReturnDestination() {
  const requested = new URLSearchParams(window.location.search).get("return_to") || "";
  if (!requested.startsWith("/") || requested.startsWith("//") || requested.includes("\\")) {
    return "/account";
  }
  let parsed;
  try {
    parsed = new URL(requested, window.location.origin);
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

function bindAuthForm(form) {
  if (!form) return;
  const errorBox = document.querySelector(`#${form.dataset.authForm}-error`);
  const password = form.querySelector('[name="password"]');
  const confirmation = form.querySelector('[name="password_confirmation"]');

  function validateConfirmation() {
    if (!confirmation || !password) return true;
    confirmation.setCustomValidity(
      confirmation.value && confirmation.value !== password.value ? "Parolele nu coincid." : "",
    );
    return confirmation.checkValidity();
  }

  confirmation?.addEventListener("input", validateConfirmation);
  password?.addEventListener("input", validateConfirmation);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateConfirmation() || !form.reportValidity()) return;
    if (errorBox) {
      errorBox.hidden = true;
      errorBox.textContent = "";
    }
    const submitButton = form.querySelector('[type="submit"]');
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.setAttribute("aria-busy", "true");
    }
    form.setAttribute("aria-busy", "true");
    try {
      const values = Object.fromEntries(new FormData(form).entries());
      const response = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(values),
      });
      let result = {};
      try { result = await response.json(); } catch { /* handled as a generic server error */ }
      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ? result.detail : "Autentificarea nu a reușit. Încearcă din nou.");
      }
      const nextState = await window.NexoAuthState?.load();
      if (!nextState || nextState.status !== "authenticated") {
        throw new Error("Contul a fost salvat, dar sesiunea nu a putut fi verificată. Reîncarcă pagina.");
      }
      window.location.assign(safeReturnDestination());
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = error instanceof Error ? error.message : "A apărut o eroare. Încearcă din nou.";
        errorBox.hidden = false;
      }
    } finally {
      form.removeAttribute("aria-busy");
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.removeAttribute("aria-busy");
      }
    }
  });
}
