"use strict";

// Search uses the same catalog API and reusable card/state components as the
// home and category views. Romanian accent-insensitive matching is applied by
// the catalog repository so all API consumers receive consistent results.
(() => {
  const section = document.querySelector("[data-search-listing]");
  if (!section || document.body.dataset.page !== "search") return;

  const grid = section.querySelector("[data-search-product-grid]");
  const title = section.querySelector("[data-search-title]");
  const count = section.querySelector("[data-search-count]");
  const pageHeading = document.querySelector(".page-main > h1");
  const query = (new URLSearchParams(window.location.search).get("q") || "").trim();

  if (query) {
    title.textContent = `Rezultate pentru „${query}”`;
    if (pageHeading) pageHeading.textContent = `Căutare: ${query}`;
    document.title = `Căutare: ${query} · Nexo Market`;
  } else {
    title.textContent = "Toate produsele";
    if (pageHeading) pageHeading.textContent = "Toate produsele";
    document.title = "Toate produsele · Nexo Market";
  }

  function showState(state) {
    const mounted = window.NexoStatus.mount(grid, state);
    mounted.style.gridColumn = "1 / -1";
  }

  async function loadProducts() {
    grid.setAttribute("aria-busy", "true");
    count.textContent = "Se încarcă produsele…";
    showState(window.NexoStatus.loading({
      title: "Se încarcă produsele",
      message: "Căutăm în catalogul Nexo Market.",
    }));

    try {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      const suffix = params.size ? `?${params.toString()}` : "";
      const response = await fetch(`/api/v1/catalog/products${suffix}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Catalog indisponibil");
      const products = await response.json();
      if (!Array.isArray(products)) throw new Error("Răspuns invalid din catalog");

      const productLabel = products.length === 1 ? "produs găsit" : "produse găsite";
      count.textContent = query
        ? `${products.length} ${productLabel} pentru „${query}”.`
        : `${products.length} ${products.length === 1 ? "produs disponibil" : "produse disponibile"}.`;

      if (products.length === 0) {
        showState(window.NexoStatus.empty({
          title: "Nu am găsit produse",
          message: query
            ? "Încearcă un alt termen sau verifică dacă ai scris corect. Poți căuta fără diacritice."
            : "Catalogul nu conține produse momentan. Revino în curând.",
          actionLabel: query ? "Vezi toate produsele" : undefined,
          onAction: query ? () => window.location.assign("/search") : undefined,
        }));
        return;
      }

      grid.replaceChildren(...products.map((product) => window.NexoProductCard.create(product)));
    } catch (error) {
      count.textContent = "Produsele nu sunt disponibile momentan.";
      showState(window.NexoStatus.error({
        title: "Nu am putut încărca produsele",
        message: "Verifică conexiunea și încearcă din nou.",
        actionLabel: "Reîncearcă",
        onAction: loadProducts,
      }));
    } finally {
      grid.removeAttribute("aria-busy");
    }
  }

  loadProducts();
})();
