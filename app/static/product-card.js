"use strict";

// Reusable DOM component. Load money.js and cart-state.js before this module.
(() => {
  const availabilityCopy = {
    in_stock: "În stoc",
    out_of_stock: "Stoc epuizat",
    unavailable: "Indisponibil",
  };

  function availabilityFor(product) {
    if (product.is_active === false) return "unavailable";
    return Number.isInteger(product.stock_quantity) && product.stock_quantity > 0
      ? "in_stock"
      : "out_of_stock";
  }

  function create(product, { onAdd = null } = {}) {
    if (!product || typeof product.id !== "string") {
      throw new TypeError("Este necesar un produs valid pentru card.");
    }
    if (!window.NexoMoney) throw new Error("Încarcă money.js înainte de product-card.js.");

    const availability = availabilityFor(product);
    const card = document.createElement("article");
    card.className = "product-card";
    card.dataset.productId = product.id;

    const image = document.createElement("img");
    image.className = "product-card__image";
    image.src = product.image_url || "";
    image.alt = typeof product.name === "string" ? product.name : "Produs";
    image.loading = "lazy";
    image.decoding = "async";

    const productLink = document.createElement("a");
    productLink.className = "product-card__link";
    productLink.href = product.slug ? `/product/${encodeURIComponent(product.slug)}` : `/product/${encodeURIComponent(product.id)}`;
    productLink.setAttribute("aria-label", `Vezi detaliile produsului ${product.name || "Produs"}`);
    productLink.append(image);

    const body = document.createElement("div");
    body.className = "product-card__body";
    const name = document.createElement("h3");
    name.className = "product-card__name";
    const nameLink = document.createElement("a");
    nameLink.href = productLink.href;
    nameLink.textContent = product.name || "Produs fără nume";
    name.append(nameLink);

    const status = document.createElement("p");
    status.className = `product-card__availability product-card__availability--${availability}`;
    status.textContent = availabilityCopy[availability];

    const price = document.createElement("p");
    price.className = "product-card__price";
    price.textContent = window.NexoMoney.formatRon(product.price_bani);

    const feedback = document.createElement("p");
    feedback.className = "product-card__feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    feedback.hidden = true;

    const button = document.createElement("button");
    button.className = "button button--primary product-card__add";
    button.type = "button";
    button.textContent = "Adaugă în coș";
    button.disabled = availability !== "in_stock";
    button.addEventListener("click", async () => {
      if (button.disabled) return;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.textContent = "Se adaugă…";
      feedback.hidden = true;
      try {
        await window.NexoCartCatalog?.hydrate();
        const result = onAdd
          ? await onAdd(product)
          : window.NexoCart?.add(product.id);
        if (!result) throw new Error("Coșul nu este disponibil momentan.");
        if (result.ok === false) throw new Error(result.error || "Produsul nu a putut fi adăugat.");
        feedback.textContent = "Produs adăugat în coș.";
        feedback.classList.remove("product-card__feedback--error");
        feedback.hidden = false;
        button.textContent = "Adăugat în coș";
        window.setTimeout(() => {
          button.textContent = "Adaugă în coș";
          button.disabled = availabilityFor(product) !== "in_stock";
        }, 1600);
      } catch (error) {
        feedback.textContent = error instanceof Error ? error.message : "Produsul nu a putut fi adăugat.";
        feedback.classList.add("product-card__feedback--error");
        feedback.hidden = false;
        button.textContent = "Adaugă în coș";
        button.disabled = availabilityFor(product) !== "in_stock";
      } finally {
        button.removeAttribute("aria-busy");
      }
    });

    body.append(name, status, price, feedback, button);
    card.append(productLink, body);
    return card;
  }

  window.NexoProductCard = Object.freeze({ create });
})();
