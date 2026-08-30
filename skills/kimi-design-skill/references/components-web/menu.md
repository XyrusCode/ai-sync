## Menu

Based on the Kimi Design System Web Menu:

- Figma file: `Kimi Design System Web`
- Node: `54:3610`
- Component group: `Menu`

### Contract

Use Menu for contextual action lists that appear in response to a trigger (button click, right-click, or overflow control). Each item represents a single, immediate action or state toggle. Do not use Menu for navigation that belongs in a sidebar or top bar, and do not nest Menus.

- **Purpose**: Action selection, context commands, overflow actions, filter/sort toggles.
- **Composition**: `Menu` (container) + `MenuItem` (entry). Menu only renders a list of MenuItem instances.
- **MenuItem states**: `default`, `hover`, `selected`, `disabled`.
- **Content per item**: optional leading icon + label text + optional trailing check icon.
- **Width constraints**: min `140px`, max `240px`.

Do not use Menu for multi-step flows, wizard steps, or content that requires scrolling beyond a short item list.

### Structure

```
Menu Frame (radius.lg, bg tertiary)
  └── MenuItem[] (VERTICAL, no gap between items)
      └── MenuItem (HORIZONTAL, SPACE_BETWEEN, CENTER)
          ├── Lead (HORIZONTAL, icon + label, gap 4px)
          └── CheckIcon (18px, visible only when selected)
```

**Menu container:**

- Layout: vertical, no item spacing between MenuItems.
- Padding: `8px` (all sides).
- Radius: `radius.lg`.
- Background: `color.background.tertiary`.
- Border: `0.5px` `color.separator.s1`.
- Shadow: `effect.shadow.small`.
- Min width: `140px`; max width: `240px`.
- Do not stretch Menu beyond `240px`. Truncate long labels with ellipsis rather than widening the container.

**MenuItem:**

- Height: `36px`.
- Radius: `radius.md`.
- Padding: `8px` (all sides).
- Layout: horizontal, `SPACE_BETWEEN`, center-aligned.
- Internal gap: `8px` between lead group and trailing Check icon.

**Lead group:**

- Layout: horizontal, `MIN`, center-aligned.
- Icon-to-label gap: `4px`.
- Leading icon: `18px`, `currentColor`; from `icon-system.md`.
- Label: `typography.webUI.b2Regular`.
- Label color: `color.labels.primary` (default, hover, selected); `color.labels.quaternary` (disabled).

**Trailing Check icon:**

- Size: `18px`, `currentColor`.
- Visible only when MenuItem is `selected`.
- Hidden in `default`, `hover`, and `disabled` states.
- Follow `icon-system.md`; use `CheckIcon`.

### Token Relationship

Use `tokens.json` for color, typography, radius, and effects.

Menu dimensions (width, min/max width, item height, padding) are component-level values from the Figma source. Do not convert them into new spacing tokens unless the design system later defines those tokens.

| Element | Token path | Fallback value |
|---------|-----------|---------------|
| Menu background | `color.background.tertiary` | `#ffffff` (light) |
| Menu radius | `radius.lg` | `12px` |
| Menu border | `color.separator.s1` | — |
| Menu shadow | `effect.shadow.small` | — |
| Item hover background | `color.fills.f1` | `rgba(0,0,0,0.03)` (light) |
| Item radius | `radius.md` | `10px` |
| Label text | `typography.webUI.b2Regular` | — |
| Label color (active) | `color.labels.primary` | — |
| Label color (disabled) | `color.labels.quaternary` | — |
| Icon color | `color.labels.primary` | — |
| Icon size | — | `18px` |

### Variant Tokens

**MenuItem state styles:**

| State | Background | Label color | Check icon | Cursor |
|-------|-----------|-------------|------------|--------|
| `default` | transparent | `color.labels.primary` | hidden | pointer |
| `hover` | `color.fills.f1` | `color.labels.primary` | hidden | pointer |
| `selected` | transparent | `color.labels.primary` | visible | pointer |
| `disabled` | transparent | `color.labels.quaternary` | hidden | not-allowed |

Rules:

- Preserve item height (`36px`), radius (`radius.md`), and padding across all states.
- Only background fill and label color change between states.
- Disabled items must not respond to click or hover.
- Do not add additional states such as `active` or `focus-visible` unless the design system defines them.

### Behavior

- Menu opens positioned relative to its trigger (button, icon, or context area). Prefer top-left alignment below the trigger; flip to top-right if space is insufficient.
- Clicking outside the Menu closes it. Clicking a MenuItem triggers its action and closes the Menu.
- Hover state follows mouse movement; there is no persistent hover after mouse leaves.
- Only one item can be `selected` at a time within a single-select Menu. For multi-select, multiple items may show the Check icon.
- Do not keep the Menu open after an action completes unless the action explicitly requires it (e.g., a toggle that needs visual feedback).

### Accessibility

- Menu container: `role="menu"`.
- MenuItem: `role="menuitem"` (single-select) or `role="menuitemcheckbox"` (multi-select).
- Keyboard navigation: arrow keys move focus between items; Enter/Space activates; Escape closes the Menu.
- Disabled items must remain focusable via keyboard but must not be activable.
- Icon-only MenuItems are not covered by this spec; all items must have a visible label.

### Code Guidance

```ts
type MenuItemState = "default" | "hover" | "selected" | "disabled";

interface MenuItemProps {
  label: string;
  state?: MenuItemState;
  icon?: React.ReactNode;
  onClick?: () => void;
}

interface MenuProps {
  children: React.ReactNode; // composition of MenuItem instances
  minWidth?: number;
  maxWidth?: number;
}
```

Implementation notes:

- Prefer CSS variables generated from `tokens.json` mappings.
- MenuItem icon size is fixed at `18px`; do not scale arbitrarily.
- Do not hard-code Menu widths; respect `minWidth` (`140px`) and `maxWidth` (`240px`).
- Use `icon-system.md` for icon selection; use `currentColor` for all monochrome icons.

---

---

