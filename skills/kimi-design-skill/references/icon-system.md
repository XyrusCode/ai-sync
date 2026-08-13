# Kimi Icon System

This file defines Kimi icon rules for AI-generated UI. Read it after `principles.md` and `tokens.json` when the task involves icons, buttons with icons, tabs, toolbars, or any icon-bearing component.

## Sources

- Figma file: `Kimi Design System`
- Node: `3508-9290`
- Style: Outlined linear icons, 1.8px stroke

## Icon Style

- **Type**: Outlined linear icons (1.8px stroke)
- **Base grid**: `24×24` viewBox
- **Color mode**: `currentColor` for all monochrome icons
- **No hard-coded fills**: All SVGs in `assets/icons/` use `fill="currentColor"`; theming is controlled via CSS or token color

## Size System

Icon size is determined by the component it lives in, not by arbitrary choice.

| Context | Host Component Height | Icon Size |
|---------|----------------------:|----------:|
| Large primary actions | `44px` (Button size 44) | `20px` |
| Default buttons, tabs, chips | `32px` (Button size 32) | `18px` |
| Compact buttons, inline chips | `26px` (Button size 26) | `16px` |
| Toolbar chips, tool buttons | `28–36px` | `18–20px` |
| Standalone icon buttons | — | `20–24px` |
| Inline with text | — | `16px` (same as text line-height alignment) |

Rules:

- Do not scale icons arbitrarily outside this table.
- Do not use `12px` icons for normal UI; `12px` is reserved for badge dots and micro indicators.
- Icon container should be a square frame (`width == height`) to preserve optical alignment.

## Color Rules

- **Default monochrome**: `currentColor`
- **Semantic overrides**:
  - Destructive actions: `color.status.danger`
  - Success/positive: `color.status.positiveGreen`
  - Disabled: `color.labels.quaternary`
- **Brand or multicolor icons**: Marked explicitly in `icons/manifest.json` with `color_mode: "multicolor"`. These are rare; most Kimi icons are monochrome.
- **Do not** hard-code `black`, `#000`, or arbitrary hex values in icon usage.

## Variant Suffixes

Some Kimi icons have suffixed variants. The suffix indicates an alternate style or orientation.

| Suffix | Meaning | Example |
|--------|---------|---------|
| `_b` | Alternative style (often filled or thicker stroke) | `Share_b`, `Dislike_b`, `Like_b` |
| `_c` | Directional variant C | `Left_c`, `Right_c`, `Up_c` |
| `_r` | Rotated or reversed orientation | `Enter_r` |

Rules:

- Prefer the non-suffixed version unless the component spec or product context explicitly requires the variant.
- Do not invent new suffixes.

## Icon Library Structure

The skill ships with 267 icons stored as SVG in `assets/icons/`.

Semantic indexes:

- `references/icons/manifest.json` — full machine-readable index (267 icons)
- `references/icons/categories/*.json` — split by domain:
  - `general`, `arrows`, `chat`, `input`, `navigation`, `editor`, `formatting`, `media`, `file`, `status`, `image`, `data`, `brand`, `system`, `social`

## Selection Flow

When an icon is needed:

1. Identify the UI intent in English or Chinese (e.g., "search", "delete", "上传").
2. Search `references/icons/manifest.json` by `aliases`, `category`, and `use_for`.
3. If multiple matches, inspect the matching `references/icons/categories/{category}.json`.
4. Use the closest semantic match.
5. Check `avoid_for` to eliminate incorrect choices (e.g., do not use `UploadIcon` for "download").
6. Apply the correct size from the Size System table above.
7. Use `currentColor` unless the manifest explicitly marks the icon as multicolor.

## Import Rules

- If the target project has its own icon library, import from the project's icon index and follow the project's `AGENTS.md`.
- If the project has no icon library, use the SVG paths from `assets/icons/` or copy them into the project's `src/icons/` directory.
- Do not import from external icon libraries (Lucide, Material Icons, FontAwesome) when a Kimi icon exists for the same intent.

## Accessibility

- Icon-only buttons must have an accessible name (`aria-label` or visually hidden text).
- Decorative icons should use `aria-hidden="true"`.
- Loading icons should expose `aria-busy="true"` on the parent control.

## Do

- Use `currentColor` for all monochrome icons.
- Match icon size to the host component size per the mapping table.
- Use left icon when the icon helps identify the action.
- Use right icon for forward movement, expansion, or navigation-like actions.
- Check `avoid_for` before choosing an icon.
- Use suffixed variants only when context demands it.

## Don't

- Do not use external icon libraries when a Kimi icon exists.
- Do not guess icon meaning from filename alone — always check the manifest.
- Do not use `ShareIcon` for "export to file" or `UploadIcon` for "download".
- Do not scale icons arbitrarily outside the size system.
- Do not embed icon SVGs directly in business components — import from the icon library.
- Do not use more than one left + one right icon in a single Button.

## Custom Icons

Only create a custom icon when no Kimi icon in `assets/icons/` matches the semantic need.

A custom icon **must** match the Kimi icon style:

- **Type**: Outlined linear icon (1.8px stroke)
- **Base grid**: `24×24` viewBox
- **Color mode**: `currentColor`
- **Construction**: consistent stroke caps and joins, no fills, no gradients, no shadows
- **Visual weight**: match the optical density of existing icons in the same size context

If a custom icon is needed, reference existing icons in `assets/icons/` as a construction guide. Do not deviate from the 1.8px stroke or the outlined linear style.
