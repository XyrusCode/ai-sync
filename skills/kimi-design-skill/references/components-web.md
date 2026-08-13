# Kimi Web Components

This file is the index for Kimi Web component specifications. Read it after `principles.md` and `tokens.json` when the target platform is Web.

For page-level layout, spacing, density, and interaction rules, read `web-best-practices.md`.

For animation and motion rules, read `animation.md`.

For icon-bearing components, read `icon-system.md` as directed by `SKILL.md`.

## Global Web Component Rules

- Treat `tokens.json` as the source of truth.
- Use semantic token paths from `tokens.json` in implementation code and component notes.
- Keep Figma variable names only as source traceability when needed; do not use raw Figma names or observed hex values as product-facing token contracts.
- Web components may use hover and focus-visible states.
- Do not use mobile-only behavior such as pressed-only feedback for web controls.
- Do not invent new colors, radii, typography, or shadows when the design system already defines an equivalent token.
- Keep components compact and work-focused. Avoid decorative gradients, glassmorphism, oversized rounded cards, and ornamental effects.
- **Do not redefine styles of atomic components inside parent components.** A parent component (Modal, Dialog, Card) defines its own layout and structure only. For child components (Button, Icon, Input) used inside it, reference the child component's rules. Do not duplicate token mappings, color values, or state definitions that belong to the child component's spec. Parent docs describe *where* and *how* the child is composed; child docs describe *what* it looks like.
- **Cross-component elements** (like a Close button that appears in both Modal and Dialog) should either reference `icon-system.md` or have their own component spec if they carry enough complexity. Do not redefine them differently in each parent.

## Component Index

Read individual component files for full specifications:

- **[Button](components-web/button.md)** — Explicit actions: submit, confirm, cancel, navigate. Variants: primary, secondary, outline. Sizes: 44, 32, 26.
- **[Modal](components-web/modal.md)** — Focused, interruptive tasks with forms or complex content. Sizes: small, medium, large.
- **[Menu](components-web/menu.md)** — Contextual action lists. Min/max width constraints, item states.
- **[Dialog](components-web/dialog.md)** — Pure-text binary confirmations. Fixed 360px width. No close button.
- **[Selection Control](components-web/selection-control.md)** — Unified circular Checkbox/Radio visual component. Same circle + thick checkmark; behavior mode controls multi-select vs single-select. Sizes: 16, 20, 24.
- **[Toggle](components-web/toggle.md)** — Binary on/off switch. Sizes: lg (44×24), sm (32×18). Thumb slides with hover shrink.
- **[Segmented Control](components-web/segmented-control.md)** — Single-select button group. 2–3 segments, sizes: sm, md. Selected segment pops out with distinct background.
- **[Form](components-web/form.md)** — Data entry and submission inside Modal or pages. Field, section, radio, and checkbox composition.
- **[Toast](components-web/toast.md)** — Non-blocking transient feedback. Types: success, error, info, loading, caution.
- **[Tooltip](components-web/tooltip.md)** — Contextual hints and labels on hover/focus. Variants: default, coach-mark. Directions: top, bottom, left, right.
- **[Header](components-web/header.md)** — Top navigation bar with three-slot layout: logo, nav, cta.
- **[Card](components-web/card.md)** — Container for grouped content with media and content slots. Width and height range: 320px–560px.

## Non-Component References

- **[Chart Colors](components-web/chart-colors.md)** — Color scales for data visualization: categorical, sequential, diverging. Derived from existing tokens.

## Planned Components

The following components are not yet documented:

- Input / Textarea
- Select
- Tabs
- Empty State

Follow the existing component file structure when adding new ones.
