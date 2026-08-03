## Selection Control

Based on the Kimi Design System Web Selection Control:

- Figma file: `Kimi Design System Web`
- Checkbox node: `221:8932`
- Radio node: `674:4794`

Checkbox and Radio are now one unified visual component: **Selection Control**. They differ only by interaction semantics, not by shape or mark style.

### Contract

Use **Selection Control** for option selection. The component is always a circular control with a filled selected state and a white checkmark.

- **Checkbox behavior**: independent multi-select or on/off selection. Clicking a selected item toggles it off.
- **Radio behavior**: mutually exclusive single-select inside a group. Clicking a selected item keeps it selected.
- **Only visual shape**: circle.
- **Only selected mark**: thick white checkmark.

Do not create a square Checkbox variant. Do not use a traditional Radio dot. Do not use separate visual foundations for Checkbox and Radio.

| Behavior mode | Selection model | Visual shape | Selected visual | Click selected item |
|---------------|-----------------|--------------|-----------------|---------------------|
| `checkbox` | Multiple / independent | Circle only | Filled circle + thick white checkmark | Toggles off |
| `radio` | Single / mutually exclusive | Circle only | Filled circle + thick white checkmark | Remains selected |

### Size And Dimensions

| Size | Circle diameter | Checkmark box | Checkmark stroke | Typical use |
|------|----------------:|--------------:|-----------------:|-------------|
| `16` | `16px` | `10×10px` | `2.2px` | Compact rows, inline selectors, tight form fields |
| `20` | `20px` | `12×12px` | `2.4px` | Default form usage, standard option lists |
| `24` | `24px` | `14×14px` | `2.8px` | Large touch targets, lists, tables, bulk management |

Rules:

- Circle container is always square: `width == height == size`.
- Circle radius is always `50%`.
- Border width is `1.8px` for unchecked states.
- The checkmark must feel bold enough at small sizes. Do not use hairline strokes, thin icon defaults, or a downscaled full-size icon that visually becomes too light.
- The clickable area extends at least `8px` beyond the visible circle on all sides for accessibility.
- When used with a label, preserve a `4px`–`8px` gap between the circle and the label text.

### Structure

```
Selection Row (HORIZONTAL, items CENTER, clickable)
├── Circle (size 16/20/24)
│   ├── Unselected: ring only
│   └── Selected: filled circle + thick white checkmark
└── Label (optional, typography.webUI.b2Regular)
```

**Circle:**

- Container: square frame, `width == height == size`.
- Shape: full circle (`border-radius: 50%`).
- **Unselected**:
  - Outer ring: `1.8px` border.
  - Border color: `color.fills.f4`.
  - Center: transparent.
- **Selected**:
  - Outer fill: `color.labels.primary` by default.
  - Inner mark: thick checkmark, `color.always.white`, centered.
  - Border: none; fill replaces the border.
- **Disabled**:
  - Reduce opacity to `0.4` or replace colors with `color.labels.quaternary`.
  - Cursor: `not-allowed`.
  - Remove hover feedback.

**Checkmark:**

- Use a checkmark for both checkbox and radio behavior.
- Stroke color: `color.always.white`.
- Stroke width: size-specific values from the size table.
- Stroke caps and joins: `round`.
- Optical position: centered inside the circle, with the mark slightly above mathematical center if needed for visual balance.
- Do not use a dot for Radio.
- Do not use a thin checkmark. The mark should remain clearly visible in dark mode and at `16px`.

**Label:**

- Text: `typography.webUI.b2Regular`.
- Color: `color.labels.primary`.
- The entire row (circle + label) is the click target. Do not require the user to hit the small circle precisely.
- Label text must not wrap to a second line inside a horizontal group. Truncate with ellipsis if needed.

### Token Relationship

Use `tokens.json` for color. Component-specific metrics (diameter, border width, checkmark box, checkmark stroke) are component-level values from the Figma source and this spec.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Selected fill (default scene) | `color.labels.primary` | `rgba(0,0,0,0.9)` (light) / `rgba(255,255,255,0.84)` (dark) |
| Selected fill (destructive scene) | `color.status.danger` | `#ff3849` |
| Selected fill (positive scene) | `color.status.positiveGreen` | `#16c456` |
| Selected fill hover | `color.labels.primary` hover state | `rgba(37,37,37,1)` (light) / `rgba(255,255,255,0.848)` (dark) |
| Inner mark (checkmark) | `color.always.white` | `#ffffff` |
| Unselected border | `color.fills.f4` | `rgba(0,0,0,0.25)` |
| Unselected border hover | `color.labels.tertiary` | `rgba(0,0,0,0.45)` |
| Disabled opacity | — | `0.4` |
| Disabled fallback color | `color.labels.quaternary` | `rgba(0,0,0,0.3)` |
| Label text | `typography.webUI.b2Regular` | — |
| Label color | `color.labels.primary` | — |

### States

**Unselected (default):**

- Border: `color.fills.f4`, `1.8px`.
- Fill: transparent.
- Inner mark: none.
- Cursor: pointer.

**Unselected hover:**

- Border: `color.labels.tertiary`.
- Fill: transparent.
- Inner mark: none.

**Selected:**

- Fill: scene-dependent token (default `color.labels.primary`, destructive `color.status.danger`, positive `color.status.positiveGreen`).
- Inner mark: thick checkmark, `color.always.white`.
- Border: none.
- Cursor: pointer.

**Selected hover:**

- Fill: the hover counterpart of the selected scene token.
- Inner mark: unchanged (`color.always.white`, same stroke width).

**Disabled:**

- Apply `opacity: 0.4` to the entire control.
- If opacity is not available, fallback to `color.labels.quaternary` for both border and fill.
- Inner mark: `color.always.white` at reduced opacity.
- Cursor: `not-allowed`.
- Click events are suppressed.

### Behavior

#### Checkbox Mode

- Clicking an unselected Selection Control selects it.
- Clicking a selected Selection Control unselects it.
- Each checkbox-mode Selection Control is independent; siblings are not affected.
- Keyboard: `Space` toggles the focused control.

#### Radio Mode

- Clicking a radio-mode Selection Control selects it and deselects all other controls in the same group.
- Clicking an already selected radio-mode control does nothing; there is no toggle-off behavior.
- Inside a radio group, use `Tab` to focus the group, then `ArrowUp`/`ArrowDown` or `ArrowLeft`/`ArrowRight` to move selection between options.
- `Space` or `Enter` selects the focused radio-mode control.

#### Hover

- Unselected hover darkens the border.
- Selected hover darkens the fill.
- Disabled controls do not respond to hover.

### Accessibility

Use native inputs when possible:

- Checkbox mode: `<input type="checkbox">` visually represented by the circular Selection Control.
- Radio mode: `<input type="radio">` visually represented by the same circular Selection Control.

If custom roles are required:

- Checkbox mode uses `role="checkbox"` and `aria-checked="true"` / `"false"`.
- Radio mode uses `role="radio"` on each item and `role="radiogroup"` on the parent container.
- Radio groups need an accessible name via `aria-label` or `aria-labelledby`.
- Link each control to its label via `aria-labelledby` or wrap the control inside a `<label>`.
- Disabled controls must have `aria-disabled="true"`.
- Respect `prefers-reduced-motion`: skip any scale transition on state change.

### Code Guidance

```ts
type SelectionControlMode = "checkbox" | "radio";
type SelectionControlSize = 16 | 20 | 24;

interface SelectionControlProps {
  mode: SelectionControlMode;
  size?: SelectionControlSize;
  checked: boolean;
  disabled?: boolean;
  label?: string;
  value?: string;
  name?: string;
  onChange?: (checked: boolean, value?: string) => void;
}

interface SelectionControlGroupProps {
  mode: "radio" | "checkbox";
  name?: string;
  value?: string | string[];
  options: SelectionControlProps[];
  onChange?: (value: string | string[]) => void;
}
```

Implementation notes:

- Prefer one shared visual component for both Checkbox and Radio APIs.
- Keep legacy `Checkbox` and `Radio` wrappers only as semantic aliases if needed, but both must render the same circular Selection Control.
- Do not expose or implement a `variant="square"` option.
- The clickable area should extend at least `8px` beyond the visible circle on all sides.
- Render the circle with CSS borders/fills for easier state-driven color changes.
- The checkmark can be an SVG or CSS pseudo-element, but it must follow the size-specific stroke widths above.
- Circle fill transition: `background-color 150ms ease`.
- When used for terms agreement, the label may contain `<a>` links; ensure links remain clickable without triggering the selection toggle.
- The group owns radio-mode selection logic and keyboard navigation. Do not embed group state logic inside the single control.

```tsx
// Correct: checkbox-mode selection with label
<SelectionControl
  mode="checkbox"
  size={20}
  checked={agreed}
  onChange={setAgreed}
  label="已阅读并同意《模型服务协议》"
/>

// Correct: radio-mode selection inside a group
<SelectionControlGroup mode="radio" name="invoiceType" value="normal" onChange={setInvoiceType}>
  <SelectionControl mode="radio" value="normal" label="普通发票" size={20} checked />
  <SelectionControl mode="radio" value="special" label="专用发票" size={20} checked={false} />
</SelectionControlGroup>
```

Visual acceptance:

- Checkbox and Radio look identical when selected: filled circle + thick white checkmark.
- Checkbox and Radio look identical when unselected: circular ring.
- No square checkbox appears anywhere in the component system.
- No radio dot appears anywhere in the component system.
- At `16px`, the checkmark is still visibly bold, not hairline.

---
