"use strict";

(() => {
  if (document.body.dataset.page !== "checkout-details") return;
  const host = document.querySelector("#page-content");
  if (!host) return;

  const draftKey = "nexo.checkout.address.v1";
  host.classList.remove("placeholder-card");
  host.removeAttribute("aria-labelledby");
  host.innerHTML = `
    <section class="checkout-details" aria-labelledby="checkout-details-title">
      <div class="checkout-details__intro">
        <p class="eyebrow">Pasul 1 din 3</p>
        <h2 id="checkout-details-title">Date de livrare</h2>
        <p>Completează datele destinatarului și adresa din România.</p>
      </div>
      <section class="checkout-payment" aria-labelledby="checkout-payment-title">
        <p class="eyebrow">Metodă de plată</p>
        <h3 id="checkout-payment-title">Plată simulată (prototip)</h3>
        <p>Aceasta este o simulare. Nu se procesează nicio plată și nu ți se vor cere date de card.</p>
        <p class="checkout-payment__help">Comanda va fi salvată doar ca înregistrare demonstrativă în contul tău.</p>
      </section>
      <form class="checkout-form" data-checkout-address-form novalidate>
        <p class="checkout-form__error" data-form-error role="alert" hidden></p>
        <div class="checkout-form__grid">
          <label class="checkout-field checkout-field--wide" for="recipient_name">
            <span>Numele destinatarului</span>
            <input id="recipient_name" name="recipient_name" autocomplete="name" minlength="2" maxlength="120" required aria-describedby="recipient_name-error">
            <span class="checkout-field__error" id="recipient_name-error" hidden></span>
          </label>
          <label class="checkout-field" for="phone">
            <span>Telefon</span>
            <input id="phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" maxlength="24" required aria-describedby="phone-error">
            <span class="checkout-field__error" id="phone-error" hidden></span>
          </label>
          <div class="checkout-field" aria-live="polite">
            <span>Adresa de e-mail a contului</span>
            <output class="checkout-field__readonly" data-checkout-email>Se încarcă…</output>
            <small>Folosim adresa de e-mail a contului pentru comunicările despre comandă.</small>
          </div>
          <label class="checkout-field" for="county">
            <span>Județ</span>
            <input id="county" name="county" autocomplete="address-level1" minlength="2" maxlength="80" required aria-describedby="county-error">
            <span class="checkout-field__error" id="county-error" hidden></span>
          </label>
          <label class="checkout-field" for="locality">
            <span>Localitate</span>
            <input id="locality" name="locality" autocomplete="address-level2" maxlength="100" required aria-describedby="locality-error">
            <span class="checkout-field__error" id="locality-error" hidden></span>
          </label>
          <label class="checkout-field checkout-field--wide" for="street_address">
            <span>Stradă și număr</span>
            <input id="street_address" name="street_address" autocomplete="street-address" minlength="3" maxlength="200" required aria-describedby="street_address-error">
            <span class="checkout-field__error" id="street_address-error" hidden></span>
          </label>
          <label class="checkout-field" for="building">
            <span>Bloc <small>(opțional)</small></span>
            <input id="building" name="building" autocomplete="address-line2" maxlength="30" aria-describedby="building-error">
            <span class="checkout-field__error" id="building-error" hidden></span>
          </label>
          <label class="checkout-field" for="entrance">
            <span>Scară <small>(opțional)</small></span>
            <input id="entrance" name="entrance" maxlength="30" aria-describedby="entrance-error">
            <span class="checkout-field__error" id="entrance-error" hidden></span>
          </label>
          <label class="checkout-field" for="floor">
            <span>Etaj <small>(opțional)</small></span>
            <input id="floor" name="floor" maxlength="20" aria-describedby="floor-error">
            <span class="checkout-field__error" id="floor-error" hidden></span>
          </label>
          <label class="checkout-field" for="apartment">
            <span>Apartament <small>(opțional)</small></span>
            <input id="apartment" name="apartment" maxlength="20" aria-describedby="apartment-error">
            <span class="checkout-field__error" id="apartment-error" hidden></span>
          </label>
          <label class="checkout-field" for="postal_code">
            <span>Cod poștal</span>
            <input id="postal_code" name="postal_code" inputmode="numeric" autocomplete="postal-code" minlength="6" maxlength="6" pattern="[0-9]{6}" required aria-describedby="postal_code-error">
            <span class="checkout-field__error" id="postal_code-error" hidden></span>
          </label>
        </div>
        <input type="hidden" name="country_code" value="RO">
        <div class="checkout-form__actions">
          <a class="button button--secondary" href="/cart">Înapoi la coș</a>
          <button class="button button--primary" type="submit">Continuă la revizuirea comenzii</button>
        </div>
      </form>
    </section>`;

  const form = host.querySelector("[data-checkout-address-form]");
  const emailOutput = host.querySelector("[data-checkout-email]");
  const formError = host.querySelector("[data-form-error]");
  const fieldLimits = {
    recipient_name: { min: 2, max: 120, required: true },
    phone: { min: 7, max: 24, required: true },
    county: { min: 2, max: 80, required: true },
    locality: { min: 1, max: 100, required: true },
    street_address: { min: 3, max: 200, required: true },
    building: { max: 30 },
    entrance: { max: 30 },
    floor: { max: 20 },
    apartment: { max: 20 },
    postal_code: { min: 6, max: 6, required: true },
  };

  function fieldValue(name) {
    return String(new FormData(form).get(name) || "").trim();
  }

  function setFieldError(name, message) {
    const input = form.elements.namedItem(name);
    const error = host.querySelector(`#${name}-error`);
    if (!input || !error) return;
    input.setAttribute("aria-invalid", String(Boolean(message)));
    error.textContent = message || "";
    error.hidden = !message;
  }

  function validate() {
    let valid = true;
    for (const [name, rules] of Object.entries(fieldLimits)) {
      const value = fieldValue(name);
      let message = "";
      if (rules.required && !value) message = "Acest câmp este obligatoriu.";
      else if (value && rules.min && value.length < rules.min) message = `Introdu cel puțin ${rules.min} caractere.`;
      else if (value.length > rules.max) message = `Introdu cel mult ${rules.max} caractere.`;
      if (!message && name === "phone" && value) {
        const digits = value.replace(/\D/g, "");
        if (!/^[0-9+() .-]+$/.test(value) || digits.length < 7 || digits.length > 15) {
          message = "Introdu un număr de telefon cu 7–15 cifre.";
        }
      }
      if (!message && name === "postal_code" && value && !/^\d{6}$/.test(value)) {
        message = "Codul poștal trebuie să conțină exact 6 cifre.";
      }
      setFieldError(name, message);
      if (message) valid = false;
    }
    return valid;
  }

  try {
    const saved = JSON.parse(sessionStorage.getItem(draftKey) || "null");
    if (saved && typeof saved === "object") {
      for (const [name, value] of Object.entries(saved)) {
        if (form.elements.namedItem(name) && typeof value === "string") form.elements.namedItem(name).value = value;
      }
    }
  } catch {
    sessionStorage.removeItem(draftKey);
  }

  fetch("/api/v1/auth/me", { headers: { Accept: "application/json" }, credentials: "same-origin" })
    .then((response) => {
      if (!response.ok) throw new Error("profile");
      return response.json();
    })
    .then((profile) => { emailOutput.textContent = profile.email || "Adresa de e-mail indisponibilă"; })
    .catch(() => { emailOutput.textContent = "Nu am putut încărca adresa de e-mail a contului."; });

  form.addEventListener("input", (event) => {
    const name = event.target.name;
    if (fieldLimits[name]) setFieldError(name, "");
    formError.hidden = true;
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!validate()) {
      form.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }
    const address = { country_code: "RO" };
    for (const name of Object.keys(fieldLimits)) {
      const value = fieldValue(name);
      address[name] = ["building", "entrance", "floor", "apartment"].includes(name) ? (value || null) : value;
    }
    try {
      sessionStorage.setItem(draftKey, JSON.stringify(address));
      window.location.assign("/checkout/review");
    } catch {
      formError.textContent = "Nu am putut salva temporar datele. Verifică setările browserului și încearcă din nou.";
      formError.hidden = false;
    }
  });
})();