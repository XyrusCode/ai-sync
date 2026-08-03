## Segmented Control

Based on the Kimi Design System Web Segmented Control:

- Figma file: `Kimi Design System Web`
- Node: `584:22989`
- Component group: `Toggle` (Figma name)

### Contract

Use Segmented Control for selecting a single option from a compact, mutually exclusive set. Segmented Control presents options as a grouped row of button-like segments inside a unified track. It is visually denser than a Radio group and more scannable than a Dropdown.

- **Purpose**: View switching, filter modes, category tabs, format selection.
- **Options**: `2` or `3` segments. Do not exceed `3` — use Dropdown or Tabs for more options.
- **Sizes**: `sm`, `md`. Use `md` as the default.
- **States**: `default` (unselected), `selected`, `disabled` (on individual segments).
- **Content per segment**: text label (required) + optional leading icon (16px).

Do not use Segmented Control for navigation that spans pages, for multi-select, or for actions that should use a Button group or Tabs.

### Size And Dimensions

Track (container):

| Size | Width (2 segs) | Width (3 segs) | Height | Radius | Inner padding |
|------|---------------:|---------------:|-------:|--------:|-------------|
| `sm` | `108px` | `160px` | `32px` | `10px` | `2px` |
| `md` | `112px` | `164px` | `40px` | `12px` | `4px` |

Segment item:

| Size | Width | Height | Radius (selected) | Radius (unselected) | Padding X | Padding Y |
|------|------:|-------:|------------------:|--------------------:|----------:|----------:|
| `sm` | `52px` | `28px` | `8px` | `4px` | `12px` | `4px` |
| `md` | `52px` | `32px` | `8px` | `8px` | `12px` | `6px` |

Rules:

- Track uses a subtle gray background (`fills.f2`).
- All segments share the same height within a track.
- Gap between segments: `4px`.
- Each segment has a minimum width of `32px`; in the standard 2–3 segment layout they are `52px`.
- The selected segment pops out with a white (light) / dark gray (dark) background.

### Structure

```
Track (fills.f2, pill radius)
  └── Segment[] (HORIZONTAL, gap 4px)
      └── Segment Item (selected or unselected)
          ├── Leading Icon (16px, optional)
          └── Label text (b2Regular)
```

**Track:**

- Layout: horizontal flex, `items-start`.
- Background: `color.fills.f2`.
- Radius: `10px` (sm) / `12px` (md).
- Padding: `2px` (sm) / `4px` (md).

**Segment Item:**

- Layout: flex, `items-center`, `justify-center`, gap `4px`.
- Horizontal padding: `12px`.
- **Selected**:
  - Background: `color.background.quaternary` (`#ffffff` light / `#4d4d4d` dark).
  - Radius: `8px`.
  - Text: `color.labels.primary`.
- **Unselected**:
  - Background: transparent.
  - Radius: `4px` (sm) / `8px` (md).
  - Text: `color.labels.primary`.

**Leading Icon:**

- Size: `16px`.
- Color: `currentColor` (inherits from label text color).
- Optional. Most segments are text-only; use an icon only when it clarifies the option.

### Token Relationship

Use `tokens.json` for color and typography.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Track background | `color.fills.f2` | `rgba(0,0,0,0.05)` (light) |
| Selected segment bg | `color.background.quaternary` | `#ffffff` (light) / `#4d4d4d` (dark) |
| Unselected segment bg | — | transparent |
| Label text | `typography.webUI.b2Regular` | — |
| Label color (all states) | `color.labels.primary` | `rgba(0,0,0,0.9)` (light) |
| Icon | `currentColor` | — |
| Icon size | — | `16px` |

### States

**Selected:**

- Background: `color.background.quaternary`.
- Radius: `8px`.
- Text: `color.labels.primary`.
- Cursor: pointer.

**Unselected:**

- Background: transparent.
- Radius: `4px` (sm) / `8px` (md).
- Text: `color.labels.primary`.
- Cursor: pointer.

**Disabled (segment-level):**

- If a single segment is disabled, reduce its opacity to `0.4`.
- The disabled segment must not respond to click.
- Other segments remain interactive.

**Disabled (entire control):**

- Reduce the entire track opacity to `0.4`.
- No segment is interactive.

### Behavior

**Selection:**

- Clicking an unselected segment selects it and deselects the previously selected segment.
- Clicking an already selected segment does nothing (no toggle-off).
- Selection takes effect immediately.

**Keyboard navigation:**

- Use `Tab` to focus the Segmented Control container.
- Use `ArrowLeft`/`ArrowRight` to move selection between segments.
- `Space` or `Enter` activates the focused segment.
- Only one segment can be selected at a time.

### Accessibility

- Container: `role="radiogroup"` with `aria-label` describing the group purpose.
- Each segment: `role="radio"`.
- Selected segment: `aria-checked="true"`; unselected: `"false"`.
- Disabled segment: `aria-disabled="true"`.
- Ensure the selected segment has sufficient contrast against the track background.

### Code Guidance

```ts
type SegmentedControlSize = "sm" | "md";

interface SegmentedControlOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface SegmentedControlProps {
  size?: SegmentedControlSize;
  options: SegmentedControlOption[];
  value: string;
  onChange: (value: string) => void;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- Use a single `<button>` element for each segment. Do not use `<div>` with click handlers.
- The selected background should use a CSS transition (`150ms ease`) for a subtle pop effect.
- Do not animate text color between selected and unselected.
- Ensure segments have equal visual weight; do not make the selected segment taller or wider than unselected ones.

```tsx
// Correct: 2-segment view switcher
<SegmentedControl
  size="md"
  options={[
    { value: "code", label: "代码" },
    { value: "preview", label: "预览" }
  ]}
  value={activeView}
  onChange={setActiveView}
/>

// Correct: 3-segment format selector
<SegmentedControl
  size="sm"
  options={[
    { value: "classic", label: "经典" },
    { value: "modern", label: "现代" },
    { value: "sketch", label: "手绘" }
  ]}
  value={styleMode}
  onChange={setStyleMode}
/>
```

- The Segmented Control owns the selection state and keyboard navigation. Each segment button owns its own label, icon, and disabled state.

---
