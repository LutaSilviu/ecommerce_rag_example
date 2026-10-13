"use strict";

(() => {
  if (document.body.dataset.page !== "confirmation") return;
  const host = document.querySelector("#page-content");
  if (!host) return;

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const showError = (message) => {
    const panel = el("section", "order-page__panel order-page__error");
    panel.setAttribute("role", "alert");
    panel.append(el("h2", "", "Nu am putut încărca această comandă"), el("p", "", message));
    const link = el("a", "button button--secondary", "Vezi comenzile mele");
    link.href = "/account/orders";
    panel.append(link);
    host.classList.remove("placeholder-card");
    host.removeAttribute("aria-labelledby");
    host.replaceChildren(panel);
  };
  const optionalAddress = (address) => [
    address.building && `Bloc ${address.building}`,
    address.entrance && `Scara ${address.entrance}`,
    address.floor && `Etaj ${address.floor}`,
    address.apartment && `Apartament ${address.apartment}`,
  ].filter(Boolean);

  async function load() {
    const orderNumber = decodeURIComponent(window.location.pathname.split("/").filter(Boolean).at(-1) || "");
    try {
      const response = await fetch(`/api/v1/orders/${encodeURIComponent(orderNumber)}`, {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (response.status === 404) return showError("Comanda nu există sau nu este disponibilă în contul tău.");
      if (!response.ok) throw new Error("Încearcă din nou peste câteva momente.");
      const order = await response.json();

      const page = el("section", "order-page");
      page.setAttribute("aria-labelledby", "order-confirmation-title");
      const hero = el("header", "order-page__hero");
      hero.append(el("p", "eyebrow", "Comandă demonstrativă"));
      hero.append(el("h2", "", "Comanda ta de test a fost salvată în cont"));
      const number = el("p", "order-page__number", `Număr comandă: ${order.order_number}`);
      hero.append(number, el("p", "", "Nu s-a efectuat nicio plată și nu ți se vor cere date de card."));
      hero.querySelector("h2").id = "order-confirmation-title";
      page.append(hero);

      const details = el("div", "order-page__grid");
      const products = el("section", "order-page__panel");
      products.append(el("h3", "", "Produse comandate"));
      const list = el("ul", "order-page__items");
      for (const item of order.items) {
        const row = el("li", "order-page__item");
        const main = el("div", "");
        main.append(el("strong", "", item.name), el("span", "", `${item.quantity} × ${window.NexoMoney.formatRon(item.unit_price_bani)}`));
        row.append(main, el("strong", "", window.NexoMoney.formatRon(item.line_total_bani)));
        list.append(row);
      }
      products.append(list);
      details.append(products);

      const delivery = el("section", "order-page__panel");
      delivery.append(el("h3", "", "Livrare"));
      const address = order.delivery_address;
      const addressLines = [address.recipient_name, address.phone, address.street_address, ...optionalAddress(address), `${address.locality}, ${address.county}, ${address.postal_code}, România`];
      const addressBlock = el("div", "order-page__address");
      addressLines.forEach((line) => addressBlock.append(el("p", "", line)));
      delivery.append(addressBlock);
      details.append(delivery);
      page.append(details);

      const summary = el("section", "order-page__panel order-page__summary");
      summary.append(el("h3", "", "Sumar comandă"));
      const createdAt = new Intl.DateTimeFormat("ro-RO", { dateStyle: "long", timeStyle: "short" }).format(new Date(order.created_at));
      const status = order.status === "registered" ? "Înregistrată" : "Actualizată";
      summary.append(el("p", "", `Data: ${createdAt}`), el("p", "", `Status comandă: ${status}`), el("p", "", "Plată simulată: neprocesată; nu s-a retras nicio sumă."));
      const total = el("div", "order-page__total");
      total.append(el("span", "", "Total comandă"), el("strong", "", window.NexoMoney.formatRon(order.total_bani)));
      summary.append(total);
      page.append(summary);

      const actions = el("nav", "order-page__actions");
      actions.setAttribute("aria-label", "Pașii următori");
      const ordersLink = el("a", "button button--primary", "Vezi comenzile mele");
      ordersLink.href = "/account/orders";
      const shopLink = el("a", "button button--secondary", "Continuă cumpărăturile");
      shopLink.href = "/search";
      actions.append(ordersLink, shopLink);
      page.append(actions);
      host.classList.remove("placeholder-card");
      host.removeAttribute("aria-labelledby");
      host.replaceChildren(page);
    } catch {
      showError("A apărut o problemă de conexiune. Reîncarcă pagina pentru a încerca din nou.");
    }
  }
  load();
})();
