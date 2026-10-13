"use strict";

// Hydrate against the complete catalog before an add, including on filtered pages.
(() => {
  let hydration = null;

  async function hydrate() {
    if (!window.NexoCart) throw new Error("Coșul nu este disponibil momentan.");
    if (window.NexoCart.getState().catalog_ready) return window.NexoCart.getState();
    if (!hydration) {
      hydration = fetch("/api/v1/catalog/products", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      }).then(async (response) => {
        if (!response.ok) throw new Error("Catalogul nu este disponibil momentan.");
        const products = await response.json();
        if (!Array.isArray(products)) throw new Error("Catalogul a returnat date invalide.");
        return window.NexoCart.setProducts(products);
      }).catch((error) => {
        hydration = null;
        throw error;
      });
    }
    return hydration;
  }

  window.NexoCartCatalog = Object.freeze({ hydrate });
})();
