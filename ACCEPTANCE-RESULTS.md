# Nexo Market acceptance results

**Run date:** 2026-10-13  
**Environment:** Local FastAPI server and isolated API/TestClient walkthrough.  
**Overall:** Pass for the locally testable MVP scope. Google OAuth and deployment to a hosting provider remain external setup items, not implementation failures.

## Results

| Scenario | Result | Evidence |
|---|---|---|
| Storefront and key customer page routes | Pass | `/`, `/checkout/details`, `/checkout/review`, `/checkout/confirmation/{example}`, `/account/orders`, and `/account/orders/{example}` returned HTTP 200. |
| Catalog access | Pass | `GET /api/v1/catalog/products` returned HTTP 200. |
| Order access without a session | Pass | Anonymous `GET /api/v1/orders` and `GET /api/v1/orders/{order_number}` returned HTTP 401. |
| Account-to-order API journey | Pass | Isolated walkthrough registered an account, created an order, replayed the same idempotency key and received the same order, read the owner-scoped history and detail, logged out, then confirmed order reads returned HTTP 401. |
| Narrow viewport overflow | Pass | At a 360px viewport, the document measured 345px wide; no horizontal overflow was reported. |
| Localization, responsive fixes, accessibility, privacy/security, setup documentation | Pass for completed task checks | T056–T060 are recorded complete in `TASKS.md`; see their task notes for the reviewed changes. |
| Provider-neutral deployment configuration | Pass | Docker Compose configuration was checked with a placeholder-only test secret; the image was not built or deployed. |

The first order-creation walkthrough exposed SQLite foreign-key ordering between the order snapshot and its idempotency record. The implementation was corrected to flush the order snapshot first, and the walkthrough was rerun successfully, including the idempotent replay.

## External items not exercised

- **Google sign-in:** Not exercised against Google because no OAuth client ID/secret are configured. Local and production callback/origin setup is documented; supply valid values to run this scenario.
- **Hosted deployment:** Not tested because no hosting provider has been selected. T061 provides provider-neutral container configuration and deployment notes.
- **Full browser-only checkout interaction:** The order lifecycle and idempotency were exercised through an isolated TestClient/API walkthrough. The recorded 360px check covered overflow; this acceptance run did not automate every click and keyboard interaction across every page.

These are scope/configuration limitations, not failures in the tested local order flow. No real payment is processed.

`python -m compileall -q app` passed. No committed Python `test_*.py` suite was present; the order lifecycle verification above was the isolated TestClient walkthrough.

## Handoff

T062 is complete for the implemented and locally testable MVP acceptance scope. Google OAuth configuration and provider-specific deployment remain follow-up work when those external choices and credentials are available.
