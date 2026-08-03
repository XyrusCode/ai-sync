# Mode: Explainer / data videos

Explain a concept, teach a topic, or animate data — driven by subject matter
rather than a brand. Same Remotion foundation; the scenes carry information
instead of hype.

## Structure

Think in beats, one idea per scene, narration-paced (~3–6s each):

1. **Hook** — the question or problem ("Why is X slow?").
2. **Setup** — the context/definition, one line at a time.
3. **Body** — the mechanism, built up progressively (steps, a diagram
   assembling, a chart growing).
4. **Payoff** — the takeaway/answer, emphasized.
5. **Outro** — recap or source/CTA.

Keep on-screen text short — headlines and labels, not paragraphs. If there's a
script/voiceover, the visuals punctuate it; time scenes to the narration.

## Kinetic typography

The workhorse of explainers. Reveal words with intent:
- **Word-by-word** — map each word to a start frame; `spring` it up + fade in.
- **Emphasis** — scale/color a key word on its beat; dim the rest.
- **Line replace** — old line springs out as the new one springs in (reuse the
  `Flash` or a slide).
Drive all of it with `useCurrentFrame()` + `spring`/`interpolate`.

## Charts & data (drawn, animated)

Draw charts as SVG and animate them in — no charting lib needed for simple ones:
- **Bar chart** — one `<rect>` per datum; animate `height` (and `y`) via
  `interpolate(frame, [start, start+grow], [0, value*scale])`, staggering
  `start` per bar. Add value labels that fade in as each bar finishes.
- **Line chart** — build the `points`/path, then reveal with
  `strokeDasharray`/`strokeDashoffset` animated from full-length to 0 (a
  "drawing" effect). A dot rides the path head.
- **Counter** — a number counting up: `Math.round(interpolate(frame, […], [0, target]))`.
- **Progress ring/donut** — an SVG circle with animated `strokeDashoffset`.

Keep data in a small array/JSON at the top of the scene so it's easy to swap.
For heavier/interactive charts, a library (e.g. visx/d3 scales) can compute
geometry while Remotion drives the reveal — but start simple.

Color meaning consistently (one hue per series); label axes; don't animate so
fast the viewer can't read values.

## Diagrams

Assemble a diagram piece by piece: nodes spring in, then connectors draw
(dash-offset), then labels fade. Revealing structure in the order you'd explain
it is what makes a diagram feel taught rather than shown.
