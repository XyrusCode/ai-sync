# Kimi Animation & Interaction

This file defines animation rules for Kimi-style Web and Mobile UI. Read it when the task involves transitions, state changes, entrance/exit effects, or any component-level motion.

## 1. Decision Framework

### 1.1 Frequency-Based Decision

| Frequency | Decision |
|-----------|----------|
| 100+ times/day (keyboard shortcuts, command palette) | **No animation. Ever.** |
| Tens of times/day (hover, list nav) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare/first-time (onboarding, empty states) | Can add subtle delight |

> Raycast has no open/close animation. That is optimal for something used hundreds of times daily.

### 1.2 Purpose Checklist

Every animation must answer **"why does this animate?"**

- **Spatial consistency**: toast enters/exits same direction → swipe-to-dismiss intuitive
- **State indication**: morphing feedback button shows state change
- **Explanation**: marketing animation showing how a feature works
- **Feedback**: button scales down on press → confirms input received
- **Prevent jarring changes**: elements appearing without transition feel broken

If the purpose is just "it looks cool" and users see it often → **do not animate**.

## 2. Timing & Duration

### 2.1 Duration by Component Type

| Element | Duration | Notes |
|---------|---------:|-------|
| Button press feedback | `100–160ms` | Quick scale or color shift |
| Tooltip, small popover | `125–200ms` | |
| Dropdown, Menu | `150–250ms` | |
| Modal, Dialog | `150–200ms` | Kimi default |
| Drawer, side panel | `250–400ms` | |
| Toast enter/exit | `300–400ms` | |
| Page entrance | `300–600ms` | |
| Stagger between items | `30–100ms` | Keep short; never block interaction |

**Rule**: UI animations stay **under 300ms** unless the element is large (drawer, full-screen transition).

### 2.2 Perceived Performance

Speed in animation is not just about feeling snappy — it directly affects how users perceive your app's performance:

- A **fast-spinning spinner** makes loading feel faster (same load time, different perception)
- A **180ms select** animation feels more responsive than a **400ms** one
- **Instant tooltips** after the first one is open (skip delay + skip animation) make the whole toolbar feel faster

The perception of speed matters as much as actual speed. Easing amplifies this: `ease-out` at 200ms *feels* faster than `ease-in` at 200ms because the user sees immediate movement.

### 2.3 Enter vs Exit

- **Exit is faster than enter** (~75% of enter duration)
- Asymmetric timing: press can be slow (deliberate), release must be snappy

```css
/* Release: fast */
.overlay { transition: clip-path 200ms ease-out; }

/* Press: slow & deliberate */
.button:active .overlay { transition: clip-path 2s linear; }
```

### 2.4 Stagger

- Delay between items: **30–100ms** (keep it short, long delays feel slow)
- Never block interaction while stagger plays

```css
.item { animation: fadeIn 300ms ease-out forwards; }
.item:nth-child(1) { animation-delay: 0ms; }
.item:nth-child(2) { animation-delay: 50ms; }
.item:nth-child(3) { animation-delay: 100ms; }
```

## 3. Easing

### 3.1 Decision Tree

```
Is the element entering or exiting the viewport?
  Yes → ease-out (starts fast, feels responsive)
  No →
    Is it moving/morphing on screen (drag, reorder)?
      Yes → ease-in-out (natural acceleration/deceleration)
    Is it a hover or color change?
      Yes → ease
    Is it constant motion (marquee, progress)?
      Yes → linear
    Default → ease-out
```

### 3.2 Recommended Curves

| Name | Curve | Use for |
|------|-------|---------|
| `ease-out` | `cubic-bezier(0.23, 1, 0.32, 1)` | Entering/exiting elements |
| `ease-in-out` | `cubic-bezier(0.77, 0, 0.175, 1)` | Movement on screen |
| `ease-drawer` | `cubic-bezier(0.32, 0.72, 0, 1)` | Drawer/side panel |

**Critical: use custom easing curves.** Built-in CSS easings are too weak. They lack the punch that makes animations feel intentional.

### 3.3 Forbidden

| Never use | Why |
|-----------|-----|
| `ease-in` on UI | Starts slow → feels sluggish |
| `bounce` / `elastic` | Dated; draws attention to animation itself |
| `ease-in-out` for enter/exit | Both directions slow → unresponsive |

> Resources: [easing.dev](https://easing.dev/), [easings.co](https://easings.co/)

## 4. Patterns

### 4.1 Entrance

- Start from `opacity: 0` + `scale(0.95–0.97)`, **never `scale(0)`**
- Backdrop fades in simultaneously with content
- Stagger children with `30–100ms` delay

```css
/* Bad */
.entering { transform: scale(0); }

/* Good */
.entering { transform: scale(0.95); opacity: 0; }
```

### 4.2 Exit

- Reverse the entrance: fade + slight scale/shrink
- Backdrop fades out slightly after content starts exiting
- Duration: ~75% of enter duration

### 4.3 Micro-interactions

| Context | Pattern | Duration |
|---------|---------|---------:|
| Button press | `transform: scale(0.96–0.97)` | `100–160ms` |
| Button hover lift | `transform: scale(1.02)` | `150ms` |
| Icon switch | cross-fade `opacity` + `scale(0.8→1)` | `150–200ms` |
| Toggle/check | translate + color transition | `200ms` |

> `0.96` is the sweet spot for press. Never below `0.95` — it feels exaggerated.

### 4.4 Popover / Menu

- Scale from trigger origin, not center
- Duration: `150–200ms`, ease-out
- Modals are the exception — they scale from center

```css
.popover { transform-origin: var(--popover-content-transform-origin); }
```

### 4.5 Modal / Dialog

- Content: `opacity: 0` + `scale(0.96)` → `opacity: 1` + `scale(1)`
- Backdrop: `opacity: 0` → `opacity: 1`
- Duration: `150–200ms`

### 4.6 Tooltip

- Delay before appearing to prevent accidental activation
- Once one tooltip is open, subsequent ones should open instantly with no animation
- Duration: `125ms`, ease-out

```css
.tooltip {
  transition: transform 125ms ease-out, opacity 125ms ease-out;
  transform-origin: var(--transform-origin);
}
.tooltip[data-starting-style],
.tooltip[data-ending-style] {
  opacity: 0;
  transform: scale(0.97);
}
/* Skip animation on subsequent tooltips */
.tooltip[data-instant] { transition-duration: 0ms; }
```

## 5. Spring Animations

Springs feel more natural than duration-based animations because they simulate real physics.

### 5.1 When to Use

- Drag interactions with momentum
- Elements that should feel "alive" (like Apple's Dynamic Island)
- Gestures that can be interrupted mid-animation
- Decorative mouse-tracking interactions

### 5.2 Configuration

**Recommended approach (easier to reason about):**

```js
{ type: "spring", duration: 0.5, bounce: 0.2 }
```

**Traditional physics (more control):**

```js
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }
```

Keep bounce subtle (0.1–0.3). Avoid bounce in most UI contexts.

### 5.3 Interruptibility

Springs maintain velocity when interrupted. CSS keyframes restart from zero. This makes springs ideal for gestures users might change mid-motion.

## 6. Technical Implementation

### 6.1 CSS vs JS

| Technique | Use For |
|-----------|---------|
| CSS transitions | Simple state changes, hover, toggle |
| CSS @keyframes | Complex sequences that run once |
| Web Animations API | Programmatic control + CSS performance |
| JS libraries (Motion, GSAP) | Complex interactive, gestures |

**Rule**: CSS animations run off main thread — they stay smooth when JS is busy.

### 6.2 GPU Acceleration

```css
/* ✅ GPU-accelerated */
.animated { transform: translateX(100px); opacity: 0.5; }

/* ❌ CPU-bound (triggers layout + paint) */
.animated { left: 100px; width: 300px; }
```

**Only animate**: `transform`, `opacity`, `filter` (GPU compositable).

### 6.3 `will-change`

- Only for `transform`, `opacity`, `filter`
- Add sparingly when you notice first-frame stutter
- Never `will-change: all`
- Remove after animation completes if possible

### 6.4 Transition Specificity

```css
/* ❌ Bad */
transition: all 300ms;

/* ✅ Good */
transition: transform 200ms ease-out, opacity 200ms ease-out;
```

### 6.5 `@starting-style` for Enter Animations

Modern CSS way to animate entry without JS:

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 400ms ease, transform 400ms ease;

  @starting-style {
    opacity: 0;
    transform: translateY(100%);
  }
}
```

### 6.6 Skip Animation on Page Load

```jsx
// Motion library
<AnimatePresence initial={false}>
```

## 7. Performance

### 7.1 Golden Rules

- **Only animate `transform` and `opacity`**
- **Target 60fps** (16ms per frame)
- **Batch DOM reads, then writes** (avoid layout thrashing)
- **Use CSS containment** for independent regions
- **Minimize DOM depth and size**

### 7.2 Layout Thrashing

```javascript
// ❌ Bad: alternating reads and writes
elements.forEach(el => {
  const height = el.offsetHeight; // Read (forces layout)
  el.style.height = height * 2;   // Write
});

// ✅ Good: batch reads, then batch writes
const heights = elements.map(el => el.offsetHeight); // All reads
elements.forEach((el, i) => {
  el.style.height = heights[i] * 2; // All writes
});
```

### 7.3 CSS Variables & Children

Changing a CSS variable on a parent recalculates all children. Update `transform` directly on the element instead.

```javascript
// Bad: triggers recalc on all children
element.style.setProperty('--swipe-amount', `${distance}px`);

// Good: only affects this element
element.style.transform = `translateY(${distance}px)`;
```

## 8. Gestures & Drag

### 8.1 Momentum-Based Dismissal

Don't require dragging past a threshold. Calculate velocity:

```js
const timeTaken = Date.now() - dragStartTime;
const velocity = Math.abs(dragDistance) / timeTaken;

if (Math.abs(dragDistance) >= SWIPE_THRESHOLD || velocity > 0.11) {
  dismiss();
}
```

### 8.2 Damping at Boundaries

When dragging past natural boundary, apply damping (the more they drag, the less it moves).

### 8.3 Pointer Capture

Once dragging starts, capture all pointer events to continue even if pointer leaves element bounds.

### 8.4 Multi-Touch Protection

Ignore additional touch points after initial drag begins to prevent jumps.

## 9. Accessibility

### 9.1 `prefers-reduced-motion`

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Reduced motion means **fewer and gentler** animations, not zero. Keep opacity and color transitions that aid comprehension.

### 9.2 Touch Device Hover

```css
@media (hover: hover) and (pointer: fine) {
  .element:hover { transform: scale(1.05); }
}
```

Touch devices trigger hover on tap, causing false positives.

## 10. Review Format

When reviewing animation code, use a markdown table with Before/After/Why columns:

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | Specify exact properties; avoid `all` |
| `transform: scale(0)` | `transform: scale(0.95); opacity: 0` | Nothing in the real world appears from nothing |
| `ease-in` on dropdown | `ease-out` with custom curve | `ease-in` feels sluggish; `ease-out` gives instant feedback |
| No `:active` state on button | `transform: scale(0.97)` on `:active` | Buttons must feel responsive to press |
| `transform-origin: center` on popover | `transform-origin: var(--popover-content-transform-origin)` | Popovers should scale from their trigger (not modals — modals stay centered) |

## 11. Philosophy

- **Motion explains, it does not decorate.** Every animation must serve a purpose: state change, feedback, spatial continuity, or waiting reduction. If the purpose is only "it looks cool" and users encounter it often, remove it.
- **Unseen details compound.** Users rarely notice individual timing choices, but they feel the overall coherence. Consistent easing and duration across the product build trust.
- **Restraint over delight.** Product UI is not a showcase for animation technique. Short, responsive transitions feel more polished than elaborate sequences.
- **Cohesion matters.** Easing, duration, and style should match the component's personality and the product's vibe. A calm product does not need bouncy springs.
- **Review with fresh eyes.** Check animations the next day. Play in slow motion to spot timing issues. Taste is trained, not innate.

## 12. Quick Reference

### Duration Cheat Sheet

| Purpose | Duration |
|---------|---------:|
| Button press | `100–160ms` |
| Tooltip / popover | `125–200ms` |
| Dropdown / Menu | `150–250ms` |
| Modal / Dialog | `150–200ms` |
| Drawer | `250–400ms` |
| Stagger delay | `30–100ms` |

### Easing Cheat Sheet

| Scenario | Easing |
|----------|--------|
| Enter / exit | `ease-out` / `cubic-bezier(0.23, 1, 0.32, 1)` |
| On-screen movement | `ease-in-out` / `cubic-bezier(0.77, 0, 0.175, 1)` |
| Hover / color | `ease` |
| Drawer | `cubic-bezier(0.32, 0.72, 0, 1)` |

### Scale Values

| Context | Scale |
|---------|------:|
| Press feedback | `0.96–0.97` |
| Hover lift | `1.02` |
| Entry start | `0.95–0.97` |
| Exit end | `0.97` with fade |
