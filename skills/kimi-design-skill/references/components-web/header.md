## Header

Provisional Kimi Web Header reference:

- Source status: draft / inferred from partial design evidence; validate against the final Figma source before treating as production.
- Figma file: pending final source
- Node: `9:94757`
- Component group: `Head Navigation`

### Contract

Use Header for page-level navigation across Kimi Web surfaces. Header provides brand identity, page navigation, and a primary action slot. Do not use Header for sidebars, footers, inline toolbars, or Chat-product chrome (those use dedicated product-specific shells).

- **Purpose**: Top-level navigation, brand display, primary CTA.
- **Height**: `64px` fixed. Do not change for different content combinations.
- **Composition**: Shell frame with three slots — `logo`, `nav`, `cta`.
- **Background**: `backdrop-blur` with a translucent surface; see variant specs below.
- **Width**: stretches to container width; uses horizontal padding that scales with viewport.

Do not add page-level decoration, gradients, heavy shadows, or marketing-style hero composition to Header. It is a quiet, functional surface.

### Size And Dimensions

| Property | Value |
|----------|------:|
| Total height | `64px` (fixed) |
| Content height | `32px` |
| Vertical padding | `16px` (top and bottom) |
| Width | `100%` of parent container |
| Horizontal padding | `120px` at `1440px` viewport; `16px` minimum on narrow viewports |
| Layout | horizontal, `SPACE_BETWEEN`, center-aligned |
| Inter-slot gap | `24px` between `nav` items |

Rules:

- Height is always `64px`. Content inside must fit within the `32px` content band.
- The shell frame has no border radius (`0`).
- Horizontal padding decreases on smaller viewports; never use `120px` below `768px`.

### Structure

```
Header Frame (backdrop-blur, no radius)
  └── Content (HORIZONTAL, SPACE_BETWEEN, height: 32px, vertically centered)
      ├── Logo Slot
      │   ├── Variant: logoOnly — image/SVG only
      │   └── Variant: logoWithTitle — pill badge + title text
      ├── Nav Slot
      │   └── Navigation links (HORIZONTAL, gap: 24px)
      └── CTA Slot
          └── Primary action button (Button component instance)
```

**Logo Slot:**

- Layout: horizontal, `MIN`, center-aligned.
- Internal gap: `8px` when both badge and title are present.

Two mutually exclusive variants:

| Variant | Structure | Typical size |
|---------|-----------|-------------|
| `logoOnly` | Logo image or SVG only. | ~`74×24` for text logos; scale proportionally for image logos. |
| `logoWithTitle` | Pill badge (`radius.full`, ~`20px` corner radius) + title text. | Badge: `66×26` typical; title: `typography.ui.t2Emphasized`. |

Pill badge rules:

- Background: `color.labels.primary`.
- Text/icon inside badge: `color.background.primary` or `color.always.white`.
- Use `radius.full` for the pill shape.
- The badge contains the logo mark only (not the title text).

Title text (when `logoWithTitle`):

- Text: `typography.ui.t2Emphasized`.
- Color: `color.labels.primary`.
- Placed immediately to the right of the badge with `8px` gap.

**Nav Slot:**

- Layout: horizontal, `MIN`, center-aligned.
- Internal gap: `24px` between items.
- Each item is a text link:
  - Text: `typography.ui.t2`.
  - Default color: `color.labels.secondary`.
  - Active/current color: `color.labels.primary`.
  - Hover: subtle background fill (`color.fills.f1`) without border; do not add a stroke.
  - Padding: `px: 8px`, `py: 4px` for the clickable area.
  - Radius: `radius.sm` (`8px`) for the hover background.
- Do not use Button component instances for nav links; Button does not define a ghost/link variant. Define nav links directly in Header.

**CTA Slot:**

- Single primary action.
- Must compose a **Button** instance from `button.md`:
  - Variant: `primary`.
  - Size: `32` (default web action size).
  - Follow Button rules for variant, size, state, and loading.
- Do not define new button styles inside Header.

### Token Relationship

Use `tokens.json` for color, typography, radius, and effects.

Header dimensions (height, padding) are component-level values from the Figma source.

| Element | Token path | Notes |
|---------|-----------|-------|
| Header background (dark) | transparent / `rgba(0,0,0,0.01)` | With `backdrop-blur` applied via CSS |
| Header background (light) | `color.background.primary70` | With `backdrop-blur` applied via CSS |
| Nav link text | `typography.ui.t2` | — |
| Nav link color (default) | `color.labels.secondary` | — |
| Nav link color (active) | `color.labels.primary` | — |
| Nav link hover fill | `color.fills.f1` | No border on hover |
| Logo title text | `typography.ui.t2Emphasized` | — |
| Logo title color | `color.labels.primary` | — |
| Logo badge background | `color.labels.primary` | — |
| Logo badge text/icon | `color.background.primary` | — |
| CTA button | Follow `button.md` | Variant `primary`, size `32` |

### Variant Tokens

Header appearance changes based on **theme** and **blur intensity**:

| Theme | Background | `backdrop-blur` | Logo | Nav | CTA |
|-------|-----------|----------------|------|-----|-----|
| `dark` | Transparent | `6px` (default) or `50px` (product pages) | Light/inverse | `color.labels.secondary` → `color.labels.primary` active | `primary` (inverse colors) |
| `light` | `color.background.primary70` | `6px` | Dark | `color.labels.secondary` → `color.labels.primary` active | `primary` (default colors) |

Rules:

- `dark` theme is used for hero sections, product pages, and any surface with a non-white background behind the Header.
- `light` theme is used for standard content pages with a white/light background.
- `backdrop-blur: 50px` is reserved for product pages (e.g., 开放平台) where the background is visually complex; default is `6px`.
- The `cta` slot always uses Button `primary` variant; the Button itself handles color inversion via `tokens.json` dark/light modes.

### Behavior

- Header is sticky at the top of the page container by default.
- Nav links scroll smoothly to anchor targets or navigate to routes.
- The active nav item matches the current route or scroll position.
- CTA button triggers its action without page navigation (e.g., open login modal, open try-flow).
- Do not animate Header entrance/exit; it is a persistent chrome element.

### Accessibility

- Header container: `role="banner"`.
- Nav container: `role="navigation"`, `aria-label="主导航"` or equivalent.
- Active nav item: `aria-current="page"`.
- All nav links must have visible focus states following `color.status.kimiBlue` focus ring.
- Logo link (if clickable) must have an accessible name.
- Follow `icon-system.md` accessibility rules if the logo contains an icon.

### Code Guidance

```ts
type LogoVariant = "logoOnly" | "logoWithTitle";
type HeaderTheme = "dark" | "light";
type HeaderBlur = 6 | 50;

interface HeaderProps {
  logoVariant: LogoVariant;
  logoSrc?: string;           // image/SVG path for logo mark
  logoTitle?: string;         // title text when logoVariant = "logoWithTitle"
  navItems: {
    label: string;
    href: string;
    active?: boolean;
  }[];
  cta: {
    label: string;
    onClick: () => void;
  };
  theme?: HeaderTheme;
  blur?: HeaderBlur;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Use `position: sticky; top: 0;` for the Header container.
- Apply `backdrop-filter: blur(Npx)` to the Header frame, not to inner content.
- The `64px` height must be preserved even when content wraps or shrinks on narrow viewports.
- Compose the CTA from **Button** instances via the `cta` prop; do not embed button styles inside Header.
- Nav links should use semantic `<a>` elements for route navigation and `<button>` only for in-page actions.
