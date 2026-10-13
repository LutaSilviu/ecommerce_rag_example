"use strict";

(() => {
  if (document.body.dataset.page !== "checkout-review") return;
  const host = document.querySelector("#page-content");
  if (!host) return;
  const draftKey = "nexo.checkout.address.v1";

  function make(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function showProblem(title, message, href, action) {
    host.classList.remove("placeholder-card");
    host.removeAttribute("aria-labelledby");
    host.replaceChildren();
    const section = make("section", "checkout-review__problem");
    section.setAttribute("role", "alert");
    section.append(make("h2", "", title), make("p", "", message));
    const link = make("a", "button button--secondary", action);
    link.href = href;
    section.append(link);
    host.append(section);
  }

  function optionalParts(address) {
    return [
      address.building && `Bloc ${address.building}`,
      address.entrance && `Scara ${address.entrance}`,
      address.floor && `Etaj ${address.floor}`,
      address.apartment && `Apartament ${address.apartment}`,
    ].filter(Boolean);
  }

  async function loadReview() {
    let address;
    try {
      address = JSON.parse(sessionStorage.getItem(draftKey) || "null");
    } catch {
      address = null;
    }
    if (!address || typeof address !== "object" || !address.recipient_name) {
      showProblem("Datele de livrare lipsesc", "Completează datele destinatarului înainte să revizuiești comanda.", "/checkout/details", "Completează datele");
      return;
    }
    try {
      const cart = await window.NexoCartCatalog.hydrate();
      const profileResponse = await fetch("/api/v1/auth/me", { headers: { Accept: "application/json" }, credentials: "same-origin" });
      if (!profileResponse.ok) throw new Error("Nu am putut verifica sesiunea contului.");
      const profile = await profileResponse.json();
      const lines = cart.lines || [];
      if (!lines.length) {
        showProblem("Coșul este gol", "Adaugă produse înainte să confirmi comanda.", "/search", "Descoperă produsele");
        return;
      }
      const invalid = lines.some((line) => line.checkout_blocked || !line.product || !Number.isSafeInteger(line.product.price_bani));
      if (invalid) {
        showProblem("Coșul necesită modificări", "Unul sau mai multe produse nu sunt disponibile în cantitatea aleasă. Revino în coș pentru a corecta produsele.", "/cart", "Editează coșul");
        return;
      }

      const subtotal = lines.reduce((sum, line) => sum + line.product.price_bani * line.quantity, 0);
      if (!Number.isSafeInteger(subtotal)) throw new Error("Totalul comenzii nu poate fi calculat în siguranță.");
      host.classList.remove("placeholder-card");
      host.removeAttribute("aria-labelledby");
      host.replaceChildren();

      const page = make("section", "checkout-review", undefined);
      page.setAttribute("aria-labelledby", "checkout-review-title");
      const intro = make("div", "checkout-review__intro");
      intro.append(make("p", "eyebrow", "Pasul 2 din 3"), make("h2", "", "Revizuiește comanda demonstrativă"), make("p", "", "Verifică produsele și datele înainte de confirmare."));
      intro.querySelector("h2").id = "checkout-review-title";
      page.append(intro);

      const itemsSection = make("section", "checkout-review__section");
      itemsSection.append(make("h3", "", "Produse"));
      const list = make("ul", "checkout-review__items");
      for (const line of lines) {
        const product = line.product;
        const item = make("li", "checkout-review__item");
        const image = make("img", "checkout-review__image");
        image.src = product.image_url || "";
        image.alt = product.name || "Produs";
        image.loading = "lazy";
        const detail = make("div", "checkout-review__item-detail");
        const name = make("a", "checkout-review__item-name", product.name || "Produs");
        name.href = `/product/${encodeURIComponent(product.slug || product.id)}`;
        detail.append(name, make("span", "", `${line.quantity} × ${window.NexoMoney.formatRon(product.price_bani)}`));
        const amount = make("strong", "", window.NexoMoney.formatRon(product.price_bani * line.quantity));
        item.append(image, detail, amount);
        list.append(item);
      }
      itemsSection.append(list);
      page.append(itemsSection);

      const addressSection = make("section", "checkout-review__section");
      addressSection.append(make("h3", "", "Destinatar și livrare"));
      const addressLines = [
        address.recipient_name,
        address.phone,
        profile.email || "Adresa de e-mail a contului nu este disponibilă",
        address.street_address,
        ...optionalParts(address),
        `${address.locality}, ${address.county}, ${address.postal_code}, România`,
      ];
      const addressList = make("div", "checkout-review__address");
      for (const value of addressLines) addressList.append(make("p", "", value));
      addressSection.append(addressList);
      const addressEdit = make("a", "text-link", "Editează datele de livrare");
      addressEdit.href = "/checkout/details";
      addressSection.append(addressEdit);
      page.append(addressSection);

      const summary = make("section", "checkout-review__summary");
      summary.append(make("h3", "", "Sumar"));
      const subtotalRow = make("div", "checkout-review__summary-row");
      subtotalRow.append(make("span", "", "Subtotal produse"), make("strong", "", window.NexoMoney.formatRon(subtotal)));
      const deliveryRow = make("div", "checkout-review__summary-row");
      deliveryRow.append(make("span", "", "Livrare"), make("span", "", "Neconfigurată în acest prototip"));
      const totalRow = make("div", "checkout-review__summary-row checkout-review__summary-row--total");
      totalRow.append(make("span", "", "Total comandă"), make("strong", "", window.NexoMoney.formatRon(subtotal)));
      summary.append(subtotalRow, deliveryRow, totalRow);
      page.append(summary);

      const payment = make("section", "checkout-review__payment");
      payment.append(make("h3", "", "Plată simulată (neprocesată)"), make("p", "", "Aceasta este o comandă de test. Confirmarea creează o înregistrare demonstrativă; nu se efectuează nicio plată și nu vei fi taxat(ă)."));
      page.append(payment);

      const actions = make("div", "checkout-review__actions");
      const backToCart = make("a", "button button--secondary", "Înapoi la coș");
      backToCart.href = "/cart";
      const confirm = make("button", "button button--primary", "Confirmă comanda demonstrativă");
      confirm.type = "button";
      confirm.dataset.orderConfirm = "";
      confirm.dataset.reviewFingerprint = lines.map((line) => `${line.product_id}:${line.quantity}:${line.product.price_bani}`).sort().join("|");
      confirm.setAttribute("aria-describedby", "checkout-review-payment-note");
      confirm.addEventListener("click", async () => {
        await window.NexoCheckoutGuards.submit(confirm, async (checked) => {
          const idempotencyKeyName = "nexo.checkout.idempotency.v1";
          // Reuse a key only when retrying this exact reviewed intent. A
          // changed cart or delivery address is a distinct confirmation.
          const intentPayload = JSON.stringify({ items: checked.items, address: checked.address });
          if (!window.crypto?.subtle) throw new Error("Browserul nu poate verifica solicitarea de confirmare. Reîncarcă pagina și încearcă din nou.");
          const intentBytes = new TextEncoder().encode(intentPayload);
          const intentDigest = await window.crypto.subtle.digest("SHA-256", intentBytes);
          const intent = Array.from(new Uint8Array(intentDigest), (byte) => byte.toString(16).padStart(2, "0")).join("");
          let savedIntent;
          try { savedIntent = JSON.parse(sessionStorage.getItem(idempotencyKeyName) || "null"); }
          catch { savedIntent = null; }
          let idempotencyKey = savedIntent?.intent === intent ? savedIntent.key : null;
          if (!idempotencyKey) {
            if (!window.crypto?.randomUUID) throw new Error("Browserul nu poate crea o confirmare sigură. Reîncarcă pagina și încearcă din nou.");
            idempotencyKey = window.crypto.randomUUID();
            sessionStorage.setItem(idempotencyKeyName, JSON.stringify({ key: idempotencyKey, intent }));
          }

          const response = await fetch("/api/v1/orders", {
            method: "POST",
            credentials: "same-origin",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
              "Idempotency-Key": idempotencyKey,
            },
            body: JSON.stringify({ items: checked.items, delivery_address: checked.address }),
          });
          const payload = await response.json().catch(() => null);
          if (!response.ok) {
            const detail = payload?.detail;
            const message = typeof detail === "string" ? detail : detail?.message;
            throw new Error(message || "Comanda nu a putut fi salvată. Datele și coșul au fost păstrate; poți încerca din nou.");
          }
          if (!payload || typeof payload.order_number !== "string" || !payload.order_number) {
            throw new Error("Comanda a fost trimisă, dar răspunsul nu conține numărul comenzii. Reîncearcă pentru a verifica aceeași solicitare.");
          }

          window.NexoCart.clear();
          sessionStorage.removeItem(draftKey);
          sessionStorage.removeItem(idempotencyKeyName);
          window.location.assign(`/checkout/confirmation/${encodeURIComponent(payload.order_number)}`);
          return { navigating: true };
        });
      });
      actions.append(backToCart, confirm);
      actions.append(make("p", "checkout-review__payment-note", "Fără plată reală"));
      actions.lastChild.id = "checkout-review-payment-note";
      page.append(actions);
      host.append(page);
    } catch (error) {
      showProblem("Nu am putut încărca revizuirea", error instanceof Error ? error.message : "Încearcă din nou.", "/cart", "Revino la coș");
    }
  }

  loadReview();
})();
