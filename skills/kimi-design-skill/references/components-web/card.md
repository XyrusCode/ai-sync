## Card

Provisional Kimi Web Card reference:

- Source status: draft / inferred from partial design evidence; validate against the final Figma source before treating as production.
- Figma file: pending final source
- Node: `6:83519`
- Component group: `Card`

### Contract

Use Card as a container for grouped content that needs visual separation from its surroundings. Card provides a framed surface with a media area and a content area; both slots accept caller-provided content.

- **Purpose**: Feature highlights, product cards, content previews, navigation shortcuts.
- **Composition**: Two slots — `media` (top) and `content` (bottom).
- **Width**: flexible. Minimum `320px`, maximum `560px`. The caller or layout context decides the exact width.
- **Height**: content-driven. The Card grows to fit its media + content.
- **Background**: `color.background.primary` with a light border.
- **Do not** use Card for passive lists, dense data tables, or inline form rows where a plain container suffices.

### Size And Dimensions

| Property | Value |
|----------|------:|
| Width | `320px` minimum, `560px` maximum. Exact width is layout-dependent. |
| Height | Content-driven; typical range `320px`–`560px`. No fixed height. |
| Card radius | `radius.lg` (`12px`) or `radius.sm` (`8px`), see variant rules below. |
| Card border | `0.5px` `color.separator.s1` |
| Internal padding | `8px` (gap between card edge and media/content) |
| Media-to-content gap | `16px` |
| Content inner padding | `16px` left/right, `16px` bottom |

Rules:

- Card never exceeds `560px` wide; on narrow viewports it may shrink to `320px` or stack vertically.
- The `media` slot may fill the full internal width (width − `16px`) or be smaller if the caller provides a fixed-size element.
- The `content` slot height is fully content-driven. Typical total Card height falls in `320px`–`560px` depending on media size and content volume.

### Structure

```
Card Frame (bg primary, stroke s1, radius)
  ├── Media Slot (caller-provided)
  │   └── [image, icon, illustration, video, or any custom content]
  └── Content Slot (caller-provided)
      └── [title, description, tags, buttons, or any custom content]
```

**Media Slot:**

- Positioned at the top of the Card, inside the `8px` card padding.
- Media area width = Card width − `16px` (left `8px` + right `8px`).
- Media area height is caller-defined; typical ranges are `160px`–`220px`.
- If the media is an image or video, apply a radius smaller than the Card radius:
  - Card `radius.lg` (`12px`) → Media `radius.md` (`10px`) or `radius.sm` (`8px`).
  - Card `radius.sm` (`8px`) → Media `radius.xxs` (`4px`).
- Media may be full-bleed (fills the slot) or contain a centered icon/illustration with a background fill.

**Content Slot:**

- Below the media slot, separated by `16px`.
- Inner padding: `16px` left/right, `16px` bottom. No top padding (the `16px` media-to-content gap already provides separation).
- Layout: vertical, caller-provided. Common patterns:
  - Title + description
  - Title + description + action button
  - Badge + title + description
- All text inside the content slot uses tokens; do not hard-code local font sizes.

### Token Relationship

Use `tokens.json` for color, typography, radius, and spacing.

Card dimensions (padding, gap) are component-level values. Do not convert them into new spacing tokens.

| Element | Token path | Notes |
|---------|-----------|-------|
| Card background | `color.background.primary` | — |
| Card border | `color.separator.s1` | `0.5px` |
| Title text | `typography.webUI.largeTitleEmphasized` | `20/600/30` |
| Title color | `color.labels.primary` | — |
| Description text | `typography.ui.t1` | `18/400/26` |
| Description color | `color.labels.secondary` | — |
| Content heading (alt) | `typography.webUI.t2Emphasized` | `16/500/24` — use when `largeTitleEmphasized` feels too large |
| Radius (card) | `radius.lg` or `radius.sm` | See variant rules |
| Radius (media) | One step smaller than card radius | See variant rules |

### Variant Tokens

Card radius and media radius follow a **step-down** rule: media is always one radius step smaller than the card itself.

| Variant | Card radius | Media radius | Typical use |
|---------|------------:|-------------:|-------------|
| `default` | `radius.lg` (`12px`) | `radius.sm` (`8px`) | Standard cards, content previews |
| `compact` | `radius.sm` (`8px`) | `radius.xxs` (`4px`) | Dense grids, tool cards, inline cards |

Rules:

- Prefer `default` for most surfaces.
- Use `compact` only when cards are packed tightly in a grid and large rounding would feel excessive.
- Do not mix `default` and `compact` cards in the same local area without a clear reason.

### Common Content Patterns

Card is intentionally flexible. Below are common patterns observed in the design system; none are mandatory.

**Pattern A: Image + Title + Description**
- Media: full-bleed image.
- Content: `typography.webUI.largeTitleEmphasized` title + `typography.ui.t1` description.
- Use for feature cards, product highlights, blog previews.

**Pattern B: Background Image + Center Icon + Title + Description**
- Media: background image with a centered `48×48` icon on top.
- Content: same as Pattern A.
- Use for capability cards, tool showcases.

**Pattern C: Image + Badge Title + Description**
- Media: full-bleed image.
- Content: pill/badge label (`typography.webUI.b2Emphasized`, `radius.full`) + title + description + **Button** instance (follow `button.md`).
- Use for hero cards, agent/product type cards.

**Pattern D: Custom**
- Media or content may contain any composition: video, form, chart, button group.
- Card only provides the frame; the caller owns the interior.

### Behavior

- Card does not animate on its own. Entrance/exit animations belong to the layout or list that contains the Card.
- Hover state: subtle background shift to `color.fills.f1` if the entire Card is clickable; otherwise, hover states belong to interactive elements inside the Card (buttons, links).
- Clicking the Card surface (if clickable) navigates to a detail view or triggers a primary action.
- Do not nest Cards inside Cards.

### Accessibility

- If the entire Card is clickable, wrap it in an `<a>` or `<button>` with an accessible label.
- If only specific elements inside are interactive, keep the Card as a generic container and add `aria-label` to each interactive child.
- Images in the media slot must have `alt` text unless they are purely decorative.
- Text inside the content slot must meet contrast requirements under both light and dark themes.

### Code Guidance

```ts
type CardRadius = "default" | "compact";

interface CardProps {
  radius?: CardRadius;
  media?: React.ReactNode;
  content?: React.ReactNode;
  href?: string;            // makes the entire card clickable
  onClick?: () => void;     // alternative to href for actions
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Card width should use CSS custom properties or container queries so the layout context controls it.
- Do not hard-code `320px` or `560px` in the Card component itself; expose a `className` or `style` prop for layout control.
- Media slot should use `overflow: hidden` with the correct radius.
- The Card frame itself should have `overflow: hidden` to clip media corners cleanly.
