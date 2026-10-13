"use strict";

// Browser counterpart of app.domain.money: accepts integer bani only.
(() => {
  const formatter = new Intl.NumberFormat("ro-RO", {
    style: "currency",
    currency: "RON",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  window.NexoMoney = Object.freeze({
    formatRon(amountBani) {
      if (!Number.isSafeInteger(amountBani) || amountBani < 0) {
        throw new TypeError("Prețul trebuie să fie exprimat în bani întregi.");
      }
      return formatter.format(amountBani / 100);
    },
  });
})();
