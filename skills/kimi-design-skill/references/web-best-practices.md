# Kimi Web Best Practices

This file captures page-level Kimi Web patterns. Read it after `principles.md`, `tokens.json`, `icon-system.md`, and `components-web.md` when generating or reviewing Kimi-style Web UI.

Use this file for layout, density, spacing, and interaction judgment. Component API details still belong in `components-web.md`, and visual values still come from `tokens.json`.

## Sources

- Kimi Chat 基础体验, node `555:57357`, page `首页`
- Kimi Chat 基础体验, node `6421:7553`, page `首页通知样式`
- Agent-Web, node `6981:67567`, pending: MCP could not read the node reliably; add Agent-specific rules after a smaller readable node is available.

## 1. Interaction Completeness

For any user-owned object, design the basic operation chain before polishing visuals:

- Create: where does a new object start?
- Read: where is the object listed, previewed, or opened?
- Update: how does the user rename, edit, reorder, configure, or retry?
- Delete: how does the user remove, revoke, archive, or leave?

Also define loading, empty, error, disabled, and permission-limited states. This applies to conversations, projects, files, skills, cards, list items, settings, and generated artifacts.

Do not ship an object surface that only supports the happy path.

## 2. Main Content Width

Kimi Web centers the primary task instead of filling the whole viewport.

For chat-like pages:

- Full desktop frame example: `1440px`
- Side navigation example: `240px`
- Main conversation frame: `800px`
- Inner content width: `768px`
- Main frame side inset: `16px`

Use this as a pattern, not a hard universal constant: the core task should feel focused, while side navigation and auxiliary panels stay visually secondary.

Avoid stretching input, cards, or reading content edge-to-edge on wide desktop screens.

## 3. Spacing Rhythm

Spacing should step down as hierarchy gets deeper.

Common rhythm:

- Page or major vertical section: `32px`
- Section-to-section or large content group: `20px` or `24px`
- Repeated cards or horizontal item groups: `16px`
- Container internal padding or medium groups: `12px`
- Control groups: `8px`
- Icon-to-label or badge internals: `4px`

Prefer `8px` multiples for layout spacing. Use `4px` increments only for small internal relationships such as icon-to-text gaps, badge padding, and tiny alignment corrections.

For spacing above `32px`, prefer `8px` multiples unless matching an existing Figma source.

## 4. Container Padding And Gaps

Container internals should become progressively tighter:

- If an outer container uses `24px` padding, inner groups usually use `16px` gaps.
- If an outer container uses `16px` padding, inner groups usually use `8px` or `12px` gaps.
- If a control uses `8px` vertical padding, icon/text gaps are usually `4px`.

Do not combine large padding with large internal gaps unless the screen intentionally creates an empty state or onboarding moment.

## 5. Typography And Density

Web UI mostly uses `14px` and `16px`.

Use token paths:

- Main input, prominent UI body: `typography.ui.t2` or `typography.webUI.t2Regular` (`16/24`)
- Standard labels, tabs, list text, card captions: `typography.ui.b2` or `typography.webUI.b2Regular` (`14/20`)
- Emphasized compact controls: `typography.webUI.b2Emphasized`
- Tags and small badges: `typography.ui.c1` or `typography.webUI.c1Regular` only when the element is truly auxiliary

Avoid body-level Web UI text below `14px`. Use `12px` only for small tags, badges, or low-emphasis metadata confirmed by the design system. Do not introduce arbitrary `15px` text unless the source component explicitly uses it.

## 6. Radius Rules

Use tokenized radius and relate it to component height and surface role:

- Large cards, image cards, and controls taller than `32px`: usually `radius.lg` (`12px`)
- Controls around `32px`: usually `radius.md` (`10px`)
- Small controls under `32px`: usually `radius.sm` (`8px`) or `radius.xxs` (`4px`) for badges
- Round icon buttons or pill-like tool chips may use `radius.full` only when the shape is intentionally circular or pill-shaped

Do not make every card or button fully pill-shaped. Roundness should follow component size and Kimi source patterns.

## 7. Separators And Borders

Use `color.separator.s1` for dividers, card outlines, input borders, and list separators.

Prefer visually light separators:

- Figma often uses `0.5px`
- Product code may use `1px` with token opacity when subpixel borders are not reliable

Avoid heavy black lines, high-contrast borders, or multiple nested borders unless the design source explicitly requires them.

## 8. Chat Input Pattern

The Kimi chat input is a primary action container, not a plain textarea.

Observed pattern:

- Input container width follows the inner conversation width, typically `768px`
- Input height is around `124px`
- Background: `color.background.primary`
- Border: `color.separator.s1`
- Shadow: `effect.shadow.inputDefault`
- Radius: about `20px` in the observed chat source
- Top text/input area uses `typography.ui.t2`
- Bottom toolbar uses two horizontal groups: tools on the left, model/send controls on the right
- Toolbar group gap is usually `8px`
- Icon-to-label gap is usually `4px`

The input should preserve structure across empty, focused, composing, disabled, loading, and send-disabled states. Do not let the send button, model selector, or tool chips shift the input height unexpectedly.

## 9. Chat Message Layout

Use these as starting rules for Web chat:

- Conversation container: about `800px` on full desktop
- Inner content width: about `768px`
- User message max width: `80%` of the conversation container
- At `800px` container width, user message max width is `640px`
- Gap between a user message group and a Kimi response group: `36px`
- Gap between consecutive same-speaker user messages: `8px`

Message spacing should reflect conversation structure. Do not use one uniform gap for every message if it hides speaker grouping.

## 10. Cards And Repeated Content

Cards should be light, repeatable units rather than page-level decoration.

Observed case-card pattern:

- Three-card row inside a `768px` content area
- Card media width: about `246px`
- Card media height: about `144px`
- Card media radius: `radius.lg`
- Gap between cards: `16px`
- Gap between media and caption: `8px`
- Caption: `14/20`, secondary label color, one-line ellipsis

Do not wrap repeated cards in another decorative card. Use the card itself as the framed object.

## 11. Tabs, Chips, And Tool Buttons

Tool chips and compact tabs should be consistent inside the same group:

- Icon size: usually `18px` or `20px` (see `icon-system.md` Size System)
- Icon-to-label gap: `4px`
- Horizontal padding: commonly `10px` to `12px`
- Height: commonly `28px`, `32px`, or `36px` depending on context
- Text: usually `typography.ui.b2`
- Border: `color.separator.s1`

Icon selection follows `icon-system.md`:

1. Search `references/icons/categories/navigation.json` for tab icons (e.g., `TabKimiIcon`, `TabDiscoverIcon`, `TabMeIcon`).
2. Search `references/icons/categories/general.json` or `input.json` for tool button icons (e.g., `SearchIcon`, `UploadIcon`, `SettingIcon`).
3. Use `currentColor` for all monochrome tab/chip icons.

If one item differs, it must be because of state or semantic role: selected, disabled, beta/new badge, danger, loading, or hidden overflow control.

## 12. Surface Usage

Default Kimi Web surfaces are quiet:

- Use `color.background.primary` for primary content surfaces
- Use `color.background.secondary` or grouped backgrounds for sidebars and app chrome
- Use `color.fills.f1` or `color.fills.f2` for subtle hover, chips, or inactive tool backgrounds
- Use `color.fills.f3` for stronger active or pressed affordance

Avoid decorative gradients, floating glow, glassmorphism, oversized shadows, and excessive card stacking. Shadows should communicate elevation or input focus, not decoration.

### Surface Over Stroke

Prefer **background fill** to express state, hierarchy, and selection. Do not rely on borders or strokes as the primary visual differentiator.

- Selected or active states should change the **background fill** (e.g., `color.fills.f2`, `color.background.quaternary`), not add a new border.
- Component separation should come from **spacing** and **background contrast**, not from wrapping each item in a border.
- Stroke is reserved for semantic boundaries: input box edges, dividers, and elevated-surface edges (see §13).
- When in doubt, use a fill token before introducing a stroke.

## 13. Overlay And Modal Behavior

Overlays should preserve task focus:

- Use a mask to reduce background attention
- Keep modal width constrained; do not span the whole viewport by default
- Put close/cancel/confirm behavior in predictable locations
- Preserve object CRUD and state handling inside the modal
- Loading and error states should appear in place, not as unrelated floating messages unless the action is global

The background page should remain recognizable but clearly inactive.

### Elevated Surfaces Need Edges

When a component floats above the page (uses z-index / elevation), it must have a visible edge so users can locate its boundary against complex backgrounds.

- **Menu, Dropdown, Popover, Select dropdown**: use a `0.5px` stroke with `color.separator.s1`.
- **Modal, Dialog**: do **not** add a stroke; the fullscreen mask already isolates the surface.
- **Toast, Tooltip**: do **not** add a stroke; their compact shape and strong background contrast are sufficient.
- If a new floating component is introduced and it lacks a mask, give it a `0.5px` stroke before considering alternatives.

## 14. Layering

Web z-index values are organized into fixed layers. Do not invent arbitrary z-index values; use the defined layer tokens or values from this table.

| Layer | Token / Value | Use for |
|-------|--------------|---------|
| Toast | `--z-toast: 1000` | Toast notifications (top of all UI) |
| Tooltip | `--z-tooltip: 900` | Tooltips and hover popovers |
| Dialog | `--z-dialog-backdrop: 850`, `--z-dialog: 860` | Dialog backdrop and frame |
| Modal | `--z-modal-backdrop: 800`, `--z-modal: 810` | Modal backdrop and frame |
| Header | `--z-header: 500` | Fixed header / navigation bar |

Rules:

- Only one interruptive overlay (Modal or Dialog) may be open at any moment. Do not stack them.
- If a Dialog needs to appear while a Modal is open, close the Modal first, then open the Dialog. Do not rely on z-index to place a Dialog above a Modal.
- A floating surface with a higher z-index must still have a visible edge: use `color.separator.s1` for stroke when the surface lacks a fullscreen mask.

## 15. Consistency Checks

Before considering a Web UI Kimi-like, check:

- Are same-role controls the same height, radius, typography, icon size, and padding?
- Are all spacing values from the `32 / 24 / 20 / 16 / 12 / 8 / 4` rhythm unless source evidence says otherwise?
- Are colors semantic token paths rather than new local colors?
- Are borders and separators light?
- Are card rows, lists, and tabs aligned to the same content width?
- Are long labels and long card titles handled with truncation, wrapping, or stable resizing?
- Are CRUD and state flows considered for all user-owned objects?

If a design looks unlike Kimi, first check density, spacing rhythm, surface weight, and component consistency before adding new visuals.

## 16. Anti-Patterns

Avoid:

- Marketing hero layouts for product work surfaces
- Full-width content on wide desktop when the task should be focused
- Generic card grids with large shadows and oversized rounded corners
- Arbitrary font sizes, especially below `14px` for normal Web UI
- Random gaps that do not follow the spacing rhythm
- Decorative gradients or color blocks unrelated to hierarchy or state
- Repeated controls with slightly different padding, icon size, or radius
- Heavy borders where `color.separator.s1` would work
- Components that only define the default state
