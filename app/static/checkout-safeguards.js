"use strict";

(() => {
  if (document.body.dataset.page !== "checkout-review") return;
  const draftKey = "nexo.checkout.address.v1";

  function feedback(button, message, href = null, linkLabel = null) {
    let node = document.querySelector("[data-checkout-submit-feedback]");
    if (!node) {
      node = document.createElement("p");
      node.dataset.checkoutSubmitFeedback = "";
      node.setAttribute("role", "alert");
      node.setAttribute("aria-live", "assertive");
      button?.parentElement?.prepend(node);
    }
    node.replaceChildren(document.createTextNode(message));
    if (href && linkLabel) {
      node.append(document.createTextNode(" "));
      const link = document.createElement("a");
      link.href = href;
      link.textContent = linkLabel;
      node.append(link);
    }
  }

  async function revalidate(button) {
    let address;
    try { address = JSON.parse(sessionStorage.getItem(draftKey) || "null"); }
    catch { address = null; }
    if (!address || typeof address !== "object" || !address.recipient_name || !address.postal_code) {
      return { ok: false, message: "Datele de livrare lipsesc. Recompletează formularul.", href: "/checkout/details", linkLabel: "Editează datele" };
    }

    const response = await fetch("/api/v1/catalog/products", {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Catalogul nu este disponibil pentru reverificare.");
    const products = await response.json();
    if (!Array.isArray(products)) throw new Error("Catalogul a returnat date invalide.");
    window.NexoCart.setProducts(products);
    const state = window.NexoCart.getState();
    if (!state.lines.length) {
      return { ok: false, message: "Coșul este gol. Adaugă produse înainte de confirmare.", href: "/search", linkLabel: "Descoperă produsele" };
    }
    if (state.lines.some((line) => line.checkout_blocked || !line.product)) {
      return { ok: false, message: "Disponibilitatea sau cantitatea unui produs s-a schimbat. Corectează coșul înainte de confirmare.", href: "/cart", linkLabel: "Editează coșul" };
    }

    const totalBani = state.lines.reduce((sum, line) => sum + line.product.price_bani * line.quantity, 0);
    if (!Number.isSafeInteger(totalBani)) throw new Error("Totalul comenzii nu poate fi calculat în siguranță.");
    const fingerprint = state.lines
      .map((line) => `${line.product_id}:${line.quantity}:${line.product.price_bani}`)
      .sort()
      .join("|");
    if (button.dataset.reviewFingerprint && fingerprint !== button.dataset.reviewFingerprint) {
      return { ok: false, stale: true, message: "Coșul sau prețurile s-au schimbat de la revizuire. Reîncarcă pagina ca să verifici din nou comanda.", href: window.location.pathname, linkLabel: "Reîncarcă revizuirea" };
    }
    return {
      ok: true,
      address,
      items: state.lines.map(({ product_id, quantity }) => ({ product_id, quantity })),
      total_bani: totalBani,
    };
  }

  async function submit(button, operation) {
    if (!button || button.dataset.submitting === "true") return { ok: false, duplicate: true };
    button.dataset.submitting = "true";
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    feedback(button, "Verificăm coșul, stocul și totalul actual…");
    try {
      const checked = await revalidate(button);
      if (!checked.ok) {
        feedback(button, checked.message, checked.href, checked.linkLabel);
        return checked;
      }
      if (typeof operation !== "function") {
        feedback(button, "Coșul este valid și totalul a fost reverificat.");
        return checked;
      }
      const result = await operation(checked);
      if (!result?.navigating) {
        feedback(button, result?.message || "Nu am putut salva comanda. Datele tale au fost păstrate.");
      }
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Nu am putut reverifica datele comenzii.";
      feedback(button, `${message} Datele și coșul au fost păstrate.`);
      return { ok: false, message };
    } finally {
      button.dataset.submitting = "false";
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  }

  window.NexoCheckoutGuards = Object.freeze({ revalidate, submit });
})();