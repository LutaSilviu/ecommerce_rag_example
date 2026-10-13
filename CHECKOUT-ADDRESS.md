# Checkout contact and Romanian address contract (T046)

This is the shared field contract for checkout entry, order creation, and saved
order snapshots. The API/domain model is `DeliveryAddress` in
[`app/domain/models.py`](./app/domain/models.py).

## Contact source

- `recipient_name` is required (2–120 characters) and identifies the person
  receiving the parcel.
- `phone` is required (7–24 characters, with 7–15 digits); digits and common
  phone separators (`+`, spaces, parentheses, hyphen, period) are accepted.
- The authenticated account email is the contact email. Checkout may display it
  as read-only, but it is not repeated in the request body or order snapshot.

## Delivery address fields

| Field | Required | Contract |
|---|---|---|
| `county` | Yes | Free text, 2–80 characters; enter județul or București. |
| `locality` | Yes | Free text, 1–100 characters; city, town, or commune. |
| `street_address` | Yes | 3–200 characters; street name and number in one field. |
| `building` | No | Up to 30 characters. |
| `entrance` | No | Up to 30 characters. |
| `floor` | No | Up to 20 characters. |
| `apartment` | No | Up to 20 characters. |
| `postal_code` | Yes | Exactly six digits. |
| `country_code` | Yes, fixed | `RO`; clients do not select or override it. |

County uses free text rather than a bundled list of 41 counties plus Bucharest.
That avoids maintaining a second taxonomy and still accepts all Romanian
localities. Delivery notes are excluded from this MVP: they are not required by
the specification and the persisted order schema has no notes field. Do not
silently add them only to the browser form.

`DomainModel` trims surrounding whitespace and forbids unknown keys. Required
fields must not be made optional in the UI or API. Validation errors should be
shown beside the relevant Romanian-labeled field; keep entered values after an
error. The API is authoritative even when browser-side validation is present.

## Downstream effects

- **T047:** Build fields from this table; use account email as read-only
  contact context, free-text județ/locality, optional address subdivisions,
  and the six-digit postal code. Do not add delivery notes.
- **T048:** Payment selection does not alter contact/address data.
- **T049:** Review the exact submitted fields; summarize optional subdivisions
  only when present and keep account email visibly associated with the contact.
- **T050:** Auth redirects must retain entered form state if checkout navigation
  requires sign-in; never place credentials in that state.
- **T051–T052:** Send the validated `delivery_address` object and persist it only
  after successful order creation. API rejection must leave form data and cart
  available for correction/retry.
- **T053–T055:** Confirmation, history/detail must read the immutable address
  snapshot; address edits in the account must not rewrite existing orders.
- **T056:** Romanian labels/errors should use județ, localitate, adresă, cod
  poștal, and telefon while preserving these machine field names.
