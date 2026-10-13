"use strict";

// Shared shell behavior only: this module renders the current auth/cart state
// and controls the compact category menu. It never handles credentials.
(() => {
  const accountLink = document.querySelector("[data-account-link]");
  const cartLink = document.querySelector(".cart-link");
  const cartCount = document.querySelector("[data-cart-count]");
  const categoryToggle = document.querySelector(".category-toggle");
  const categoryNavigation = document.querySelector("#category-navigation");
  const categoryLinks = document.querySelector("[data-category-links]");

  function renderCategories(categories) {
    if (!categoryLinks || !Array.isArray(categories)) return;
    const homeLink = categoryLinks.querySelector('a[href="/"]');
    categoryLinks.replaceChildren(...(homeLink ? [homeLink] : []));

    for (const category of categories) {
      if (!category || typeof category.slug !== "string" || typeof category.name !== "string") continue;
      const link = document.createElement("a");
      link.href = `/category/${encodeURIComponent(category.slug)}`;
      link.textContent = category.name;
      if (window.location.pathname === link.pathname) link.setAttribute("aria-current", "page");
      categoryLinks.append(link);
    }
  }

  async function loadCategories() {
    if (!categoryLinks) return;
    try {
      const response = await fetch("/api/v1/catalog/categories", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("Category request failed");
      renderCategories(await response.json());
    } catch {
      // Keep the home link usable if the catalog API is temporarily unavailable.
    }
  }

  function renderAccount(state) {
    if (!accountLink || !state) return;
    if (state.status === "authenticated" && state.user) {
      const displayName = typeof state.user.display_name === "string"
        ? state.user.display_name.trim()
        : "";
      accountLink.href = "/account";
      accountLink.textContent = displayName ? `Salut, ${displayName}` : "Contul meu";
      accountLink.setAttribute("aria-label", `Contul meu${displayName ? `, ${displayName}` : ""}`);
      return;
    }
    accountLink.href = "/login";
    accountLink.textContent = "Intră în cont";
    accountLink.setAttribute("aria-label", "Intră în cont");
  }

  function renderCart(state) {
    if (!cartCount || !cartLink || !state) return;
    const count = Number.isInteger(state.item_count) && state.item_count > 0
      ? state.item_count
      : 0;
    cartCount.textContent = count > 99 ? "99+" : String(count);
    cartLink.setAttribute("aria-label", `Coș, ${count} ${count === 1 ? "produs" : "produse"}`);
  }

  function closeCategoryMenu({ restoreFocus = false } = {}) {
    if (!categoryToggle || !categoryNavigation) return;
    categoryToggle.setAttribute("aria-expanded", "false");
    categoryNavigation.classList.remove("is-open");
    if (restoreFocus) categoryToggle.focus();
  }

  if (window.NexoAuthState) {
    renderAccount(window.NexoAuthState.getState());
    window.NexoAuthState.subscribe(renderAccount);
  }
  if (window.NexoCart) {
    renderCart(window.NexoCart.getState());
    window.NexoCart.subscribe(renderCart);
  }

  void loadCategories();

  categoryToggle?.addEventListener("click", () => {
    if (!categoryNavigation) return;
    const willOpen = categoryToggle.getAttribute("aria-expanded") !== "true";
    categoryToggle.setAttribute("aria-expanded", String(willOpen));
    categoryNavigation.classList.toggle("is-open", willOpen);
    if (!willOpen) categoryToggle.focus();
  });

  categoryNavigation?.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && categoryToggle?.getAttribute("aria-expanded") === "true") {
      event.preventDefault();
      closeCategoryMenu({ restoreFocus: true });
    }
  });
  categoryNavigation?.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeCategoryMenu();
  });
})();
