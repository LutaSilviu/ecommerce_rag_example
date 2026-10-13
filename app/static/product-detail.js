"use strict";

// Product detail page. The slug is the public URL identity; the API returns
// the stable UUID used by cart/order records and integer-bani prices.
(() => {
  if (document.body.dataset.page !== "product") return;
  const section = document.querySelector("[data-product-detail]");
  const state = section?.querySelector("[data-product-detail-state]");
  if (!section || !state) return;

  const rawSlug = window.location.pathname.split("/").filter(Boolean).at(-1) || "";
  let slug = rawSlug;
  try { slug = decodeURIComponent(rawSlug); } catch { /* request will resolve as not found */ }

  function showStatus(kind, options) {
    window.NexoStatus.mount(state, window.NexoStatus[kind](options));
  }

  function renderProduct(product, categoryName) {
    const inStock = product.is_active !== false
      && Number.isInteger(product.stock_quantity)
      && product.stock_quantity > 0;
    const article = document.createElement("article");
    article.className = "product-detail__layout";

    const image = document.createElement("img");
    image.className = "product-detail__image";
    image.src = product.image_url || "";
    image.alt = product.name;
    image.decoding = "async";
    image.addEventListener("error", () => image.classList.add("product-detail__image--missing"), { once: true });

    const content = document.createElement("div");
    content.className = "product-detail__content";
    const category = document.createElement("a");
    category.className = "product-detail__category";
    category.href = `/category/${encodeURIComponent(product.category_slug || "")}`;
    category.textContent = categoryName || "Produse Nexo";

    const title = document.querySelector(".page-main > h1");
    if (title) {
      title.textContent = product.name;
      document.title = `${product.name} · Nexo Market`;
    }

    const sku = document.createElement("p");
    sku.className = "product-detail__sku";
    sku.textContent = `Cod produs: ${product.sku}`;
    const price = document.createElement("p");
    price.className = "product-detail__price";
    price.textContent = window.NexoMoney.formatRon(product.price_bani);
    const availability = document.createElement("p");
    availability.className = `product-detail__availability ${inStock ? "is-available" : "is-unavailable"}`;
    availability.textContent = inStock ? `În stoc · ${product.stock_quantity} bucăți disponibile` : "Stoc epuizat";
    const description = document.createElement("p");
    description.className = "product-detail__description";
    description.textContent = product.description || "Descoperă acest produs din colecția Nexo Market.";

    const controls = document.createElement("div");
    controls.className = "product-detail__purchase";
    const quantityLabel = document.createElement("label");
    quantityLabel.htmlFor = "product-quantity";
    quantityLabel.textContent = "Cantitate";
    const quantity = document.createElement("input");
    quantity.id = "product-quantity";
    quantity.className = "product-detail__quantity";
    quantity.type = "number";
    quantity.min = "1";
    quantity.max = String(Math.min(99, Math.max(product.stock_quantity, 1)));
    quantity.value = "1";
    quantity.disabled = !inStock;
    const add = document.createElement("button");
    add.className = "button button--primary";
    add.type = "button";
    add.dataset.productAdd = "";
    add.textContent = "Adaugă în coș";
    add.disabled = !inStock;
    const feedback = document.createElement("p");
    feedback.className = "product-detail__feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    feedback.hidden = true;
    add.addEventListener("click", async () => {
      const amount = Number(quantity.value);
      if (!Number.isInteger(amount) || amount < 1 || amount > 99) {
        feedback.textContent = "Alege o cantitate între 1 și 99.";
        feedback.classList.add("is-error");
        feedback.hidden = false;
        return;
      }
      add.disabled = true;
      add.setAttribute("aria-busy", "true");
      try {
        await window.NexoCartCatalog?.hydrate();
      } catch (error) {
        feedback.textContent = error instanceof Error ? error.message : "Coșul nu este disponibil momentan.";
        feedback.classList.add("is-error");
        feedback.hidden = false;
        add.disabled = !inStock;
        add.removeAttribute("aria-busy");
        return;
      }
      const result = window.NexoCart?.add(product.id, amount);
      if (!result || result.ok === false) {
        feedback.textContent = result?.error || "Coșul nu este disponibil momentan.";
        feedback.classList.add("is-error");
      } else {
        feedback.textContent = "Produs adăugat în coș.";
        feedback.classList.remove("is-error");
      }
      feedback.hidden = false;
      add.disabled = !inStock;
      add.removeAttribute("aria-busy");
    });
    controls.append(quantityLabel, quantity, add);
    content.append(category, sku, price, availability, description, controls, feedback);
    article.append(image, content);
    state.replaceChildren(article);
  }

  async function load() {
    section.setAttribute("aria-busy", "true");
    showStatus("loading", { title: "Se încarcă produsul", message: "Pregătim detaliile produsului." });
    try {
      const response = await fetch(`/api/v1/catalog/products/${encodeURIComponent(slug)}`, {
        headers: { Accept: "application/json" },
      });
      if (response.status === 404) {
        showStatus("empty", {
          title: "Produsul nu a fost găsit",
          message: "Produsul căutat nu există sau nu mai este disponibil în catalog.",
          actionLabel: "Vezi toate produsele",
          onAction: () => window.location.assign("/search"),
        });
        const title = document.querySelector(".page-main > h1");
        if (title) title.textContent = "Produsul nu a fost găsit";
        return;
      }
      if (!response.ok) throw new Error("Catalog indisponibil");
      const product = await response.json();
      const [catalogResponse, categoriesResponse] = await Promise.all([
        fetch("/api/v1/catalog/products", { headers: { Accept: "application/json" } }),
        fetch("/api/v1/catalog/categories", { headers: { Accept: "application/json" } }),
      ]);
      if (catalogResponse.ok) {
        const products = await catalogResponse.json();
        if (Array.isArray(products)) window.NexoCart?.setProducts(products);
      }
      const categories = categoriesResponse.ok ? await categoriesResponse.json() : [];
      const category = Array.isArray(categories) ? categories.find((item) => item.id === product.category_id) : null;
      product.category_slug = category?.slug || "";
      renderProduct(product, category?.name || "");
    } catch {
      showStatus("error", {
        title: "Nu am putut încărca produsul",
        message: "Verifică conexiunea și încearcă din nou.",
        actionLabel: "Reîncearcă",
        onAction: load,
      });
    } finally {
      section.removeAttribute("aria-busy");
    }
  }

  load();
})();
