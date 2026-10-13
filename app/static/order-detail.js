"use strict";

(() => {
  if (document.body.dataset.page !== "order-detail") return;
  const host = document.querySelector("#page-content");
  if (!host) return;

  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const addressOptionalLines = (address) => [
    address.building && `Bloc ${address.building}`,
    address.entrance && `Scara ${address.entrance}`,
    address.floor && `Etaj ${address.floor}`,
    address.apartment && `Apartament ${address.apartment}`,
  ].filter(Boolean);

  function renderError(message) {
    const panel = make("section", "order-page__panel order-page__error");
    panel.setAttribute("role", "alert");
    panel.append(make("h2", "", "Nu am putut încărca această comandă"));
    panel.append(make("p", "", message));
    const link = make("a", "button button--secondary", "Vezi comenzile mele");
    link.href = "/account/orders";
    panel.append(link);
    host.classList.remove("placeholder-card");
    host.removeAttribute("aria-labelledby");
    host.replaceChildren(panel);
  }

  function renderOrder(order) {
    const page = make("section", "order-page");
    page.setAttribute("aria-labelledby", "order-detail-title");
    const header = make("header", "order-page__hero");
    header.append(make("p", "eyebrow", "Detalii comandă"));
    const title = make("h2", "", `Comanda ${order.order_number}`);
    title.id = "order-detail-title";
    header.append(title);
    header.append(make("p", "", "Aceasta este înregistrarea salvată la confirmarea comenzii."));
    page.append(header);

    const grid = make("div", "order-page__grid");
    const itemsPanel = make("section", "order-page__panel");
    itemsPanel.append(make("h3", "", "Produse comandate"));
    const list = make("ul", "order-page__items");
    for (const item of order.items) {
      const row = make("li", "order-page__item");
      const details = make("div", "");
      details.append(make("strong", "", item.name));
      details.append(make("span", "", `${item.quantity} × ${window.NexoMoney.formatRon(item.unit_price_bani)} / buc.`));
      row.append(details, make("strong", "", window.NexoMoney.formatRon(item.line_total_bani)));
      list.append(row);
    }
    itemsPanel.append(list);
    grid.append(itemsPanel);

    const deliveryPanel = make("section", "order-page__panel");
    deliveryPanel.append(make("h3", "", "Adresă de livrare"));
    const address = order.delivery_address;
    const addressBlock = make("div", "order-page__address");
    [address.recipient_name, address.phone, address.street_address, ...addressOptionalLines(address), `${address.locality}, ${address.county}, ${address.postal_code}, România`]
      .forEach((line) => addressBlock.append(make("p", "", line)));
    deliveryPanel.append(addressBlock);
    grid.append(deliveryPanel);
    page.append(grid);

    const summary = make("section", "order-page__panel order-page__summary");
    summary.append(make("h3", "", "Sumar comandă"));
    const createdAt = new Intl.DateTimeFormat("ro-RO", { dateStyle: "long", timeStyle: "short" }).format(new Date(order.created_at));
    summary.append(make("p", "", `Data înregistrării: ${createdAt}`));
    summary.append(make("p", "", `Status comandă: ${order.status === "registered" ? "Înregistrată" : order.status}`));
    summary.append(make("p", "", `Plată: ${order.payment?.method === "simulated" ? "simulată" : "demonstrativă"} · ${order.payment?.status === "not_processed" ? "neprocesată; nu s-a retras nicio sumă" : "fără tranzacție reală"}.`));
    const totals = make("dl", "order-detail__totals");
    for (const [label, value] of [
      ["Subtotal produse", order.subtotal_bani],
      ["Livrare", order.shipping_bani],
      ["Total comandă", order.total_bani],
    ]) {
      const row = make("div", "");
      row.append(make("dt", "", label), make("dd", "", window.NexoMoney.formatRon(value)));
      totals.append(row);
    }
    summary.append(totals);
    page.append(summary);

    const actions = make("nav", "order-page__actions");
    actions.setAttribute("aria-label", "Navigare comenzi");
    const history = make("a", "button button--primary", "Înapoi la comenzile mele");
    history.href = "/account/orders";
    const shop = make("a", "button button--secondary", "Continuă cumpărăturile");
    shop.href = "/search";
    actions.append(history, shop);
    page.append(actions);
    host.classList.remove("placeholder-card");
    host.removeAttribute("aria-labelledby");
    host.replaceChildren(page);
  }

  async function load() {
    const orderNumber = decodeURIComponent(window.location.pathname.split("/").filter(Boolean).at(-1) || "");
    try {
      const response = await fetch(`/api/v1/orders/${encodeURIComponent(orderNumber)}`, {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (response.status === 404) return renderError("Comanda nu există sau nu este disponibilă în contul tău.");
      if (!response.ok) throw new Error("Order unavailable");
      const order = await response.json();
      if (!Array.isArray(order.items) || !order.delivery_address || !order.payment) throw new Error("Invalid order response");
      renderOrder(order);
    } catch {
      renderError("A apărut o problemă de conexiune. Reîncarcă pagina pentru a încerca din nou.");
    }
  }

  void load();
})();
