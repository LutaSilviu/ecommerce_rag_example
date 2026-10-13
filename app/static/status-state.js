"use strict";

// Reusable Romanian status regions for pages and async catalog operations.
// Include this script before the page-specific script, then call
// NexoStatus.mount(container, NexoStatus.loading(...)) as needed.
(() => {
  const defaults = {
    loading: { title: "Se încarcă", message: "Te rugăm să aștepți.", icon: "…" },
    empty: { title: "Nu există rezultate", message: "Încearcă să modifici filtrele sau caută altceva.", icon: "—" },
    error: { title: "A apărut o eroare", message: "Nu am putut încărca informațiile. Încearcă din nou.", icon: "!" },
  };

  function create(type, options = {}) {
    if (!Object.hasOwn(defaults, type)) throw new TypeError(`Tip de stare necunoscut: ${type}`);
    const copy = { ...defaults[type], ...options };
    const section = document.createElement("section");
    section.className = `status-state status-state--${type}`;
    section.dataset.statusState = type;
    section.setAttribute("role", type === "error" ? "alert" : "status");
    section.setAttribute("aria-live", type === "error" ? "assertive" : "polite");
    section.setAttribute("aria-atomic", "true");

    const icon = document.createElement("span");
    icon.className = "status-state__icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = copy.icon;

    const content = document.createElement("div");
    content.className = "status-state__content";
    const heading = document.createElement("h2");
    heading.className = "status-state__title";
    heading.textContent = copy.title;
    const message = document.createElement("p");
    message.className = "status-state__message";
    message.textContent = copy.message;
    content.append(heading, message);
    section.append(icon, content);

    if (typeof copy.onAction === "function" && copy.actionLabel) {
      const action = document.createElement("button");
      action.className = "button button--secondary status-state__action";
      action.type = "button";
      action.textContent = copy.actionLabel;
      action.addEventListener("click", copy.onAction);
      section.append(action);
    }
    if (type === "loading") section.setAttribute("aria-busy", "true");
    return section;
  }

  function mount(container, state) {
    if (!(container instanceof Element)) throw new TypeError("Este necesar un container HTML.");
    const element = typeof state === "string" ? create(state) : create(state.type, state);
    container.replaceChildren(element);
    return element;
  }

  window.NexoStatus = Object.freeze({
    create,
    mount,
    loading: (options = {}) => ({ type: "loading", ...options }),
    empty: (options = {}) => ({ type: "empty", ...options }),
    error: (options = {}) => ({ type: "error", ...options }),
    clear: (container) => container?.replaceChildren(),
  });
})();
