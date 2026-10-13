"use strict";

// Cart page view and controls. Cart identity/quantity remain owned by NexoCart;
// product facts and prices are resolved from the current catalog on each render.
(() => {
  function initializeCartPage() {
    const root = document.querySelector("[data-cart-page]");
    if (!root || !window.NexoCart || !window.NexoMoney) return;

    const list = root.querySelector("[data-cart-items]");
    const template = root.querySelector("[data-cart-line-template]");
    const empty = root.querySelector("[data-cart-empty-state]");
    const subtotal = root.querySelector("[data-cart-subtotal]");
    const total = root.querySelector("[data-cart-total]");
    const checkout = root.querySelector("[data-cart-checkout]");
    if (!list || !template || !empty || !subtotal || !total || !checkout) return;

    let notice = root.querySelector("[data-cart-feedback]");
    if (!notice) {
      notice = document.createElement("p");
      notice.dataset.cartFeedback = "";
      notice.className = "cart-page__loading";
      notice.setAttribute("role", "status");
      notice.setAttribute("aria-live", "polite");
      notice.hidden = true;
      list.before(notice);
    }

    const showNotice = (message) => {
      notice.textContent = message || "";
      notice.hidden = !message;
    };

    function render(state) {
      const active = document.activeElement;
      const activeLine = active?.closest?.("[data-product-id]");
      const activeProductId = activeLine?.dataset.productId;
      const activeAction = active?.matches?.("[data-cart-remove]") ? "remove"
        : active?.matches?.("[data-cart-quantity-decrease]") ? "decrease"
          : active?.matches?.("[data-cart-quantity-increase]") ? "increase"
            : active?.matches?.("[data-cart-quantity-input]") ? "quantity" : null;
      list.replaceChildren();
      let subtotalBani = 0;
      let canCheckout = state.catalog_ready && state.lines.length > 0;

      for (const line of state.lines) {
        const product = line.product;
        if (!product) {
          canCheckout = false;
          continue;
        }
        const valid = line.availability === "in_stock" && !line.over_stock;
        if (!valid) canCheckout = false;

        const fragment = template.content.cloneNode(true);
        const article = fragment.querySelector("[data-cart-line]");
        const productHref = product.slug
          ? `/product/${encodeURIComponent(product.slug)}`
          : `/product/${encodeURIComponent(product.id)}`;
        const imageLink = fragment.querySelector("[data-cart-product-link]");
        const image = fragment.querySelector("[data-cart-image]");
        const title = fragment.querySelector("[data-cart-title]");
        const category = fragment.querySelector("[data-cart-category]");
        const availability = fragment.querySelector("[data-cart-availability]");
        const unitPrice = fragment.querySelector("[data-cart-unit-price]");
        const lineTotal = fragment.querySelector("[data-cart-line-total]");
        const input = fragment.querySelector("[data-cart-quantity-input]");
        const decrease = fragment.querySelector("[data-cart-quantity-decrease]");
        const increase = fragment.querySelector("[data-cart-quantity-increase]");
        const remove = fragment.querySelector("[data-cart-remove]");

        imageLink.href = productHref;
        image.href = productHref;
        image.src = product.image_url || "";
        image.alt = product.name || "";
        title.href = productHref;
        title.textContent = product.name || "Produs fără nume";
        category.textContent = product.category?.name || "";
        unitPrice.textContent = window.NexoMoney.formatRon(product.price_bani);
        input.value = String(line.quantity);
        input.max = String(Math.min(99, Number.isInteger(product.stock_quantity) ? Math.max(product.stock_quantity, 1) : 99));
        input.setAttribute("aria-label", `Cantitate pentru ${product.name || "produs"}`);
        decrease.setAttribute("aria-label", `Scade cantitatea pentru ${product.name || "produs"}`);
        increase.setAttribute("aria-label", `Crește cantitatea pentru ${product.name || "produs"}`);
        remove.setAttribute("aria-label", `Elimină ${product.name || "produs"} din coș`);

        const message = line.availability === "unavailable"
          ? "Produs indisponibil. Elimină-l pentru a continua."
          : line.availability === "out_of_stock"
            ? "Stoc epuizat. Elimină produsul pentru a continua."
            : line.over_stock
              ? `Stoc disponibil: ${product.stock_quantity} bucăți. Redu cantitatea sau elimină produsul.`
              : `În stoc · ${product.stock_quantity} bucăți disponibile`;
        availability.textContent = message;
        availability.classList.toggle("is-unavailable", !valid);
        article.dataset.productId = product.id;
        article.dataset.availability = line.availability;
        decrease.disabled = line.quantity <= 1;
        increase.disabled = !valid || line.quantity >= 99 || line.quantity >= product.stock_quantity;

        if (valid) {
          const amount = product.price_bani * line.quantity;
          subtotalBani += amount;
          lineTotal.textContent = window.NexoMoney.formatRon(amount);
        } else {
          lineTotal.textContent = "—";
        }

        const changeQuantity = (quantity) => {
          const result = window.NexoCart.update(product.id, quantity);
          if (!result.ok) {
            showNotice(result.error);
            render(window.NexoCart.getState());
          }
          else showNotice(`Cantitatea pentru ${product.name || "produs"} a fost actualizată la ${quantity}.`);
        };
        decrease.addEventListener("click", () => changeQuantity(line.quantity - 1));
        increase.addEventListener("click", () => changeQuantity(line.quantity + 1));
        input.addEventListener("change", () => {
          const quantity = Number(input.value);
          if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99) {
            showNotice("Cantitatea trebuie să fie un număr întreg între 1 și 99.");
            render(window.NexoCart.getState());
            return;
          }
          changeQuantity(quantity);
        });
        input.addEventListener("keydown", (event) => {
          if (event.key === "Enter") input.blur();
        });
        remove.addEventListener("click", () => {
          const result = window.NexoCart.remove(product.id);
          showNotice(result.ok ? "Produsul a fost eliminat din coș." : result.error);
          if (result.ok) {
            requestAnimationFrame(() => {
              const next = list.querySelector("[data-cart-remove]");
              if (next) next.focus();
              else root.querySelector("#cart-page-title")?.focus();
            });
          }
        });
        list.append(fragment);
      }

      const isEmpty = state.lines.length === 0;
      empty.hidden = !isEmpty;
      subtotal.textContent = window.NexoMoney.formatRon(subtotalBani);
      total.textContent = window.NexoMoney.formatRon(subtotalBani);
      checkout.setAttribute("aria-disabled", String(!canCheckout));
      checkout.tabIndex = canCheckout ? 0 : -1;
      root.setAttribute("aria-busy", "false");
      if (activeAction && activeProductId && document.activeElement === document.body) {
        const nextLine = [...list.querySelectorAll("[data-product-id]")]
          .find((line) => line.dataset.productId === activeProductId);
        const selector = activeAction === "quantity" ? "[data-cart-quantity-input]"
          : activeAction === "remove" ? "[data-cart-remove]"
            : `[data-cart-quantity-${activeAction}]`;
        nextLine?.querySelector(selector)?.focus();
      }
    }

    checkout.addEventListener("click", (event) => {
      if (checkout.getAttribute("aria-disabled") === "true") {
        event.preventDefault();
        showNotice("Rezolvă produsele indisponibile și adaugă cel puțin un produs pentru a continua.");
      }
    });

    window.NexoCart.subscribe(render);
    render(window.NexoCart.getState());
    window.NexoCartCatalog?.hydrate().then(render).catch(() => {
      root.setAttribute("aria-busy", "false");
      showNotice("Catalogul nu a putut fi încărcat. Reîncearcă peste câteva momente.");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeCartPage, { once: true });
  } else {
    initializeCartPage();
  }
})();
