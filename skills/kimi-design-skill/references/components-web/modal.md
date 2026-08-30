## Modal

Based on the Kimi Design System Web Modal:

- Figma file: `Kimi Design System Web`
- Node: `563:45804`
- Component group: `Modal`

### Contract

Use Modal for focused, interruptive tasks that require user decision or input before returning to the main flow. Do not use Modal for passive notifications, inline forms, or content that belongs in a dedicated page.

- **Purpose**: Confirmations, single-step forms, content detail, choice dialogs.
- **Sizes**: `small`, `medium`, `large`. Use `medium` as the default for general dialogs.
- **States**: `open`, `closed`, `loading` (when primary action is in progress).
- **Content slots**: `title` (required), `description` (optional), `children` (custom content area, optional), `footer` (action buttons, required when user decision is needed).
- **Backdrop**: Required. Use `color.mask.base` to reduce background attention.

Do not stack multiple Modals. Do not make a Modal so tall that it exceeds viewport height; scroll the content area instead of stretching the Modal frame.

### Stacking And Layering

Modal and Dialog **must not coexist** in the viewport at the same time. Only one interruptive overlay (Modal or Dialog) may be open at any moment.

- If a Dialog needs to be triggered from within a Modal, **close the Modal first**, then open the Dialog. After the Dialog resolves, reopen the Modal if needed.
- Do not rely on z-index to place a Dialog above a Modal. The correct approach is sequential display, not overlapping layers.
- A single open Modal uses the Web layer values from `web-best-practices.md` (`--z-modal-backdrop`, `--z-modal`). These layer values position the Modal in the page stack; sequential open/close logic prevents Modal/Dialog overlap.

### Size And Dimensions

Modal frame:

| Size | Width | Height | Typical use |
|------|------:|-------:|-------------|
| `small` | `360px` | `360px` | Compact confirmations, single-choice dialogs, mobile-like breakpoints |
| `medium` | `560px` | `420px` | Default dialogs, forms with moderate content |
| `large` | `720px` | `420px` | Complex forms, content detail with side info, wide tables |

Rules:

- Height is fixed at `420px` for `medium` and `large`; content area scrolls if overflow.
- `small` uses `360px × 360px` as a compact square frame.
- Modal is centered in viewport. Do not anchor to edges by default.
- On viewports narrower than the Modal width, Modal should shrink with a minimum side inset of `16px` and content area becomes scrollable.

### Structure

Modal follows a strict vertical stack inside a `24px` padded frame:

```
Modal Frame (radius.xl, bg tertiary)
  └── Content (VERTICAL, gap 16px, flex: 1)
      ├── Title Row (HORIZONTAL, SPACE_BETWEEN)
      │   ├── Title text
      │   └── Close Button (24×24)
      ├── Description (optional, single or multi-line)
      ├── Body (flex: 1, scrollable; content provided by caller)
      └── Footer (HORIZONTAL, right-aligned, gap 8px)
```

**Title row:**

- Height: `24px`
- Layout: horizontal, `SPACE_BETWEEN`, center-aligned
- Left: title text only (`typography.webUI.t2Emphasized`). Do not add an icon to the title.
- Right: Close button
- Title text color: `color.labels.primary`

**Close button:**

- Container: `24px × 24px`.
- Icon: `CloseIcon` from `icon-system.md`; use `currentColor`.
- Follow `icon-system.md` Size System for standalone icon buttons.

**Description:**

- Text: `typography.webUI.b2Regular`.
- Color: `color.labels.primary`.
- Optional. Omit if the title alone is sufficient.
- Multi-line descriptions are allowed; keep within `3` lines when possible.

**Body:**

- Content area for caller-provided components: forms, inputs, lists, text, or any custom content.
- Uses `layoutGrow: 1` (flex: 1) to fill available Modal height.
- Scrollable when content exceeds available space.
- Do not prescribe background, padding, or radius here; the content component owns its own styling.

**Footer:**

- Layout: horizontal, right-aligned (`end`), center-aligned vertically.
- Gap: `8px`.
- Use **Button** component for all actions; follow Button rules for variant, size, and state.
- Default button size: `32`.
- Action order: secondary (left) → primary (right).
- Do not define new button styles inside Modal.

### Token Relationship

Use `tokens.json` for color, typography, radius, and effects.

Modal-specific metrics (width, height, padding) are component-level values from the Figma source. Do not convert them into new spacing tokens unless the design system later defines those tokens.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Modal background | `color.background.tertiary` | `#ffffff` (light) |
| Modal radius | `radius.xl` | `16px` |
| Title text | `typography.webUI.t2Emphasized` | — |
| Title color | `color.labels.primary` | — |
| Description text | `typography.webUI.b2Regular` | — |
| Description color | `color.labels.primary` | — |
| Backdrop | `color.mask.base` | `rgba(0,0,0,0.4)` (light) / `rgba(0,0,0,0.6)` (dark) |
| Footer button gap | — | `8px` |

### Variant Tokens

**Size differences:**

| Size | Content width | Content area height | Notes |
|------|--------------:|--------------------:|-------|
| `small` | `312px` | `188px` | Compact; content area remains proportional |
| `medium` | `512px` | `248px` | Default |
| `large` | `672px` | `248px` | Wide content area, same height as medium |

Rules:

- Content width = Modal width − `48px` (left/right padding `24px` each).
- Only width changes across sizes; padding, radius, typography, and button specs stay constant.
- Do not use `small` for multi-step flows or complex forms.
- Do not use `large` for simple confirmations (avoids visual imbalance).

### Behavior

**Opening:**

- Follow `references/animation.md` §4.5 Modal / Dialog pattern.
- Content: `opacity: 0` + `scale(0.96)` → `opacity: 1` + `scale(1)`.
- Backdrop fades in simultaneously.
- Focus moves to the first focusable element (primary action, or first input in content area).

**Closing:**

- Follow `references/animation.md` §4.2 Exit pattern (exit faster than enter, ~75% of enter duration).
- Triggered by: clicking backdrop, clicking Close, pressing Escape, completing the primary action, or explicitly canceling.
- Restore focus to the element that opened the Modal.

**Loading state:**

- When the primary action triggers an async operation, set the primary Button to `loading` per the Button component spec.
- Modal remains open; do not replace the entire surface with a spinner.

**Scroll handling:**

- If content area exceeds available height, scroll only the content area, not the entire Modal.
- Title, description, and footer remain fixed (sticky).

**Backdrop:**

- Required. Modal must be paired with a fullscreen mask.
- Use `color.mask.base` for the backdrop overlay.
- Modal does **not** use a stroke/border; the mask provides the visual isolation.
- Clicking backdrop should close the Modal unless the action is critical (e.g., unsaved changes). For critical cases, disable backdrop click-to-close.

### Accessibility

- Use `role="dialog"` and `aria-modal="true"` on the Modal container.
- Trap focus inside the Modal while open (tab cycles within Modal).
- Close button must have `aria-label="关闭"` or equivalent.
- Title must be linked via `aria-labelledby` to the title text element.
- When Modal opens, previous focus position must be saved and restored on close.
- Respect `prefers-reduced-motion`: skip scale animation, use instant opacity transition.

### Code Guidance

```ts
type ModalSize = "small" | "medium" | "large";

interface ModalProps {
  open: boolean;
  size?: ModalSize;
  title: string;
  description?: string;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  onClose?: () => void;
  closeOnBackdrop?: boolean;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Content area should use `overflow-y: auto` with `flex: 1`.
- Do not hard-code Modal widths; use CSS custom properties mapped to size tokens.
- **Footer must compose Button instances. Do not define new button styles inside Modal.**

```tsx
// Correct: footer composes Button instances from the Button component
<Modal
  footer={
    <>
      <Button variant="secondary" size={32} onClick={onCancel}>
        取消
      </Button>
      <Button variant="primary" size={32} onClick={onConfirm} loading={isLoading}>
        确认
      </Button>
    </>
  }
/>
```

- Footer layout (right-aligned, gap 8px) belongs in Modal. Button styling (variant, size, state) belongs in Button.
- The `footer` prop accepts any `React.ReactNode`, but the only correct value is a composition of Button instances.

---
