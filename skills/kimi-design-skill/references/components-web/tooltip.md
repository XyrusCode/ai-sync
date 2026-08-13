## Tooltip

Based on the Kimi Design System Web Tooltip:

- Figma file: `Kimi Design System Web`
- Node: `42:365`
- Component group: `Tooltip`

### Contract

Use Tooltip for contextual hints, labels, or brief explanations that appear on hover or focus of a trigger element. Tooltip does not contain interactive content beyond a single optional action in Coach Mark mode. Do not use Tooltip for content that requires scrolling, forms, or multiple actions — use Modal or Popover for those.

- **Purpose**: Contextual hint, element label, brief explanation, feature discovery (Coach Mark).
- **Variants**: `default` (simple text), `coach-mark` (rich tooltip with title, description, action).
- **Directions**: `top`, `bottom`, `left`, `right`.
- **Trigger**: `hover` or `focus` on the target element.
- **Auto-hide**: hides when mouse leaves the trigger or focus moves away.

Do not use Tooltip for navigation, for content that should persist, or for actions that require user confirmation.

### Size And Dimensions

**Default Tooltip:**

| Property | Value |
|----------|------:|
| Max width | `240px` |
| Padding | `12px` horizontal, `8px` vertical |
| Radius | `radius.md` (`10px`) |
| Arrow width | `10px` |
| Arrow height | `4px` |
| Text max-width | `216px` (240px − 12px × 2) |

**Coach Mark:**

| Property | Value |
|----------|------:|
| Width | `240px` |
| Padding | `16px` |
| Internal gap | `12px` |
| Radius | `radius.xl` (`16px`) |
| Title icon | `24px` |
| Step text | `typography.webUI.c1Emphasized` |

Rules:

- Tooltip width is `auto` (hug content), capped at `240px`.
- Text wraps at `240px` max. Single line preferred; `2` lines max for default Tooltip.
- Arrow is centered on the Tooltip edge by default. Offset is allowed if the trigger is near a viewport edge.
- Coach Mark always uses `bottom` arrow and `top` direction (points upward from the trigger).

### Structure

```
Tooltip (absolute, positioned relative to trigger)
├── Arrow (10×4px triangle, pointing toward trigger)
└── Tooltip Body
    ├── Default: Text only (b2Regular, white)
    └── Coach Mark:
        ├── Header (HORIZONTAL, gap 8px)
        │   ├── Icon (24px)
        │   └── Title (t2Emphasized, white)
        ├── Description (b2Regular, white)
        └── Footer (HORIZONTAL, space-between)
            ├── Step indicator (c1Emphasized, labels.secondary)
            └── Action Button (b2Emphasized, labels.primary)
```

**Tooltip Body (default):**

- Background: `color.mask.toastPc` (`#2b2b2b`).
- Radius: `radius.md` (`10px`).
- Padding: `12px` horizontal, `8px` vertical.
- Text: `typography.webUI.b2Regular`. Color: `color.always.white`.
- No shadow. The dark background provides sufficient contrast.

**Arrow:**

- Size: `10px` wide, `4px` tall.
- Shape: isosceles triangle.
- Color: matches the Tooltip body background (`color.mask.toastPc`).
- Position: centered on the edge that faces the trigger.
- Offset: up to `8px` from center when the trigger is near a viewport edge.

**Coach Mark Body:**

- Background: `color.mask.toastPc`.
- Radius: `radius.xl` (`16px`).
- Padding: `16px`.
- Internal layout: vertical, gap `12px`.
- **Header**: horizontal, gap `8px`.
  - Icon: `24px`, from `icon-system.md`.
  - Title: `typography.webUI.t2Emphasized`. Color: `color.always.white`.
- **Description**: `typography.webUI.b2Regular`. Color: `color.always.white`. Max-width `216px`.
- **Footer**: horizontal, `space-between`.
  - Step text: `typography.webUI.c1Emphasized`. Color: `color.labels.secondary`.
  - Action: `typography.webUI.b2Emphasized`. Color: `color.labels.primary`. Background `color.fills.f2` (light) or `rgba(255,255,255,0.1)` (dark). Padding `10px` horizontal. Height `32px`. Radius `radius.md`.

### Token Relationship

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Tooltip background | `color.mask.toastPc` | `#2b2b2b` |
| Default radius | `radius.md` | `10px` |
| Coach Mark radius | `radius.xl` | `16px` |
| Default text | `typography.webUI.b2Regular` | — |
| Text color | `color.always.white` | `#ffffff` |
| Coach title | `typography.webUI.t2Emphasized` | — |
| Coach description | `typography.webUI.b2Regular` | — |
| Step text | `typography.webUI.c1Emphasized` | — |
| Step color | `color.labels.secondary` | `rgba(255,255,255,0.56)` |
| Action text | `typography.webUI.b2Emphasized` | — |
| Action color | `color.labels.primary` | `rgba(255,255,255,0.84)` |
| Action bg | `color.fills.f2` | `rgba(255,255,255,0.1)` (dark) |

### Direction Rules

| Direction | Arrow position | Tooltip position |
|-----------|----------------|------------------|
| `top` | Bottom edge, centered | Above trigger |
| `bottom` | Top edge, centered | Below trigger |
| `left` | Right edge, centered | Left of trigger |
| `right` | Left edge, centered | Right of trigger |

Rules:

- Default direction is `top`. Use `bottom` if the trigger is near the top edge of the viewport.
- The arrow is always centered on the Tooltip edge that faces the trigger.
- If the trigger is near a viewport edge, offset the arrow up to `8px` to keep the Tooltip within the viewport.
- Coach Mark always uses `bottom` direction (arrow at top, Tooltip below trigger).

### Behavior

**Appearance:**

- Follow `references/animation.md` §4.6 Tooltip pattern.
- Entry: `opacity: 0` + `scale(0.97)` → `opacity: 1` + `scale(1)`.
- Duration: `125ms`.
- Easing: `cubic-bezier(0.23, 1, 0.32, 1)` (ease-out).
- Delay before first appearance: `300ms` to prevent accidental activation on quick mouse passes.
- Subsequent Tooltips (after one is already open): open instantly with `0ms` transition.

**Trigger and hide:**

- Show on `mouseenter` or `focus` of the trigger element.
- Hide on `mouseleave` or `blur` of the trigger element.
- Hide delay: `100ms` after mouse leaves to allow crossing the gap between trigger and Tooltip.
- Coach Mark action click: triggers the action callback and hides the Tooltip.

**Positioning:**

- Tooltip is absolutely positioned relative to the trigger.
- Maintain `8px` gap between the trigger and the Tooltip body (arrow fills this gap).
- If the Tooltip would overflow the viewport, flip the direction (top ↔ bottom, left ↔ right).
- If flipping is not enough, offset the arrow and shift the Tooltip horizontally/vertically.

### Accessibility

- Default Tooltip: use `role="tooltip"` on the Tooltip body.
- Trigger element must have `aria-describedby` pointing to the Tooltip id.
- Coach Mark: use `role="dialog"` and `aria-modal="false"` (non-blocking).
- Do not trap focus in a default Tooltip.
- Coach Mark with action: the action button must be focusable and keyboard accessible.
- Respect `prefers-reduced-motion`: skip scale transition, use instant `opacity` change.

### Tooltip vs Toast / Modal

| | Tooltip | Toast | Modal |
|--|---------|-------|-------|
| **Trigger** | Hover/focus on element | System event | User action or system event |
| **Position** | Relative to trigger | Fixed top-center | Fixed center |
| **Duration** | Until mouse leaves | 3–5s auto-dismiss | Until closed |
| **Content** | 1–2 lines of text | Icon + text + optional action | Complex forms, detail |
| **Interactions** | None (default) | Optional action | Full interaction |

### Code Guidance

```ts
type TooltipDirection = "top" | "bottom" | "left" | "right";

interface TooltipProps {
  content: string;
  direction?: TooltipDirection;
}

interface CoachMarkProps {
  title: string;
  titleIcon?: string;
  description: string;
  step?: { current: number; total: number };
  action?: {
    label: string;
    onClick: () => void;
  };
  direction?: "top" | "bottom";
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Tooltip must be rendered via Portal to avoid being clipped by parent `overflow: hidden`.
- **Do not add a shadow to Tooltip.** The dark background (`color.mask.toastPc`) provides sufficient contrast.
- Arrow must be rendered with the same background color as the Tooltip body; use CSS borders or an SVG.
- For Coach Mark, the close icon is visually hidden (`opacity: 0`). Do not render it unless the design explicitly requires dismissal.
- Use a positioning library (e.g., Floating UI) to handle viewport overflow and direction flipping.

```tsx
// Correct: Default Tooltip
<Tooltip content="新建对话" direction="top">
  <IconButton icon="AddConversationIcon" />
</Tooltip>

// Correct: Coach Mark
<CoachMark
  title="工具箱"
  titleIcon="ToolboxIcon"
  description="更多的模型能力在此体验"
  step={{ current: 1, total: 2 }}
  action={{ label: "我知道了", onClick: dismissCoachMark }}
>
  <FeatureTrigger />
</CoachMark>
```

- Tooltip owns its positioning, appearance, and show/hide logic. The caller only provides content, trigger element, and optional Coach Mark configuration.
