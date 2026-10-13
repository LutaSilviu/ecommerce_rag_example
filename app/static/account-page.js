"use strict";

// The only profile source is the same-origin /auth/me result already held by
// NexoAuthState. This page never reads the session cookie or other credentials.
(() => {
  if (document.body.dataset.page !== "account") return;

  const host = document.querySelector("#page-content");
  if (!host) return;

  function render(state) {
    if (!state || state.status === "loading") {
      host.setAttribute("aria-busy", "true");
      host.innerHTML = '<div class="account-state" role="status"><span class="account-spinner" aria-hidden="true"></span><div><h2>Se verifică sesiunea</h2><p>Încărcăm datele contului tău.</p></div></div>';
      return;
    }

    host.removeAttribute("aria-busy");
    if (state.status === "error") {
      host.innerHTML = '<div class="account-state account-state--error" role="alert"><div><h2>Contul nu este disponibil momentan</h2><p data-account-error></p><button class="button button--secondary" type="button" data-account-retry>Încearcă din nou</button></div></div>';
      host.querySelector("[data-account-error]").textContent = state.error || "A apărut o eroare. Încearcă din nou.";
      host.querySelector("[data-account-retry]").addEventListener("click", () => void window.NexoAuthState?.load());
      return;
    }

    if (state.status !== "authenticated" || !state.user) {
      host.innerHTML = '<div class="account-state"><div><h2>Autentifică-te pentru a-ți vedea contul</h2><p>Contul tău îți păstrează comenzile și detaliile pentru cumpărături.</p><div class="account-actions"><a class="button button--primary" href="/login?return_to=%2Faccount">Intră în cont</a><a class="button button--secondary" href="/register?return_to=%2Faccount">Creează un cont</a></div></div></div>';
      return;
    }

    const user = state.user;
    const name = typeof user.display_name === "string" && user.display_name.trim()
      ? user.display_name.trim()
      : "Client Nexo";
    const email = typeof user.email === "string" ? user.email : "Adresă indisponibilă";
    host.innerHTML = `
      <section class="account-card" aria-labelledby="account-profile-title">
        <div class="account-card__heading">
          <div class="account-avatar" aria-hidden="true"></div>
          <div><p class="eyebrow">Profilul meu</p><h2 id="account-profile-title" data-account-name></h2></div>
          <span class="account-status"><span aria-hidden="true"></span>Cont activ</span>
        </div>
        <dl class="account-details">
          <div><dt>Adresă de e-mail</dt><dd data-account-email></dd></div>
          <div><dt>Furnizor de autentificare</dt><dd>Indisponibil în profilul curent</dd></div>
          <div><dt>Starea contului</dt><dd>Autentificat și activ</dd></div>
        </dl>
        <p class="account-provider-note">Furnizorul exact de autentificare nu este inclus în profilul disponibil.</p>
        <div class="account-card__footer">
          <a class="text-link" href="/account/orders">Vezi comenzile mele <span aria-hidden="true">→</span></a>
          <button class="button button--secondary" type="button" data-account-sign-out>Ieși din cont</button>
        </div>
        <p class="account-sign-out-message" data-account-sign-out-message role="status" aria-live="polite"></p>
      </section>`;
    host.querySelector("[data-account-name]").textContent = name;
    host.querySelector("[data-account-email]").textContent = email;
    host.querySelector(".account-avatar").textContent = name.trim().charAt(0).toLocaleUpperCase("ro-RO");
    const signOutButton = host.querySelector("[data-account-sign-out]");
    const signOutMessage = host.querySelector("[data-account-sign-out-message]");
    signOutButton.addEventListener("click", async () => {
      if (signOutButton.disabled) return;
      signOutButton.disabled = true;
      signOutButton.setAttribute("aria-busy", "true");
      signOutMessage.textContent = "Se închide sesiunea…";

      try {
        const response = await fetch("/api/v1/auth/logout", {
          method: "POST",
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          let message = "Deconectarea nu a reușit. Încearcă din nou.";
          try {
            const body = await response.json();
            if (typeof body.detail === "string") message = body.detail;
          } catch {
            // Keep the safe fallback when the server did not return JSON.
          }
          throw new Error(message);
        }

        // Checkout addresses are personal data. Keep the anonymous product
        // cart across sign-out, but discard the previous customer's draft.
        sessionStorage.removeItem("nexo.checkout.address.v1");
        sessionStorage.removeItem("nexo.checkout.idempotency.v1");

        // Reload only the auth state; the anonymous NexoCart store is untouched.
        await window.NexoAuthState?.load();
        window.location.assign("/");
      } catch (error) {
        signOutMessage.textContent = error instanceof Error
          ? error.message
          : "Deconectarea nu a reușit. Încearcă din nou.";
        signOutButton.disabled = false;
        signOutButton.removeAttribute("aria-busy");
      }
    });
  }

  if (window.NexoAuthState) {
    render(window.NexoAuthState.getState());
    window.NexoAuthState.subscribe(render);
  } else {
    render({ status: "error", error: "Starea autentificării nu s-a putut încărca." });
  }
})();
