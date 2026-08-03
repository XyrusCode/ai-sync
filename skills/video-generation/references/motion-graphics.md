# Mode: Motion graphics (brand / product promos)

For brand promos, adverts, logo intros, kinetic-typography spots. The template
is already this shape — start there and re-skin.

## The recipe

1. **Palette first.** In `src/theme.ts`, set `COLORS` to the brand's real hex
   values (or a mood-appropriate set). Pick one dark `bg` + 2–3 vivid accents.
   The accents drive every glow, stripe, and highlight downstream.
2. **Fonts.** Heavy display face for headlines, light face for support copy.
   For a brand font, load via `@remotion/google-fonts` or a local file.
3. **Scene arc** — the classic 3-beat promo, already in the template:
   - **Title** (`TitleScene`): logo/name builds in; particles converge; a
     gradient underline wipes; kicker/tagline fades up.
   - **Content** (`ContentScene`): 2–4 feature callouts slide in staggered,
     each with its own accent dot + outlined pill.
   - **Outro** (`OutroScene`): logo burst with an expanding ring, tagline,
     shimmering call-to-action pill, URL.
4. **Pacing.** 12–20s reads as a promo. Tune scene end-frames in `config.ts`.

## Animation building blocks (already used in the template)

- **`spring({frame, fps, config})`** — organic entrances. Lower `damping` =
  more bounce; higher `stiffness` = snappier. Offset `frame - delay` to stagger.
- **`interpolate(frame, [inA, inB], [outA, outB], {extrapolateLeft/Right:'clamp'})`**
  — linear maps for opacity, position, width. Always clamp to avoid overshoot.
- **`random('seed')`** — deterministic 0–1 for particle positions/sizes. Vary
  the seed string per element; never `Math.random()`.
- **`AbsoluteFill`** — full-frame layer; stack them for background → content →
  flash overlays.
- **Glow** — `boxShadow`/`textShadow` with an accent color at large blur; a
  faint radial-gradient behind the subject sells depth.
- **Sheen/shimmer** — a skewed white gradient bar whose `left` is an
  `interpolate` of `frame % period`, clipped to the element (see `OutroScene`).

## Ideas to push further (see the Stylex worked example)

The `stylex-promo` project has richer, hand-tuned versions worth copying:
- **Liquid waves** — sine-based SVG `path` filled with a gradient, phase driven
  by `frame`, with floating bubble divs (`LiquidScene.tsx`).
- **A drawn product** — an SVG "can"/bottle with clipped brand stripes and a
  moving sheen (`FeatureScene.tsx`), bobbing via `Math.sin(frame/…)`.
- **Rotating accent rings** and per-letter logo slams (`IntroScene.tsx`).

## Taste

- Restraint reads as premium: a few elements moving well beats many moving at
  once. Give each beat a moment to land.
- Keep motion continuous — something always easing — but avoid everything
  animating on the same frame.
- Contrast: bold headline weight against thin, wide-tracked support copy.
