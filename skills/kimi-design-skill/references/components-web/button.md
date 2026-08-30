## Button

Based on the Kimi Design System Web Button:

- Figma file: `Kimi Design System Web`
- Node: `3411:19530`
- Component group: `Buttons`

### Contract

Use Button for explicit actions: submit, confirm, cancel, navigate, open a flow, or trigger a visible change. Do not use buttons as static labels, tags, decoration, or emphasis without an action.

- **Variants**: `primary`, `secondary`, `outline`.
- **Sizes**: `44`, `32`, `26`; use `32` as the default web action size.
- **Danger**: `true` only for destructive or irreversible actions.
- **States**: `default`, `hover`, `disabled`, `loading`, plus `focus-visible` in implementation.
- **Content forms**: text only, left icon + text, text + right icon. Do not use both left and right icons unless a product case explicitly requires it.
- **Icon rules**: from `icon-system.md`. Match icon size to the Button size table; use `currentColor`.

Do not invent additional variants such as gradient, glass, neon, pill, link-button, or floating-button unless a later component rule explicitly defines them.

### Size And Spacing

Size tiers:

| Size | Height | Radius | Text token | Icon size | Typical use |
| --- | ---: | --- | --- | ---: | --- |
| `44` | `44px` | `radius.lg` | `typography.webUI.t2Emphasized` | `20px` | High-emphasis primary actions, large dialogs, onboarding or empty-state actions |
| `32` | `32px` | `radius.md` | `typography.webUI.b2Emphasized` | `18px` | Default web actions, forms, dialogs, toolbars |
| `26` | `26px` | `radius.sm` | `typography.webUI.c1Emphasized` | `16px` | Dense surfaces, compact rows, inline actions |

Default, text only:

| Size | Top | Bottom | Left | Right |
| --- | ---: | ---: | ---: | ---: |
| `44` | `10px` | `10px` | `14px` | `14px` |
| `32` | `6px` | `6px` | `10px` | `10px` |
| `26` | `4px` | `4px` | `8px` | `8px` |

LeftIcon, icon on the left:

| Size | Top | Bottom | Left | Right | Icon-text gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| `44` | `10px` | `10px` | `10px` | `12px` | `6px` |
| `32` | `6px` | `6px` | `8px` | `10px` | `4px` |
| `26` | `4px` | `4px` | `6px` | `8px` | `2px` |

RightIcon, icon on the right:

| Size | Top | Bottom | Left | Right | Icon-text gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| `44` | `10px` | `10px` | `12px` | `10px` | `6px` |
| `32` | `6px` | `6px` | `10px` | `8px` | `4px` |
| `26` | `4px` | `4px` | `8px` | `6px` | `2px` |

MinWidth:

| Size | MinWidth |
| --- | ---: |
| `44` | `72px` |
| `32` | `62px` |
| `26` | `52px` |

Rules:

- When MinWidth is used as a fixed width or lower bound, vertical padding follows Default and text remains horizontally centered.
- Preserve height, radius, typography, icon size, gap, and padding across states for the same size.
- Width is usually content-driven, except when loading or fixed-width usage requires locking width to prevent layout shift.

### Token Relationship

Use `tokens.json` for typography, radius, color, and effects.

Button height, padding, gap, icon size, and MinWidth are component metrics from the Button source matrix. Do not convert them into new spacing tokens unless the design system later defines those tokens.

If a referenced typography, radius, color, or effect token is missing from `tokens.json`, record the mapping gap instead of inventing a new token.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Primary fill | `color.labels.primary` | — |
| Primary text/icon | `color.background.primary` or `color.always.white` | — |
| Secondary fill | `color.fills.f1` | — |
| Secondary hover fill | `color.fills.f2` | — |
| Outline border | `color.separator.s1` | — |
| Danger fill | `color.status.danger` | — |
| Danger text | `color.status.danger` | — |
| Disabled text/icon | `color.labels.quaternary` | — |
| Text (size 44) | `typography.webUI.t2Emphasized` | — |
| Text (size 32) | `typography.webUI.b2Emphasized` | — |
| Text (size 26) | `typography.webUI.c1Emphasized` | — |
| Radius (size 44) | `radius.lg` | — |
| Radius (size 32) | `radius.md` | — |
| Radius (size 26) | `radius.sm` | — |

### Variant Tokens

Token mapping status: mapped to current `tokens.json`.

| Variant | Default | Hover | Danger |
| --- | --- | --- | --- |
| `primary` | fill `color.labels.primary`; text/icon inverse white | restrained overlay; record token gap if needed | fill `color.status.danger`; text/icon white |
| `secondary` | fill `color.fills.f1`; text/icon `color.labels.primary` | fill `color.fills.f2` | keep secondary surface; text/icon `color.status.danger` |
| `outline` | transparent/neutral background; `0.5px` `color.separator.s1` border; text/icon `color.labels.primary` | subtle fill while preserving border | text/icon `color.status.danger`; do not fill red unless variant becomes `primary` |

Disabled buttons use low-emphasis fill where needed and `color.labels.quaternary` for text and icons. If a required semantic token is missing, note the mapping gap instead of inventing a new permanent token.

### Behavior

- Use only one `primary` button in a local action group.
- Button groups usually right-align the primary action in dialogs and forms.
- Use size `44` for prominent creation, confirmation, onboarding, or empty-state actions.
- Use size `26` for dense rows, menus, and inline actions.
- Loading implies disabled interaction, prevents duplicate submission, and should preserve width when shifting would be distracting.
- Disabled and loading buttons should not trigger hover styles.
- Focus-visible must be keyboard accessible and must not shift layout.
- Use short verb-led labels. Prefer 2-6 Chinese characters or 1-3 English words.
- Avoid vague labels such as `OK`, `Submit`, or `Click here` when a specific action is available.
- Use destructive labels explicitly, such as `删除`, `移除`, `退出`, or `Revoke`.

### Accessibility

- Use semantic `<button>` elements for actions; use `<a>` only for navigation.
- Disabled buttons must be programmatically disabled when appropriate.
- Loading buttons should expose busy state when the framework supports it.
- Icon-only buttons are not covered by this Button spec; if used, they must have an accessible name.
- For icon selection, search `references/icons/manifest.json`; use `currentColor`; match icon size to the Button size table.

### Code Guidance

```ts
type ButtonVariant = "primary" | "secondary" | "outline";
type ButtonSize = 26 | 32 | 44;

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  danger?: boolean;
  disabled?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Keep size-specific height, padding, icon size, typography, radius, and gap centralized.
- Do not hard-code one-off button styles in product views.

---

