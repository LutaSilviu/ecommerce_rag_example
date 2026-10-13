"use strict";

// Same-origin session status only. JavaScript never reads the HttpOnly cookie
// and never stores a session token.
(() => {
  const events = new EventTarget();
  let state = { status: "loading", user: null, error: null };

  function publish(next) {
    state = Object.freeze(next);
    events.dispatchEvent(new CustomEvent("change", { detail: state }));
  }

  async function load() {
    publish({ status: "loading", user: null, error: null });
    try {
      const response = await fetch("/api/v1/auth/me", {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      if (response.status === 401) {
        publish({ status: "anonymous", user: null, error: null });
        return state;
      }
      if (!response.ok) throw new Error("Nu am putut verifica sesiunea.");
      const user = await response.json();
      publish({ status: "authenticated", user, error: null });
    } catch (error) {
      publish({
        status: "error",
        user: null,
        error: error instanceof Error ? error.message : "A apărut o eroare.",
      });
    }
    return state;
  }

  window.NexoAuthState = Object.freeze({
    getState: () => state,
    subscribe(listener) {
      const handler = (event) => listener(event.detail);
      events.addEventListener("change", handler);
      return () => events.removeEventListener("change", handler);
    },
    load,
  });

  void load();
})();
