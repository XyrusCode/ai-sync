# Kimi Design Principles

These principles define the highest-priority design decisions for Kimi UI generation and review. They should guide judgment before component-specific rules are loaded.

## 1. Quiet Utility

Kimi interfaces should feel calm, clear, and product-focused. Prioritize task completion, readability, hierarchy, and trust over visual decoration.

Quiet does not mean empty, weak, or unfinished. It means every element earns its place: controls are discoverable, information is scannable, and the screen avoids ornamental backgrounds, heavy effects, marketing-style composition, and unnecessary card stacking.

## 2. Token First

Use `tokens.json` for color, typography, radius, effects, and other reusable visual values.

Prefer semantic token paths over raw values. Do not hard-code visual values unless no token exists. If a token is missing, use the closest existing semantic token only if the intent is clear. Otherwise record the gap instead of inventing a permanent token or silently substituting a nearby value.

**Principles take precedence over tokens.** When a token value contradicts a principle (e.g., a color fails contrast under Quiet Utility, or a typography size breaks Platform Fit), follow the principle and record the token gap. Tokens are the implementation layer; principles are the decision layer.

**Priority**: `principles.md` guides intent and judgment; `tokens.json` provides the exact values. When a principle and a token appear to conflict, follow the principle and record the token gap. Both are mandatory reads.

## 3. Semantic Hierarchy

Each screen should make the primary task obvious within a quick scan. Secondary actions should be visually quieter than primary actions, and destructive actions should use clearly differentiated semantic treatment.

Use color, typography, spacing, and component emphasis to communicate structure and intent. Avoid multiple competing emphasis points in one local area. Color should explain hierarchy, state, or meaning; it should not fill space decoratively.

## 4. Typography For Reading And UI

Typography should create a stable reading order, not a new visual personality.

Use UI typography tokens for controls, navigation, labels, lists, and dense product surfaces. Use Markdown or reading typography tokens for long-form generated content, article-like responses, code blocks, and structured reading areas.

- **Web UI**: use `typography.webUI.*` tokens.
- **Mobile UI**: use `typography.ui.*` tokens.

Do not introduce new fonts, arbitrary sizes, negative letter spacing, or viewport-scaled type. If a required text role is missing, record the gap and map it only after the design system source is confirmed.

## 5. Platform Fit

Web and Mobile should not share layouts mechanically.

Web can support denser information, hover states, table-like structures, compact controls, keyboard focus, and side-by-side comparison. Mobile should prioritize touch targets, vertical flow, thumb-friendly placement, pressed states, and bottom-aligned actions when appropriate.

Adapt the interaction model as well as the layout. A web hover affordance usually needs a mobile pressed, expanded, or explicit-control equivalent.

## 6. Components Are Contracts

A component is not only its default state. It is the full contract of sizes, variants, content rules, interaction states, accessibility, and platform behavior.

Tokens provide `default`, `hover`, and `active` states. For states beyond these three, derive from semantic token mappings rather than inventing new colors:

- `disabled`: use `color.labels.quaternary` or `color.fills.f1`
- `loading`: reuse the default state with a loading spinner overlay
- `error`: use `color.status.danger`
- `focus-visible` (Web): use `color.status.kimiBlue`

For Web, define default, hover, active, and the derived states above where applicable. For Mobile, define default, pressed, disabled, loading, and error where applicable.

Components should handle realistic content: long labels, empty values, loading text, dynamic counts, icons, and disabled affordances must not resize or break the layout unexpectedly.

## 7. Purposeful Motion

Motion should explain state changes, confirm feedback, preserve spatial continuity, or reduce perceived waiting. Avoid animation that only decorates.

Keep motion restrained and product-like. Prefer short, responsive transitions for controls and clear enter/exit behavior for overlays or expanding surfaces. Respect reduced-motion preferences where the target platform supports them.

When implementing animation, follow `references/animation.md` for timing, easing, performance, and accessibility rules. Do not invent arbitrary durations or curves when the animation reference already defines them.

## 8. Elevation And Layering

Only one interruptive overlay (Modal or Dialog) may be open at any moment. Do not stack Modals, Dialogs, or a Dialog over a Modal. If a confirmation needs to appear while a Modal is open, close the Modal first, then open the Dialog.

Web uses `z-index` for stacking; Mobile uses view hierarchy (`UIView`/`ZStack` ordering). Define layer values per platform:

- Web: see `references/web-best-practices.md` §Layering for z-index values.
- Mobile: see `references/components-mobile.md` for view hierarchy rules.

## 9. Code Highlighting

Code syntax highlighting uses `tokens.json` `color.syntax.*` colors. These colors serve semantic distinction, not visual decoration. Do not introduce new syntax colors outside the defined set.

Defined semantic categories (see `tokens.json` for exact values):

| Semantic category | Token path |
|-------------------|-----------|
| Reserved keywords | `color.syntax.keyword` |
| Strings | `color.syntax.string` |
| Comments | `color.syntax.comment` |
| Functions | `color.syntax.functions` |
| Variables | `color.syntax.variables` |
| Numbers | `color.syntax.numbers` |
| Operators | `color.syntax.operators` |
| Search/mark highlights | `color.syntax.mark` |

Use `typography.markdown.codeblocks` for code block text and `typography.markdown.inlineCode` for inline code.

## 10. Progressive Extraction

Extract stable patterns, not hypothetical completeness.

The skill should grow through progressive disclosure: keep `SKILL.md` lightweight, always load the principles and tokens, then load only the platform or component references needed for the task.

Document reusable patterns when they are confirmed by the design system or repeated across real components. Do not over-abstract one-off designs, and do not let component docs override `tokens.json` as the source of truth.

## 11. Detail Quality

Most quality comes from details users do not consciously notice: optical alignment, spacing rhythm, text wrapping, focus states, empty states, loading states, disabled states, and resilient overflow handling.

Before treating a design as complete, check whether the interface still feels correct with real content, edge cases, and platform-specific interaction states. Completeness without coherence is not good enough for Kimi.
