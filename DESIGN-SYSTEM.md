# Nexo Market Design System

**Status:** T008 design and component conventions  
**Scope:** Romanian single-store ecommerce prototype; plain HTML, CSS, and JavaScript served by FastAPI (see `TECH-STACK.md`).  
**Principle:** Familiar, calm retail UI that keeps product imagery and prices prominent. Prefer reusable CSS classes and native controls over decorative complexity.

## 1. Visual direction

- Use a light, neutral canvas with deep ink text, a saturated blue brand action, and restrained green for success/availability.
- Use white surfaces for product cards, forms, and order summaries; separate them with a subtle border before adding shadows.
- Keep the brand visible as text (“Nexo Market”); do not require a logo asset to render the header.
- Product imagery is the strongest visual element. Use consistent image frames with `object-fit: contain` for products on a pale neutral background.
- Avoid gradients, excessive rounded pills, motion-heavy effects, and category-specific color systems.
- All customer-facing labels, feedback, and examples are Romanian. Use RON prices formatted centrally with `Intl.NumberFormat("ro-RO", { style: "currency", currency: "RON" })`.

## 2. Color tokens

Define these once in the global stylesheet under `:root`. Do not hard-code alternate colors in individual pages.

| Token | Value | Use |
|---|---|---|
| `--color-canvas` | `#F5F7FA` | Page background |
| `--color-surface` | `#FFFFFF` | Cards, forms, menus, header |
| `--color-surface-muted` | `#EEF2F6` | Image wells, subdued panels |
| `--color-border` | `#D7DEE8` | Card edges, separators, input borders |
| `--color-text` | `#17212F` | Main text and headings |
| `--color-text-muted` | `#536174` | Supporting text; keep readable |
| `--color-brand` | `#155EEF` | Primary links, primary button, selected navigation |
| `--color-brand-hover` | `#124BC2` | Hover/active primary controls |
| `--color-brand-soft` | `#EAF1FF` | Selected filters, informational emphasis |
| `--color-success` | `#176B45` | Available stock and success feedback |
| `--color-success-soft` | `#E8F5EE` | Success state background |
| `--color-warning` | `#875600` | Low stock or non-blocking warning |
| `--color-warning-soft` | `#FFF4D6` | Warning state background |
| `--color-danger` | `#B42318` | Validation errors and destructive actions |
| `--color-danger-soft` | `#FEF0EE` | Error state background |
| `--color-focus` | `#F59E0B` | High-visibility keyboard focus outline |

Use text and an icon/label in addition to color for stock and status communication. Success/error foregrounds must remain on their corresponding soft backgrounds or white surfaces.

## 3. Typography

Use a system font stack; the app must not depend on a remote font request:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", sans-serif;
```

| Role | Size / line height | Weight | Notes |
|---|---:|---:|---|
| Page title (`h1`) | `2rem / 1.2` (32/38px) | 700 | Reduce to 28px on narrow screens |
| Section title (`h2`) | `1.5rem / 1.25` (24/30px) | 650–700 | Clear separation between page sections |
| Card/product title (`h3`) | `1rem / 1.4` (16/22px) | 600 | Clamp only in dense listing cards; full title on detail page |
| Body | `1rem / 1.5` (16/24px) | 400 | Default text and form content |
| Supporting text | `.875rem / 1.45` (14/20px) | 400 | Muted color, never below 14px for essential content |
| Price | `1.25rem / 1.3` (20/26px) | 700 | Use tabular numerals where available |
| Small metadata | `.75rem / 1.4` (12/17px) | 500 | Non-essential labels only |

Use sentence case and natural Romanian diacritics. Avoid all-caps labels except short decorative badges. Keep paragraphs to a comfortable measure (about 65–75 characters).

## 4. Spacing, shape, and elevation

Use a 4px base scale. Prefer these tokens and avoid one-off spacing values:

| Token | Value | Typical use |
|---|---:|---|
| `--space-1` | `4px` | Icon/text gap, compact badge padding |
| `--space-2` | `8px` | Tight control gaps |
| `--space-3` | `12px` | Card internals, compact field gaps |
| `--space-4` | `16px` | Standard component padding |
| `--space-6` | `24px` | Section and card spacing |
| `--space-8` | `32px` | Page section separation |
| `--space-12` | `48px` | Large section separation |

- Content container: `max-width: 1200px`, centered, with 24px horizontal gutters on desktop and 16px on narrow screens.
- Standard card radius: 12px; compact controls: 8px; pill shape only for short status badges.
- Inputs and buttons are at least 44px tall (48px preferred for primary touch actions).
- Borders are 1px solid `--color-border`. Use a soft shadow only for overlays or hover lift: `0 4px 16px rgb(23 33 47 / 8%)`.
- Do not use shadow as the only boundary between adjacent cards.

## 5. Component conventions

### Buttons and links

- `.button` is the shared base: inline-flex, centered contents, 44px minimum height, 8px radius, 16px horizontal padding, 600 weight, and visible focus treatment.
- `.button--primary`: brand blue fill with white text; hover uses `--color-brand-hover`.
- `.button--secondary`: white fill, ink text, 1px border; hover uses `--color-brand-soft`.
- `.button--danger`: danger text/border on white for secondary destructive actions; use danger fill only when the destructive action is the main decision.
- Disabled/pending buttons must be visibly distinct, non-interactive, and retain readable text. Show a short Romanian pending label or status next to the control; do not rely on animation alone.
- Inline links are underlined in body copy. Navigation links may omit underline but need a clear hover and focus state.

### Inputs and forms

- Every field has a persistent visible `<label>`; placeholder text is an example, never the only label.
- Standard input/select/textarea: white surface, ink text, 1px border, 8px radius, 12px horizontal padding, at least 44px high.
- Use `:focus-visible` with a 3px outline using `--color-focus` and a 2px offset. Do not remove the browser outline without replacing it.
- Invalid fields use the danger border and an adjacent error message; associate the message with `aria-describedby` and set `aria-invalid="true"` when invalid.
- Group related fields with `fieldset` and `legend`. Keep Romanian checkout field names explicit (județ, localitate, stradă, cod poștal).

### Product cards

- White surface, subtle border, 12px radius, consistent internal padding and equal-height grid rows.
- Image area uses a 4:3 frame with muted background and contained image; preserve source aspect ratio without stretching.
- Content order: image, availability/status, product name, price, add-to-cart action.
- Make the product name a link to its detail route. The add-to-cart button is a separate control with a clear name (e.g. “Adaugă în coș”).
- Keep price and availability readable without opening the detail page. Announce add-to-cart success in a polite live region.

### Alerts, badges, and status

- Alerts have a semantic role appropriate to the event (`role="status"` for routine success, `role="alert"` for blocking error), a short Romanian heading/message, and optional action.
- Use soft state background plus matching readable foreground; include text/icon to communicate meaning without color.
- Stock badges use concise labels such as “În stoc” or “Stoc epuizat”. Prototype orders/payment must say “Comandă demonstrativă” / “Plată simulată” wherever status could be mistaken for a real transaction.

### Layout primitives

- `.container`: centered max-width content region.
- `.stack`: vertical flow using a consistent gap.
- `.cluster`: wrapped horizontal controls with a consistent gap.
- `.product-grid`: responsive equal-width columns and consistent gaps.
- Checkout/order summaries remain visually grouped and should not split labels from values at narrow widths.

## 6. Responsive behavior

Use mobile-first CSS and these shared breakpoints:

| Breakpoint | Width | Layout guidance |
|---|---:|---|
| Small | `< 600px` | One-column page content; product grid 2 columns when cards remain usable, otherwise 1; compact header with menu control; checkout summary follows form |
| Medium | `600px–899px` | 2–3 product columns; allow search and account/cart controls to wrap cleanly; form may use 2 columns only for short related fields |
| Large | `900px–1199px` | 3–4 product columns; desktop category navigation; checkout can use main form plus summary column |
| Wide | `≥ 1200px` | Center content at 1200px; 4 product columns; do not stretch text lines or cards indefinitely |

- At 320px viewport width, prevent horizontal page scrolling and preserve access to all controls.
- At narrow widths, keep touch controls at least 44×44px, allow long Romanian words/addresses to wrap, and keep cart count visible.
- Do not hide essential price, availability, form errors, order status, or checkout actions at any breakpoint.
- Respect `prefers-reduced-motion: reduce`; transitions are optional and limited to color/shadow/transform feedback.

## 7. Accessibility and interaction requirements

- Use semantic landmarks, one clear `<h1>` per page, ordered headings, native buttons/links/forms, and descriptive image alternative text (empty alt for decorative imagery).
- All interactive elements work with keyboard alone. Tab order follows visual order; menus and dialogs expose their expanded/open state and return focus appropriately.
- Focus indicators remain visible against both light surfaces and brand-colored controls.
- Maintain WCAG AA contrast targets: at least 4.5:1 for normal text, 3:1 for large text and meaningful control boundaries/icons. Verify actual foreground/background pairs when implementing; do not assume a token pairing passes solely by appearance.
- Use at least 16px form/input text to avoid cramped mobile forms. Essential supporting text should be 14px or larger.
- Give icon-only controls an accessible name. Do not use emoji as the sole accessible label.
- Announce asynchronous search/cart/auth/checkout results without moving focus unexpectedly. Preserve entered values when a recoverable error occurs.
- Ensure validation identifies the field and explains how to fix it in Romanian; do not communicate errors by color alone.

## 8. Plain CSS implementation notes

- Put global tokens, reset/base styles, typography, and reusable component classes in a shared stylesheet imported by every page.
- Keep selectors class-based and low-specificity; avoid page-specific overrides of shared controls.
- Prefer CSS Grid for product listings and form/layout columns, Flexbox for header/control clusters, and native responsive wrapping.
- No CSS framework or build step is required. Keep the design responsive with ordinary media queries and CSS custom properties.
- When adding a component, reuse the tokens and conventions above; add a new token only when an existing one cannot express the need consistently.
