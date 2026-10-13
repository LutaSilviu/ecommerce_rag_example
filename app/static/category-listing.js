"use strict";

// Category page consumer. Category names/descriptions come from the canonical
// taxonomy API; the URL slug remains the stable machine-facing identifier.
(() => {
  const section = document.querySelector("[data-category-listing]");
  if (!section || document.body.dataset.page !== "category") return;

  const grid = section.querySelector("[data-category-product-grid]");
  const title = section.querySelector("[data-category-title]");
  const description = section.querySelector("[data-category-description]");
  const pageHeading = document.querySelector(".page-main > h1");
  let slug = window.location.pathname.split("/").filter(Boolean).at(-1) || "";
  try {
    slug = decodeURIComponent(slug);
  } catch {
    // Treat malformed URL encoding as an unknown category and show the normal
    // localized not-found state instead of failing during script startup.
  }
  let requestController = null;

  function showState(state) {
    const mounted = window.NexoStatus.mount(grid, state);
    mounted.style.gridColumn = "1 / -1";
  }

  async function loadCategory() {
    requestController?.abort();
    requestController = new AbortController();
    const { signal } = requestController;
    grid.setAttribute("aria-busy", "true");
    showState(window.NexoStatus.loading({
      title: "Se încarcă produsele",
      message: "Pregătim produsele din această categorie.",
    }));

    try {
      const categoriesResponse = await fetch("/api/v1/catalog/categories", {
        headers: { Accept: "application/json" },
        signal,
      });
      if (!categoriesResponse.ok) throw new Error("Categorii indisponibile");
      const categories = await categoriesResponse.json();
      if (!Array.isArray(categories)) throw new Error("Răspuns invalid din catalog");
      const category = categories.find((item) => item.slug === slug);

      if (!category) {
        if (pageHeading) pageHeading.textContent = "Categoria nu a fost găsită";
        showState(window.NexoStatus.empty({
          title: "Categoria nu este disponibilă",
          message: "Categoria căutată nu există. Explorează toate produsele din magazin.",
          actionLabel: "Vezi produsele",
          onAction: () => window.location.assign("/search"),
        }));
        return;
      }

      title.textContent = category.name;
      description.textContent = category.description || "Descoperă produsele disponibile în această categorie.";
      if (pageHeading) pageHeading.textContent = category.name;
      document.title = `${category.name} · Nexo Market`;

      const productsResponse = await fetch(
        `/api/v1/catalog/products?category_slug=${encodeURIComponent(category.slug)}`,
        { headers: { Accept: "application/json" }, signal },
      );
      if (!productsResponse.ok) throw new Error("Produse indisponibile");
      const products = await productsResponse.json();
      if (!Array.isArray(products)) throw new Error("Răspuns invalid din catalog");
      if (products.length === 0) {
        showState(window.NexoStatus.empty({
          title: "Nu există produse momentan",
          message: "Nu avem produse disponibile în această categorie acum. Revino în curând sau explorează alte categorii.",
          actionLabel: "Vezi toate produsele",
          onAction: () => window.location.assign("/search"),
        }));
        return;
      }

      grid.replaceChildren(...products.map((product) => window.NexoProductCard.create(product)));
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      showState(window.NexoStatus.error({
        title: "Nu am putut încărca categoria",
        message: "Verifică conexiunea și încearcă din nou.",
        actionLabel: "Reîncearcă",
        onAction: loadCategory,
      }));
    } finally {
      grid.removeAttribute("aria-busy");
    }
  }

  loadCategory();
})();
