## Dialog

Based on the Kimi Design System Web Dialog:

- Figma file: `Kimi Design System Web`
- Node: `635:15302`
- Component group: `Dialog`

### Contract

Use Dialog for **pure-text alert scenarios** where the user makes a single binary choice (confirm or cancel). Dialog is the lightest interruptive overlay. Do not use Dialog for forms, content reading, multi-step flows, or any surface that requires scrolling or complex interaction — use **Modal** for those.

- **Purpose**: Destructive confirmations (delete, revoke, logout), irreversible action warnings, simple acknowledgments.
- **Width**: **only `360px`**. No size variants.
- **States**: `open`, `closed`.
- **Content**: title (required, short), description (required, 1–3 lines), two footer actions (primary + secondary).
- **Backdrop**: Required. Dialog must be paired with a fullscreen mask (`color.mask.base`). Dialog does not use a stroke/border; the mask provides visual isolation.

Do not add a Close button to Dialog. The user must make an explicit choice via the footer actions. Do not nest Dialogs. Do not use Dialog for passive notifications — use Toast or inline messages instead.

### Stacking And Layering

Dialog and Modal **must not coexist** in the viewport at the same time. Only one interruptive overlay (Dialog or Modal) may be open at any moment.

- If a Dialog is triggered from within a Modal, **close the Modal first**, then open the Dialog. After the Dialog resolves, reopen the Modal if the flow requires it.
- Do not rely on z-index to place a Dialog above a Modal. The correct approach is sequential display, not overlapping layers.
- A single open Dialog uses the Web layer values from `web-best-practices.md` (`--z-dialog-backdrop`, `--z-dialog`). These layer values position the Dialog in the page stack; sequential open/close logic prevents Dialog/Modal overlap.
- Do not open a second Dialog while another Dialog is already open. Replace the content of the existing Dialog instead.

### Size And Dimensions

| Property | Value |
|----------|------:|
| Width | `360px` (fixed) |
| Padding | `16px` (all sides) |
| Radius | `radius.xl` (`16px`) |
| Max content width | `328px` (`360px` − `16px` × 2) |

Rules:

- Dialog width is **always** `360px`. Do not stretch, shrink, or add responsive breakpoints.
- Content must fit without scrolling. If the text exceeds ~3 lines, shorten the copy or switch to Modal.
- Dialog is centered in viewport, same as Modal.

### Structure

```
Dialog Frame (radius.xl, grouped bg secondary)
  └── Content (VERTICAL, gap 12px)
      ├── Title Row (HORIZONTAL, SPACE_BETWEEN)
      │   └── Title text
      ├── Body (VERTICAL, gap 16px)
      │   ├── Description text
      │   └── Footer (HORIZONTAL, right-aligned, gap 8px)
      │       ├── Secondary Button (cancel)
      │       └── Primary Button (confirm)
```

**Title:**

- Text: `typography.webUI.t2Emphasized` (`16/24`, Medium).
- Color: `color.labels.primary`.
- Single line. No icons. No Close button.
- Examples: `提示`, `确认删除`, `退出登录`.

**Description:**

- Text: `typography.webUI.b2Regular` (`14/20`, Regular).
- Color: `color.labels.primary`.
- 1–3 lines. Must fit within the `328px` content width without scrolling.
- Be explicit about consequences for destructive actions.

**Footer:**

- Layout: horizontal, right-aligned (`end`), center-aligned vertically.
- Gap: `8px`.
- Use **Button** component for both actions; follow Button rules.
- Default button size: `32`.
- **Secondary** (left): cancel, dismiss, or safe action. Text must be explicit (`取消`, `不删除`).
- **Primary** (right): confirm or destructive action. For destructive actions, use Button `danger` variant.
- Action order: secondary (left) → primary (right).

### Token Relationship

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Dialog background | `color.groupedBackground.secondary` | `#ffffff` (light) |
| Dialog radius | `radius.xl` | `16px` |
| Title text | `typography.webUI.t2Emphasized` | — |
| Title color | `color.labels.primary` | — |
| Description text | `typography.webUI.b2Regular` | — |
| Description color | `color.labels.primary` | — |
| Backdrop | `color.mask.base` | `rgba(0,0,0,0.4)` (light) / `rgba(0,0,0,0.6)` (dark) |
| Footer button gap | — | `8px` |

### Behavior

**Opening / Closing:**

- Follow `references/animation.md` §4.5 Modal / Dialog pattern.
- Content: `opacity: 0` + `scale(0.96)` → `opacity: 1` + `scale(1)`.
- Backdrop fades in simultaneously.
- No Close button. Closing requires clicking a footer action or the backdrop.
- Backdrop click should trigger the **safe** action (equivalent to secondary/cancel), not the primary action.

**Focus management:**

- For destructive Dialogs, set initial focus on the **secondary** (cancel) button to give the user extra pause.
- For non-destructive Dialogs, set initial focus on the **primary** button for efficiency.

### Accessibility

- Use `role="alertdialog"` (not `role="dialog"`) because Dialog demands an immediate user response.
- Trap focus inside the Dialog while open.
- The title must be linked via `aria-labelledby` to the title text element.
- The description must be linked via `aria-describedby` to the description text element.
- Respect `prefers-reduced-motion`: skip scale animation, use instant opacity transition.

### Dialog vs Modal

| | Dialog | Modal |
|--|--------|-------|
| **Width** | Fixed `360px` | `small`/`medium`/`large` |
| **Content** | Pure text, 1–3 lines | Can contain forms, lists, complex content |
| **Close button** | No | Yes |
| **Actions** | Exactly 2 (binary choice) | Flexible footer, can be 1+ |
| **Role** | `alertdialog` | `dialog` |
| **Use for** | Confirmations, warnings | Forms, detail, multi-step |

When in doubt: if the surface needs a Close button or more than two actions, use **Modal**.

### Code Guidance

```ts
interface DialogProps {
  open: boolean;
  title: string;
  description: string;
  footer?: React.ReactNode; // composition of Button instances
  onBackdropClick?: () => void;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- **Pass Button instances via the `footer` prop; do not embed button styles inside Dialog.**
- Use Button `size={32}` for Dialog actions.
- For destructive Dialogs, the cancel Button should be on the left; the confirm Button on the right with `variant="primary"` and `danger` if applicable.
- Do not add a Close button or an `×` icon. Dialog is closed by explicit choice only.
- Do not make the Dialog width responsive. It is always `360px`.

---
