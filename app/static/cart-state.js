"use strict";

// Browser-only cart state. Persist identity and quantity only; product facts
// are always supplied by the current catalog and are never trusted from disk.
(() => {
  const STORAGE_KEY = "nexo-market.cart.v1";
  const STORAGE_VERSION = 1;
  const MIN_QUANTITY = 1;
  const MAX_QUANTITY = 99;
  const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const events = new EventTarget();

  let productsById = new Map();
  let catalogReady = false;
  let storageAvailable = true;
  let lines = [];

  const copyLines = () => lines.map((line) => ({
    product_id: line.product_id,
    quantity: line.quantity,
  }));

  function productState(product) {
    if (!product) return "unknown";
    if (product.is_active === false) return "unavailable";
    if (Number(product.stock_quantity) <= 0) return "out_of_stock";
    return "in_stock";
  }

  function validateLine(productId, quantity) {
    if (typeof productId !== "string" || !UUID_PATTERN.test(productId)) {
      return "Identificatorul produsului nu este valid.";
    }
    if (!Number.isInteger(quantity) || quantity < MIN_QUANTITY || quantity > MAX_QUANTITY) {
      return "Cantitatea trebuie să fie între 1 și 99.";
    }
    return null;
  }

  function parsePersistedLines() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const stored = JSON.parse(raw);
      if (!stored || stored.version !== STORAGE_VERSION || !Array.isArray(stored.lines)) return [];

      const seen = new Set();
      return stored.lines.flatMap((line) => {
        if (!line || typeof line !== "object") return [];
        const productId = line.product_id;
        const quantity = line.quantity;
        if (validateLine(productId, quantity) || seen.has(productId)) return [];
        if (catalogReady && !productsById.has(productId)) return [];
        seen.add(productId);
        return [{ product_id: productId, quantity }];
      });
    } catch (_error) {
      // Malformed JSON, blocked storage, or a browser privacy mode must not
      // prevent the storefront from loading. Use an in-memory empty cart.
      storageAvailable = false;
      return [];
    }
  }

  function persist() {
    if (!storageAvailable) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        version: STORAGE_VERSION,
        lines: copyLines(),
      }));
    } catch (_error) {
      storageAvailable = false;
    }
  }

  function publish() {
    const state = getState();
    events.dispatchEvent(new CustomEvent("change", { detail: state }));
  }

  function reconcileAgainstCatalog() {
    if (!catalogReady) return;
    lines = lines.filter((line) => productsById.has(line.product_id));
  }

  function getState() {
    const currentLines = copyLines().map((line) => {
      const product = productsById.get(line.product_id) || null;
      const availability = catalogReady ? productState(product) : "unknown";
      const stockQuantity = product && Number.isInteger(product.stock_quantity)
        ? product.stock_quantity
        : null;
      const overStock = stockQuantity !== null && line.quantity > stockQuantity;
      return {
        ...line,
        product: product ? { ...product } : null,
        availability,
        over_stock: overStock,
        checkout_blocked: availability !== "in_stock" || overStock,
      };
    });
    return Object.freeze({
      lines: currentLines,
      item_count: currentLines.reduce((sum, line) => sum + line.quantity, 0),
      catalog_ready: catalogReady,
      storage_available: storageAvailable,
    });
  }

  function result(ok, error = null) {
    return { ok, error, state: getState() };
  }

  function add(productId, amount = 1) {
    const validation = validateLine(productId, amount);
    if (validation) return result(false, validation);
    if (catalogReady && !productsById.has(productId)) {
      return result(false, "Produsul nu mai este disponibil în catalog.");
    }

    const product = productsById.get(productId);
    if (product && productState(product) !== "in_stock") {
      return result(false, "Produsul nu este disponibil momentan.");
    }

    const existing = lines.find((line) => line.product_id === productId);
    const nextQuantity = (existing ? existing.quantity : 0) + amount;
    if (nextQuantity > MAX_QUANTITY) {
      return result(false, "Poți adăuga cel mult 99 de bucăți dintr-un produs.");
    }
    if (product && nextQuantity > product.stock_quantity) {
      return result(false, `Stoc disponibil: ${product.stock_quantity} bucăți.`);
    }

    if (existing) existing.quantity = nextQuantity;
    else lines.push({ product_id: productId, quantity: amount });
    persist();
    publish();
    return result(true);
  }

  function update(productId, quantity) {
    const validation = validateLine(productId, quantity);
    if (validation) return result(false, validation);
    const existing = lines.find((line) => line.product_id === productId);
    if (!existing) return result(false, "Produsul nu se află în coș.");

    const product = productsById.get(productId);
    // Lowering quantity is always allowed, including when stock or product
    // availability changed after the item was added.
    if (quantity > existing.quantity) {
      if (catalogReady && !product) return result(false, "Produsul nu mai este disponibil în catalog.");
      if (product && productState(product) !== "in_stock") {
        return result(false, "Produsul nu este disponibil momentan.");
      }
      if (product && quantity > product.stock_quantity) {
        return result(false, `Stoc disponibil: ${product.stock_quantity} bucăți.`);
      }
    }

    existing.quantity = quantity;
    persist();
    publish();
    return result(true);
  }

  function remove(productId) {
    const nextLines = lines.filter((line) => line.product_id !== productId);
    if (nextLines.length === lines.length) return result(false, "Produsul nu se află în coș.");
    lines = nextLines;
    persist();
    publish();
    return result(true);
  }

  function clear() {
    lines = [];
    persist();
    publish();
    return result(true);
  }

  function setProducts(products) {
    if (!Array.isArray(products)) throw new TypeError("Catalogul trebuie să fie o listă de produse.");
    productsById = new Map();
    for (const product of products) {
      if (!product || typeof product.id !== "string" || !UUID_PATTERN.test(product.id)) continue;
      productsById.set(product.id, { ...product });
    }
    catalogReady = true;
    lines = parsePersistedLines();
    reconcileAgainstCatalog();
    // Rewrite only the sanitized shape after catalog IDs have been checked.
    persist();
    publish();
    return getState();
  }

  function refreshProducts(products) {
    if (!Array.isArray(products)) throw new TypeError("Catalogul trebuie să fie o listă de produse.");
    productsById = new Map();
    for (const product of products) {
      if (!product || typeof product.id !== "string" || !UUID_PATTERN.test(product.id)) continue;
      productsById.set(product.id, { ...product });
    }
    catalogReady = true;
    reconcileAgainstCatalog();
    publish();
    return getState();
  }

  function reconcileAfterAuth() {
    // This prototype has no account-scoped cart. Keep the browser cart as the
    // canonical cart across email/Google redirects; never replace it with an
    // empty server cart or merge account data that does not exist. Catalog
    // reconciliation removes only unknown IDs and preserves unavailable or
    // over-stock lines for the shopper to fix explicitly.
    reconcileAgainstCatalog();
    persist();
    publish();
    return getState();
  }

  // Read defensively now so callers can render immediately. Catalog-aware
  // hydration happens when setProducts is called by the catalog consumer.
  lines = parsePersistedLines();

  window.NexoCart = Object.freeze({
    getState,
    subscribe(listener) {
      if (typeof listener !== "function") throw new TypeError("Listenerul trebuie să fie o funcție.");
      const handler = (event) => listener(event.detail);
      events.addEventListener("change", handler);
      return () => events.removeEventListener("change", handler);
    },
    setProducts,
    refreshProducts,
    reconcileAfterAuth,
    add,
    update,
    remove,
    clear,
  });
})();
