---
name: kimi-design-skill
description: Use when generating, modifying, or reviewing Kimi-style Web UI, and draft Kimi-style Mobile UI. This skill applies Kimi design principles, design tokens, and platform-specific component rules with progressive disclosure.
---

# Kimi Design Skill

Use this skill when the user asks to create, modify, review, or normalize Kimi-style UI for Web or Mobile.

## Progressive Read Order

Always read Level A before making UI decisions:

1. `references/principles.md`
2. `references/tokens.json`

Then read Level B based on the platform. These are **mandatory**, not optional:

- **Web UI**: read `references/components-web.md` first, then `references/web-best-practices.md`.
- **Mobile UI**: read `references/components-mobile.md`.

Then read conditionally based on the task:

- **Animation**: read `references/animation.md` for any task that involves UI components, interactions, or state changes. This includes default, hover, pressed, focus, disabled, loading, entrance, exit, and transition states — not only obvious motion effects. Do not skip this file unless the task is purely static text or color-only adjustments with no components involved.
- **Icons**: read `references/icon-system.md` when any component in the task uses icons. Prefer existing icons from the icon system. Only create a custom icon when no existing icon matches the semantic need, and the custom icon must match the stroke weight, style, and construction rules defined in `icon-system.md`.
- **Chart colors**: read `references/components-web/chart-colors.md` when the task involves data visualization (charts, graphs, heatmaps, or any data-encoded color).

If the task involves specific Web components (Button, Modal, Dialog, Toast, etc.), read the matching file from `references/components-web/*.md`. Component rules are **mandatory** when a matching component exists — you must follow the component spec, not invent your own variant. Mobile currently has only the draft index at `references/components-mobile.md`; no `references/components-mobile/*.md` files exist yet.

If no matching component file exists, derive the new component from `tokens.json` and `principles.md`, guided by platform best practices. Do not invent arbitrary colors, radii, spacing, or styles outside the token system.

If the platform is unclear, infer it from the request. If it remains unclear, default to Web. Do not read both Web and Mobile component files unless the task explicitly targets both platforms.

## Core Requirements

- **Principles take precedence over tokens.** When a token value contradicts a principle (e.g., a color fails contrast under Quiet Utility, or a typography size breaks Platform Fit), follow the principle and record the token gap. Both `principles.md` and `tokens.json` are mandatory reads.
- Treat `references/tokens.json` as the source of truth for color, typography, radius, effects, and other design tokens.
- Use semantic token paths from `tokens.json` in component decisions and implementation notes.
- **When a component rule exists, follow it.** Do not invent arbitrary colors, radii, typography, shadows, or component variants when a matching component file or token exists.
- Follow `principles.md` before adding decoration or local visual ideas.
- Follow platform-specific component rules.
- For Web UI, follow `web-best-practices.md` for page-level layout, spacing, density, and interaction completeness.
- For Web UI component details, read the matching file in `references/components-web/*.md`. Use `components-web.md` as the index.
- Components should include relevant states, especially default, hover or pressed, disabled, loading, error, and focus where applicable.

## Source Ownership

When sources appear to conflict, resolve by ownership rather than a single linear priority:

1. **`principles.md`** owns product judgment: clarity, hierarchy, platform fit, accessibility, restraint, and when a token or component choice fails the intended experience.
2. **`tokens.json`** owns reusable visual token values: color, typography, radius, effects, and defined spacing tokens.
3. **Component rules** (`components-web/*.md`, or the draft `components-mobile.md`) own component contracts: anatomy, allowed variants, sizes, states, component metrics, composition, and accessibility.
4. **Platform best practices** (`web-best-practices.md` or `components-mobile.md`) own page-level defaults: layout, density, information hierarchy, interaction completeness, and which component or variant is appropriate in context.

Rules:

- If a component spec references a token, use the token path from the component spec and the value from `tokens.json`.
- If a component metric is defined in the component spec, do not replace it with spacing tokens or page-level rhythm.
- If a token value breaks a principle, follow the principle and record the token gap instead of silently substituting.
- If best practices and a component spec differ, use best practices to choose the component or variant, then use the component spec to implement it.

## When Token Mapping Is Incomplete

If a component references a token that is missing from `tokens.json`:

1. Use the closest existing semantic token only if the intent is clear.
2. Record the missing token or mapping in the implementation notes.
3. Do not create a permanent new token name without user or design-system confirmation.

## Current MVP Scope

This skill currently covers:

- Level A: principles and tokens.
- Level B: icon system, animation reference, Web component references, draft Mobile component reference, plus Web page-level best practices.

Do not add `patterns/`, `pages/`, `workflow.md`, `conventions.md`, or preview tooling unless the user explicitly asks to expand beyond this MVP.
