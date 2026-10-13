"use strict";

// Home storefront data consumer. Catalog pages can reuse the same endpoint,
// while this module renders only the mixed-catalog home section.
(() => {
  const grid = document.querySelector("[data-home-product-grid]");
  if (!grid || document.body.dataset.page !== "home") return;

  let requestController = null;

  function showState(state) {
    const mounted = window.NexoStatus.mount(grid, state);
    mounted.style.gridColumn = "1 / -1";
  }

  async function loadProducts() {
    requestController?.abort();
    requestController = new AbortController();
    grid.setAttribute("aria-busy", "true");
    showState(window.NexoStatus.loading({
      title: "Se încarcă produsele",
      message: "Pregătim o selecție din toate categoriile.",
    }));

    try {
      const response = await fetch("/api/v1/catalog/products", {
        headers: { Accept: "application/json" },
        signal: requestController.signal,
      });
      if (!response.ok) throw new Error("Catalog indisponibil");
      const products = await response.json();
      if (!Array.isArray(products)) throw new Error("Răspuns invalid din catalog");

      // Cart hydration needs the full catalog so stored IDs can be validated,
      // even if a future homepage chooses to present a shorter editorial set.
      window.NexoCart?.setProducts(products);
      if (products.length === 0) {
        showState(window.NexoStatus.empty({
          title: "Nu există produse momentan",
          message: "Revino în curând pentru a descoperi noutățile Nexo Market.",
        }));
        return;
      }

      const cards = products.map((product) => window.NexoProductCard.create(product));
      grid.replaceChildren(...cards);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
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
