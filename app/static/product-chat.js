"use strict";

(() => {
  const launcher = document.querySelector(".product-chat-launcher");
  const dialog = document.querySelector("#product-chat-dialog");
  const closeButton = dialog?.querySelector(".product-chat__close");
  const form = dialog?.querySelector(".product-chat__form");
  const input = dialog?.querySelector("#product-chat-input");
  const messages = dialog?.querySelector(".product-chat__messages");
  const status = dialog?.querySelector(".product-chat__status");
  if (!launcher || !dialog || !form || !input || !messages || !status) return;

  const history = [];
  let pending = false;
  let catalogProducts = [];

  // Product names and slugs come from the catalog API. Build links with DOM
  // APIs only so assistant text is always treated as untrusted plain text.
  const catalogReady = fetch("/api/v1/catalog/products", { headers: { Accept: "application/json" } })
    .then((response) => (response.ok ? response.json() : []))
    .then((products) => {
      if (Array.isArray(products)) {
        catalogProducts = products
          .filter((product) => typeof product.name === "string"
            && typeof product.slug === "string"
            && /^[a-z0-9-]+$/.test(product.slug))
          .sort((left, right) => right.name.length - left.name.length);
      }
    })
    .catch(() => {});

  function addMessage(role, content) {
    const bubble = document.createElement("p");
    bubble.className = `product-chat__bubble product-chat__bubble--${role}`;
    bubble.textContent = content;
    messages.append(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }

  function renderAssistantAnswer(bubble, content) {
    const text = String(content ?? "");
    const matches = [];
    for (const product of catalogProducts) {
      const escaped = product.name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const expression = new RegExp(escaped, "giu");
      for (const match of text.matchAll(expression)) {
        const start = match.index;
        const end = start + match[0].length;
        if (!matches.some((item) => start < item.end && end > item.start)) {
          matches.push({ start, end, product });
        }
      }
    }
    matches.sort((left, right) => left.start - right.start);
    const nodes = [];
    let cursor = 0;
    for (const match of matches) {
      if (match.start > cursor) nodes.push(document.createTextNode(text.slice(cursor, match.start)));
      const link = document.createElement("a");
      link.href = `/product/${encodeURIComponent(match.product.slug)}`;
      link.textContent = text.slice(match.start, match.end);
      link.className = "product-chat__product-link";
      nodes.push(link);
      cursor = match.end;
    }
    if (cursor < text.length || nodes.length === 0) nodes.push(document.createTextNode(text.slice(cursor)));
    bubble.replaceChildren(...nodes);
  }

  launcher.addEventListener("click", () => {
    if (!dialog.open) dialog.showModal();
    input.focus();
  });
  closeButton?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || pending) return;
    pending = true;
    input.value = "";
    input.disabled = true;
    form.querySelector("button[type=submit]").disabled = true;
    status.textContent = "Se caută în catalog…";
    addMessage("user", message);
    const thinking = addMessage("assistant", "Se pregătește răspunsul…");
    try {
      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ message, history: history.slice(-6) }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Chatul nu este disponibil momentan.");
      await catalogReady;
      renderAssistantAnswer(thinking, payload.answer);
      history.push({ role: "user", content: message }, { role: "assistant", content: payload.answer });
      if (history.length > 6) history.splice(0, history.length - 6);
      status.textContent = "";
    } catch (error) {
      thinking.textContent = error.message || "Nu am putut obține un răspuns. Încearcă din nou.";
      status.textContent = "Verifică dacă asistentul AI este configurat și încearcă din nou.";
    } finally {
      pending = false;
      input.disabled = false;
      form.querySelector("button[type=submit]").disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  });
})();
