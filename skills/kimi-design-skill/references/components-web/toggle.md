## Toggle (Switch)

Based on the Kimi Design System Web Switch/Toggle:

- Figma file: `Kimi Design System Web`
- Node: `4377:20705`
- Component group: `Switch`

### Contract

Use Toggle for binary on/off state changes that take immediate effect. Toggle is a pill-shaped track with a sliding thumb. Do not use Toggle for settings that require a separate save action, for multi-step confirmations, or when the state change is destructive or irreversible.

- **Purpose**: Settings toggles, feature enable/disable, preference switches.
- **Sizes**: `lg` (`44×24`), `sm` (`32×18`). Use `lg` as the default.
- **States**: `on`, `off`, `hover`, `disabled`.
- **Thumb behavior**: slides left (off) or right (on). On hover, the thumb shrinks slightly and shifts toward the active edge.
- **Non-negotiable shape**: the thumb is a true circle in every state. Its width and height must always be equal, and its radius must be `50%` / `radius.full`.

Do not use Toggle for navigation, for wizard steps, or for actions that should use a Button or Checkbox.

### Size And Dimensions

Track:

| Size | Width | Height | Radius | Thumb size (default) | Thumb size (hover) | Typical use |
|------|------:|-------:|--------|---------------------:|-------------------:|-------------|
| `lg` | `44px` | `24px` | `999px` | `20×20` | `16×16` | Default, standard form settings |
| `sm` | `32px` | `18px` | `999px` | `14×14` | `12×12` | Compact rows, dense toolbars |

Thumb position:

| Size | State | Thumb X | Thumb Y | Thumb size |
|------|-------|--------:|--------:|-----------:|
| `lg` | off | `2px` | `2px` | `20×20` |
| `lg` | off hover | `4px` | `4px` | `16×16` |
| `lg` | on | `22px` | `2px` | `20×20` |
| `lg` | on hover | `24px` | `4px` | `16×16` |
| `sm` | off | `2px` | `2px` | `14×14` |
| `sm` | off hover | `2px` | `3px` | `12×12` |
| `sm` | on | `16px` | `2px` | `14×14` |
| `sm` | on hover | `18px` | `3px` | `12×12` |

Rules:

- Thumb is always circular. Use `border-radius: 50%` or `radius.full`; do **not** use fixed small corner radii such as `4px` or `3.2px`.
- When hover shrinks the thumb, only the diameter changes. The thumb must still read as a circle at every size and state.
- Never model the thumb as a rounded rectangle, capsule, squircle, or token-radius box. The only acceptable thumb shape is a circle.
- Track is always a full pill (`radius: 999px`).
- Preserve track height and thumb proportions across sizes.

### Structure

```
Toggle Track (pill, full radius)
└── Thumb (circle, slides left/right)
```

**Track:**

- Width/height per size table above.
- Radius: `999px` (full pill).
- Background: state-dependent token (see Token Relationship).

**Thumb:**

- Shape: circle at all sizes and states.
- Width equals height in default, hover, on, off, and disabled states.
- Fill: `color.always.white` (default and hover); `color.others.whiteOnDarkDisabled` (disabled).
- Position: per thumb position table above.
- On hover, thumb shrinks and shifts toward the active edge:
  - `lg` off → off hover: shrinks by `4px`, shifts right `2px`
  - `lg` on → on hover: shrinks by `4px`, shifts right `2px`
  - `sm` off → off hover: shrinks by `2px`, shifts down `1px`
  - `sm` on → on hover: shrinks by `2px`, shifts right `2px`, shifts down `1px`

### Token Relationship

Use `tokens.json` for color. Toggle-specific metrics (width, height, thumb size, position) are component-level values from the Figma source.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| On track bg | `color.labels.primary` | `rgba(0,0,0,0.9)` (light) / `rgba(255,255,255,0.84)` (dark) |
| Off track bg | `color.fills.f3` | `rgba(0,0,0,0.15)` (light) / `rgba(255,255,255,0.18)` (dark) |
| On disabled track bg | `color.fills.f2` | `rgba(0,0,0,0.05)` (light) / `rgba(255,255,255,0.10)` (dark) |
| Off disabled track bg | `color.fills.f3` | `rgba(0,0,0,0.15)` (light) / `rgba(255,255,255,0.18)` (dark) |
| Thumb (default/hover) | `color.always.white` | `#ffffff` |
| Thumb (disabled) | `color.others.whiteOnDarkDisabled` | `#ffffff` (light) / `rgba(255,255,255,0.4)` (dark) |
| Disabled opacity (off) | — | `0.4` on entire component |

### States

**Off (default):**

- Track: `color.fills.f3`.
- Thumb: `color.always.white`, default size, left-aligned.
- Cursor: pointer.

**Off hover:**

- Track: `color.fills.f3` (unchanged).
- Thumb: `color.always.white`, circular hover size, shifted slightly right.
- Cursor: pointer.

**On (default):**

- Track: `color.labels.primary`.
- Thumb: `color.always.white`, default size, right-aligned.
- Cursor: pointer.

**On hover:**

- Track: `color.labels.primary` (unchanged).
- Thumb: `color.always.white`, circular hover size, shifted further right.
- Cursor: pointer.

**Disabled (off):**

- Track: `color.fills.f3`.
- Entire Toggle: `opacity: 0.4`.
- Thumb: `color.others.whiteOnDarkDisabled`.
- Cursor: `not-allowed`.
- No hover response.

**Disabled (on):**

- Track: `color.fills.f2`.
- Thumb: `color.others.whiteOnDarkDisabled`.
- Cursor: `not-allowed`.
- No hover response.

### Behavior

**Toggle:**

- Clicking a Toggle switches it between `on` and `off`.
- The state change should take effect immediately (no separate save required).
- When toggling, the thumb should slide from one side to the other with a short transition.
- Do not animate track color changes unless the transition is very brief (`150ms` or less).

**Hover:**

- Thumb shrinks and shifts when hovered, giving a tactile "pre-press" feel.
- Disabled Toggles do not respond to hover.

**Transition:**

- Thumb slide: `150ms`–`200ms`, `ease-out`.
- Thumb size change on hover: `100ms`–`150ms`.
- Track color change: `150ms`.

### Accessibility

- Use `role="switch"` on the Toggle element.
- Use `aria-checked="true"` for on; `"false"` for off.
- Disabled Toggles must have `aria-disabled="true"`.
- The Toggle must be focusable via keyboard (`Tab`).
- `Space` or `Enter` toggles the focused Toggle.
- Respect `prefers-reduced-motion`: skip thumb slide animation, use instant state change.

### Code Guidance

```ts
type ToggleSize = "lg" | "sm";

interface ToggleProps {
  checked: boolean;
  size?: ToggleSize;
  disabled?: boolean;
  onChange?: (checked: boolean) => void;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Use `transform: translateX()` for thumb sliding to avoid layout shifts.
- Keep the thumb circular with `width === height` and `border-radius: 50%` in default, hover, on, off, and disabled states.
- Track color and thumb position should both transition smoothly.
- On hover, scale the thumb down uniformly and shift it. Use one scalar `scale()` value, never separate `scaleX()` / `scaleY()` values.
- Do not hard-code thumb positions; use CSS custom properties mapped to size tokens.

Visual acceptance:

- `lg` default/on/off thumb renders as a `20px` circle.
- `lg` hover thumb renders as a `16px` circle.
- `sm` default/on/off thumb renders as a `14px` circle.
- `sm` hover thumb renders as a `12px` circle.
- Browser inspection should show equal computed width and height for the thumb in every state.

```tsx
// Correct: Toggle with label
<div>
  <label htmlFor="notifications">接收通知</label>
  <Toggle id="notifications" checked={enabled} onChange={setEnabled} />
</div>
```

- The Toggle component owns its visual state (track color, thumb position, size). The parent owns the checked state.

---
