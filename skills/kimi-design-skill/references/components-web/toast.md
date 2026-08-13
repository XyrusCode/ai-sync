## Toast

Based on the Kimi Design System Web Toast:

- Figma file: `Kimi Design System Web`
- Node: `709:29433`
- Component group: `Message` / `Toast`

### Contract

Use Toast for non-blocking, transient feedback that auto-dismisses without requiring user interaction. Toast appears as a floating pill-shaped banner, usually at the top-center of the viewport. Do not use Toast for decisions that require immediate user action — use Dialog or Modal for those.

- **Purpose**: Operation feedback, system status, error recovery hints, completion confirmation.
- **Types**: `success`, `error`, `info`, `loading`, `caution`.
- **Action**: optional. A text-only action link can be appended for undo, retry, or navigation.
- **Auto-dismiss**: default `3000ms` (`3s`). Loading Toast persists until the async operation completes.
- **Position**: fixed, top-center of viewport, `16px` below the top edge.

Do not use Toast for form validation errors that belong inline, for wizard progress, or for passive decorative messages.

### Size And Dimensions

| Property | Value |
|----------|------:|
| Min height | `40px` |
| Width | `auto` (hug content) |
| Max width | `360px` |
| Icon size | `20px` |
| Icon-text gap | `8px` |
| Text vertical padding | `10px` |
| Horizontal padding | `12px` (`16px` for `info` type) |
| Radius | `radius.lg` (`12px`) |
| Action padding | `4px` |
| Action radius | `radius.xxs` (`4px`) |

Rules:

- Toast width is `auto` (hug content), capped at `360px` max. Content determines the width; only cap when text would exceed `360px`.
- Long text wraps to a second line; max `2` lines. The Toast widens to fit the content until it hits the `360px` cap.
- Single-line Toast is vertically centered. Multi-line Toast keeps the icon top-aligned to the first line.
- Multiple Toasts stack vertically with `8px` gap. Newest Toast appears at the top.

### Structure

```
Toast Frame (fixed, top-center, radius.lg)
└── Toast Content (HORIZONTAL, items CENTER, gap 8px)
    ├── Icon (20px, optional, color varies by type)
    ├── Message (flex: 1, max-w 320px, b2Regular, white)
    └── Action (optional, b2Emphasized, brand blue, p 4px)
```

**Toast Frame:**

- Layout: horizontal, `items: center`.
- Padding: `12px` horizontal (`16px` for `info` type), `10px` vertical.
- Radius: `radius.lg` (`12px`).
- Background: `color.mask.toastPc` (`#2b2b2b`).
- Shadow: none. Toast relies on the dark background for contrast.
- Position: fixed, top-center of viewport. Horizontal centering with `transform: translateX(-50%)`.

**Icon:**

- Size: `20px`.
- Color: type-dependent (see Variant Tokens below).
- From `icon-system.md`:
  - `success`: checkmark / success icon
  - `error`: close / error icon
  - `loading`: spinner / loading icon
  - `caution`: exclamation / alert icon
  - `info`: **no icon**
- Do not invent new icon colors outside the type mapping.

**Message:**

- Text: `typography.webUI.b2Regular`.
- Color: `color.always.white`.
- Max-width: `320px` inside the Toast.
- Line clamp: `2` lines max. If the message exceeds `2` lines, shorten the copy.

**Action:**

- Optional. Appears at the right end of the Toast.
- Text: `typography.webUI.b2Emphasized`.
- Color: `color.status.kimiBlue`.
- Padding: `4px`.
- Radius: `radius.xxs` (`4px`).
- Hover: `opacity: 0.8`.
- Do not use a Button component for the action. It is plain text inside the Toast.

### Token Relationship

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Toast background | `color.mask.toastPc` | `#2b2b2b` |
| Toast radius | `radius.lg` | `12px` |
| Message text | `typography.webUI.b2Regular` | — |
| Message color | `color.always.white` | `#ffffff` |
| Action text | `typography.webUI.b2Emphasized` | — |
| Action color | `color.status.kimiBlue` | `#1783ff` |
| Icon size | — | `20px` |
| Icon-text gap | — | `8px` |
| Action padding | — | `4px` |

### Variant Tokens

| Type | Icon presence | Icon color token | Icon fallback | Background | Use for |
|------|---------------|------------------|---------------|------------|---------|
| `success` | yes | `color.status.positiveGreen` | `#16c456` | `color.mask.toastPc` | Completed actions, saved changes |
| `error` | yes | `color.status.danger` | `#ff3849` | `color.mask.toastPc` | Failed operations, network errors |
| `info` | **no** | — | — | `color.mask.toastPc` | Neutral status, logout, account info |
| `loading` | yes | `color.labels.tertiary` | `rgba(0,0,0,0.45)` | `color.mask.toastPc` | In-progress operations |
| `caution` | yes | `color.status.orange` | `#ff9500` | `color.mask.toastPc` | Capacity warnings, slow responses |

Rules:

- The Toast **background** is constant across all types. Only the icon color changes.
- `info` type has **no icon**. Do not add an icon to info Toast.
- Loading icon uses `color.labels.tertiary` (a muted gray) rather than a bright color.
- Do not use `success` for decorative confirmation; reserve it for explicit operation feedback.
- Do not use `caution` for critical blocking errors that need a Dialog.

### Behavior

**Appearance (entry):**

- Entry: `opacity: 0` + `translateY(-16px)` + `scale(0.96)` → `opacity: 1` + `translateY(0)` + `scale(1)`.
- Duration: `350ms`.
- Easing: `cubic-bezier(0.23, 1, 0.32, 1)` (ease-out). Do not use CSS built-in `ease-out`.
- Toast enters above the viewport and settles at the top-center position.

**Auto-dismiss:**

- Default duration: `3000ms` (`3s`) for `success`, `error`, `info`, `caution`.
- `loading` Toast: persists until the async operation completes. Dismiss manually when done.
- Hovering over a Toast pauses the dismiss timer. Moving away resumes it.

**Action click:**

- Clicking the action text immediately triggers the action callback and dismisses the Toast.
- The action area is the only clickable part of the Toast (outside of hover). Do not make the entire Toast clickable unless the design explicitly requires it.

**Stacking:**

- Multiple Toasts stack vertically with `8px` gap.
- New Toasts appear at the top; older ones shift downward.
- When a new Toast enters, existing Toasts shift down by (Toast height + `8px`) with a `50ms` stagger delay between each.
- Shift duration: `300ms`, easing `cubic-bezier(0.23, 1, 0.32, 1)`.
- Maximum stack: `3` Toasts. If more arrive, dismiss the oldest before showing the new one.

**Exit:**

- Exit: `opacity: 1` + `translateY(0)` + `scale(1)` → `opacity: 0` + `translateY(-12px)` + `scale(0.97)`.
- Duration: `260ms` (~75% of enter duration).
- Easing: `cubic-bezier(0.23, 1, 0.32, 1)` (ease-out). **Never use `ease-in` on UI** — it starts slow and feels sluggish.
- Remove from DOM after exit animation completes.
- Only `transform` and `opacity` are animated. Do not animate width, height, or margin.

### Accessibility

- Toast container must have `role="status"` for `success`, `info`, `caution` and `role="alert"` for `error`.
- Use `aria-live="polite"` for `success`/`info`/`caution`/`loading`; `aria-live="assertive"` for `error`.
- Do not steal focus when a Toast appears.
- Respect `prefers-reduced-motion`: skip translateY, use instant opacity only.

### Toast vs Modal / Dialog

Toast is the lightest feedback layer. Modal and Dialog demand attention; Toast does not.

| | Toast | Dialog | Modal |
|--|-------|--------|-------|
| **Blocking** | No | Yes | Yes |
| **Duration** | 3s auto-dismiss | Until explicit choice | Until closed |
| **Position** | Top-center | Center viewport | Center viewport |
| **Actions** | 0–1 text link | 2 binary buttons | Flexible footer |
| **Use for** | Feedback, status | Binary decisions | Forms, detail |

When in doubt: if the user must make a choice before continuing, use **Dialog** or **Modal**. If the message is purely informational and auto-dismisses, use **Toast**.

### Code Guidance

```ts
type ToastType = "success" | "error" | "info" | "loading" | "caution";

interface ToastProps {
  type: ToastType;
  message: string;
  duration?: number; // ms, default 3000, loading uses Infinity
  action?: {
    label: string;
    onClick: () => void;
  };
  onDismiss?: () => void;
}

interface ToastContainerProps {
  toasts: ToastProps[];
  maxStack?: number; // default 3
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Toast must be rendered outside the normal document flow (Portal) to avoid clipping.
- **Do not change the Toast background per type.** Only the icon color changes.
- **Do not add a close (×) icon.** Toast auto-dismisses or is dismissed by action click.
- Action text inside Toast must not use the Button component; it is plain emphasized text.
- For stacking, use a fixed-position container with `flex-direction: column; gap: 8px`.

```tsx
// Correct: Success Toast
<Toast type="success" message="已成功绑定微信号" duration={3000} />

// Correct: Error Toast with retry action
<Toast
  type="error"
  message="上传失败，请重新上传"
  action={{ label: "重试", onClick: handleRetry }}
/>

// Correct: Loading Toast (persists until done)
<Toast type="loading" message="正在执行某个操作" />

// Correct: Caution Toast with upgrade action
<Toast
  type="caution"
  message="Kimi 回复较慢，升级会话体验 4 倍速"
  action={{ label: "去升级", onClick: handleUpgrade }}
/>
```

- Toast owns its appearance, animation, auto-dismiss timer, and stacking. The caller provides content, type, and optional action handlers.

---

