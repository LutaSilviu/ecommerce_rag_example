"use strict";

(() => {
  if (document.body.dataset.page !== "orders") return;
  const host = document.querySelector("#page-content");
  if (!host) return;
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const resetHost = () => {
    host.classList.remove("placeholder-card");
    host.removeAttribute("aria-labelledby");
    host.replaceChildren();
  };

  function showError() {
    resetHost();
    const card = make("section", "order-page__panel order-page__error");
    card.setAttribute("role", "alert");
    card.append(make("h2", "", "Comenzile nu sunt disponibile momentan"));
    card.append(make("p", "", "Verifică legătura la internet și încearcă din nou."));
    const retry = make("button", "button button--secondary", "Încearcă din nou");
    retry.type = "button";
    retry.addEventListener("click", load);
    card.append(retry);
    host.append(card);
  }

  function showEmpty() {
    resetHost();
    const card = make("section", "order-page__panel order-page__error");
    card.append(make("h2", "", "Nu ai încă nicio comandă"));
    card.append(make("p", "", "Comenzile tale vor apărea aici după ce confirmi o comandă."));
    const shop = make("a", "button button--primary", "Descoperă produsele");
    shop.href = "/search";
    card.append(shop);
    host.append(card);
  }

  async function load() {
    resetHost();
    host.setAttribute("aria-busy", "true");
    const loading = make("p", "order-page__loading", "Se încarcă comenzile…");
    loading.setAttribute("role", "status");
    host.append(loading);
    try {
      const response = await fetch("/api/v1/orders", {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Orders unavailable");
      const orders = await response.json();
      if (!Array.isArray(orders)) throw new Error("Invalid orders response");
      host.removeAttribute("aria-busy");
      if (!orders.length) return showEmpty();

      resetHost();
      const list = make("div", "order-history");
      list.setAttribute("aria-label", "Istoricul comenzilor");
      for (const order of orders) {
        const card = make("article", "order-page__panel order-history__card");
        const heading = make("div", "order-history__heading");
        heading.append(make("h2", "", `Comanda ${order.order_number}`));
        const detailsLink = make("a", "text-link", "Vezi detaliile");
        detailsLink.href = `/account/orders/${encodeURIComponent(order.order_number)}`;
        heading.append(detailsLink);
        card.append(heading);

        const date = new Intl.DateTimeFormat("ro-RO", { dateStyle: "medium", timeStyle: "short" }).format(new Date(order.created_at));
        const orderStatus = order.status === "registered" ? "Înregistrată" : "Actualizată";
        const details = make("dl", "order-history__details");
        for (const [label, value] of [
          ["Data", date],
          ["Produse", String(order.items.length)],
          ["Status", orderStatus],
          ["Plată", "Plată simulată — neprocesată"],
        ]) {
          const row = make("div", "");
          row.append(make("dt", "", label), make("dd", "", value));
          details.append(row);
        }
        card.append(details);
        const total = make("p", "order-history__total");
        total.append(make("span", "", "Total comandă"));
        total.append(make("strong", "", window.NexoMoney.formatRon(order.total_bani)));
        card.append(total);
        list.append(card);
      }
      host.append(list);
    } catch {
      host.removeAttribute("aria-busy");
      showError();
    }
  }

  void load();
})();
