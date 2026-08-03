## Chart Colors

Based on the Kimi Design System color tokens. Chart colors are derived from existing tokens rather than invented.

### Contract

Use chart colors for data visualization: line charts, bar charts, pie charts, area charts, heatmaps, and any surface that encodes data through color. Do not use chart colors for UI state, branding, or decoration outside of data contexts.

- **Principle**: Color explains data, not decorates it. Prefer fewer colors over more.
- **Source**: All colors derive from `tokens.json`. No new colors are invented.
- **Maximum series**: 5 categorical colors for standard charts; use shape/line-style variation beyond 5.

### Categorical Colors

For distinguishing different data series. Selected for maximum hue distance and colorblind safety.

| Order | Token path | Hex (light) | Usage |
|-------|-----------|-------------|-------|
| 1 | `color.status.kimiBlue` | `#1783ff` | Primary series |
| 2 | `color.status.danger` | `#ff3849` | Contrast series / negative metric |
| 3 | `color.syntax.functions` | `#7EB233` | Diverging-positive / growth |
| 4 | `color.syntax.string` | `#A44185` | Diverging-negative / anomaly |
| 5 | `color.labels.quaternary` | `#b2b2b2` | Neutral / fallback / disabled series |

Rules:

- Do not use `color.status.positiveGreen` alongside `color.status.danger`; they are hard to distinguish under deuteranopia.
- Do not use `color.status.orange` or `color.status.yellow` for small elements; their contrast against white is too low.
- Do not use `color.syntax.keyword` or `color.syntax.numbers` alongside `color.status.kimiBlue`; they are too close in hue.

### Sequential Scales

For showing magnitude or intensity (low → high). Two symmetric scales derived from `kimiBlue` and `danger` using the same opacity-mixing logic. The lightest steps have been increased from 15%/30% to 25%/40% to ensure visibility on both light and dark backgrounds.

**Blue scale** (from `color.status.kimiBlue`):

| Step | Opacity blend | Hex (light) | Hex (dark) | Token derivation |
|------|--------------|-------------|------------|-----------------|
| 1 | 25% | `#c5e0ff` | `#1a3350` | `kimiBlue` @ 25% on background |
| 2 | 40% | `#a2cdff` | `#1a4673` | `kimiBlue` @ 40% on background |
| 3 | 50% | `#8bc1ff` | `#1a528a` | `kimiBlue` @ 50% on background |
| 4 | 70% | `#5ca8ff` | `#1a6db8` | `kimiBlue` @ 70% on background |
| 5 | 100% | `#1783ff` | `#1a88ff` | `color.status.kimiBlue` |

**Red scale** (from `color.status.danger`):

| Step | Opacity blend | Hex (light) | Hex (dark) | Token derivation |
|------|--------------|-------------|------------|-----------------|
| 1 | 25% | `#ffcdd2` | `#50272b` | `danger` @ 25% on background |
| 2 | 40% | `#ffafb6` | `#732e34` | `danger` @ 40% on background |
| 3 | 50% | `#ff9ba4` | `#8a323a` | `danger` @ 50% on background |
| 4 | 70% | `#ff737f` | `#b83a46` | `danger` @ 70% on background |
| 5 | 100% | `#ff3849` | `#ff4756` | `color.status.danger` |

Rules:

- Use **Blue scale** for primary metrics, volume, density, or any "more is more" context.
- Use **Red scale** for negative metrics, risk, temperature (hot), or any "more is worse" context.
- The lightest step (25%) is now visible enough for all use cases including heatmap cells and bar fills. The 40% step provides comfortable mid-range distinction.
- In solid-filled heatmaps, ensure adjacent cells are distinguishable by border or gap. In line/area charts, the line stroke provides the boundary, so low-contrast fills are acceptable.

### Neutral

For baseline, reference line, grid, or "no data".

| Theme | Token | Hex |
|-------|-------|-----|
| Light | `color.labels.quaternary` | `#b2b2b2` |
| Dark | `color.labels.quaternary` (dark mode) | `#424242` |

### Diverging Scales

For showing deviation from a center point (negative ↔ neutral ↔ positive).

**Standard diverging** (red ↔ neutral ↔ blue):

```
#ff3849  →  #d06c75  →  #b2b2b2  →  #5ca8ff  →  #1783ff
  100%       50/50        neutral       50/50       100%
  danger     mix           quaternary    mix          kimiBlue
```

**Extended diverging** (for richer multi-color needs, using syntax colors):

```
#ff3849  →  #b2b2b2  →  #1783ff  →  #7EB233  →  #A44185
 danger     neutral       kimiBlue      functions     string
```

Rules:

- The neutral point is always `color.labels.quaternary`.
- Prefer the **standard red-blue diverging** for most financial / performance charts.
- Use **extended diverging** only when the dataset has more than three semantic zones.

### Hue-Ring Palette Order

When a single sequential scale is exhausted, transition to the next hue following the hue-ring (color wheel) order. This ensures natural visual progression rather than jarring jumps to high-contrast colors.

**Hue-ring order** (clockwise from Blue):

```
kimiBlue (210°) → string (323°) → danger (355°) → functions (85°)
       Blue           Purple          Red            Green
```

**Extended multi-series palette** (following hue-ring order, each with opacity steps):

| Series | Base hue | Opacity | Hex (light) | Hex (dark) |
|--------|---------|---------|-------------|------------|
| 1 | kimiBlue | 100% | `#1783ff` | `#1a88ff` |
| 2 | kimiBlue | 70% | `#5ca8ff` | `#1a6db8` |
| 3 | kimiBlue | 50% | `#8bc1ff` | `#1a528a` |
| 4 | string | 100% | `#A44185` | `#CE9178` |
| 5 | string | 70% | (mix) | (mix) |
| 6 | danger | 100% | `#ff3849` | `#ff4756` |
| 7 | danger | 70% | `#ff737f` | `#b83a46` |
| 8 | functions | 100% | `#7EB233` | `#DCDCAA` |

Rules:

- When the Blue scale is exhausted, move to the next hue in the ring (string → danger → functions).
- Each new hue also supports opacity steps (100%, 70%, 50%) for sub-series within that hue family.
- Beyond 8 series, use line-style variation (solid / dashed / dotted) to differentiate.
- Do not skip hues. Follow the ring order to maintain visual coherence.

### Content-Driven Color Selection

Color choice depends on the **semantic relationship between series**, not just the chart type.

| Relationship | Example | Color Strategy |
|-------------|---------|---------------|
| **Comparable dimensions** (same metric, different categories) | Revenue across regions, temperature across cities | Same-hue opacity (Blue sequential) |
| **Independent metrics** (truly different measurements) | Users vs Revenue vs Orders, Product A vs Product B vs Product C | Categorical / Hue-ring palette |
| **Positive vs baseline** | Actual vs Target, Sales vs Forecast | Blue vs Neutral gray |
| **Positive vs negative** (emotional) | Profit vs Loss, Risk vs Safety | Blue vs Red |
| **Deviation from center** | Above/below target, Over/under budget | Red ↔ Blue diverging |

**Decision flow:**

```
Are the series measuring the SAME metric type?
  ├─ Yes → Same-hue opacity (Blue sequential)
  └─ Are the series truly independent?
      ├─ Yes → Categorical / Hue-ring palette
      └─ Is there a positive/negative split?
          ├─ Emotionally charged? → Red vs Blue
          └─ Neutral comparison? → Blue vs Neutral gray
```

### Scale by Chart Type

| Chart type | Default scale | Content override |
|-----------|--------------|------------------|
| Single-series line / area / bar | Blue sequential | — |
| Pie / donut | Blue sequential | Categorical if slices are independent competitors |
| Heatmap / density | Blue sequential (or Red for "hot" metrics) | Never categorical |
| Grouped bar (comparable) | Blue sequential + opacity | Categorical if groups are independent |
| Grouped bar (positive vs baseline) | **Blue vs Neutral gray** | Red only for emotional contexts |
| Deviation from target | Red ↔ Blue diverging | — |
| Multi-series line (≤3 comparable) | Same-hue opacity | Categorical if metrics are independent |
| Multi-series line (4–5 series) | Categorical + line-style | Hue-ring order |
| Scatter (density) | Blue sequential | Categorical for 3–5 distinct groups |

**Chart-specific rules:**

- **Line charts**: Use same-hue opacity for comparable time series (e.g., revenue across regions). Use categorical / hue-ring palette when series measure independent metrics (e.g., users vs orders vs revenue). Never use categorical for single-metric trends.
- **Bar charts**: For positive-vs-baseline comparison, default to **Blue vs Neutral gray** (`kimiBlue` vs `quaternary`). Reserve `kimiBlue` vs `danger` for emotionally charged contexts (profit/loss, risk). For grouped bars with comparable metrics, use same-hue opacity.
- **Area charts**: Always use continuous scales. Never use categorical colors for stacked areas.
- **Pie / donut charts**: Prefer Blue sequential. Slices are parts of one whole; multiple colors imply unrelated categories. Only use categorical colors if the slices are semantically independent (e.g., market share by competitor).
- **Scatter plots**: Use Blue sequential for density, Red vs Blue for two opposing groups, categorical for 3–5 distinct independent groups.
- **Heatmaps**: Always use Blue sequential (or Red sequential for "hot" metrics). Never use categorical colors.

**Same-hue opacity for comparable series:**

When all series measure the same metric type (e.g., revenue across regions, temperature across cities), use same-hue opacity instead of categorical colors. It is quieter, more cohesive, and colorblind-friendly.

| Series | Color |
|--------|-------|
| 1st | `color.status.kimiBlue` 100% |
| 2nd | `color.status.kimiBlue` 70% |
| 3rd | `color.status.kimiBlue` 50% |
| 4th | `color.status.kimiBlue` 40% + dashed line |
| 5th | `color.status.kimiBlue` 25% + dotted line |

Note: The 40% and 25% steps replace the former 30% and 15% steps for better visibility on all backgrounds.

**Diverging rules:**

- **Standard diverging** (red ↔ blue): Use only when there is a true neutral midpoint (0%, break-even, target).
- **Extended diverging**: Use only when the data has more than three semantic zones AND the zones are not comparable on a single axis.
- **Do not use diverging for**: simple two-group comparisons (use Red vs Blue sequential side-by-side instead), single-metric trends (use Blue sequential).

**Color combinations to avoid:**

- Do not use `color.status.kimiBlue` alongside `color.syntax.functions` (green) in the same chart; they are hard to distinguish under deuteranopia.
- Do not use Red and Blue sequential in the same chart unless the semantic is explicitly "positive vs negative".
- Do not use `color.status.positiveGreen` alongside `color.status.danger` in the same chart; red-green colorblind users will see them as the same color.

**Quiet Utility for charts:**

- Prefer fewer colors. A chart with one hue and varying opacity is calmer than one with five different colors.
- If a chart looks "colorful," first check whether the colors are serving the data or just decorating.
- Reserve categorical colors for cases where the categories are truly independent and unordered.
- Sequential scales are the default; categorical is the exception; diverging is the last resort.

### Accessibility

- All chart colors must remain distinguishable under grayscale (print / monochrome preview).
- Do not rely on color alone to convey critical information; add labels, tooltips, or pattern overlays.
- The lightest sequential step (25%) is suitable for all fills but should be paired with a visible stroke or border for thin lines.

### Token Derivation Notes

Sequential hex values are computed as `white * (1 - opacity) + tokenColor * opacity`. They are not stored as permanent tokens because they are derived mathematically. If `tokens.json` later gains official chart color tokens, migrate to those.
