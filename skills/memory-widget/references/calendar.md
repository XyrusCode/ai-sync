# Calendar / Timeline

Show entities over time — *when each entity entered the user's memory*. Good for "本月我都记了
些什么 / 这条记忆多久了 / 最近在忙什么"。

> **Honesty rule:** the only dates the vault has are `created` / `lastUpdated` — these are
> **memory-creation dates (pipeline metadata), not real-world events.** Label the widget
> 「记忆时间线」, never 「日程 / 日历安排」. Don't imply these are appointments.

## Contract

Bind vault data into `items`. You only map fields — you don't style.

```ts
KW.calendar(mount, {
  mode: 'timeline' | 'month',          // default 'timeline' (data is metadata, not events)
  items: Array<{
    date:   string,                    // 'YYYY-MM-DD'  ← entity.created (or .lastUpdated)
    title:  string,                    // ← entity.name
    color?: string,                    // ← entity.type  (component maps type→token color)
    id?:    string,                    // ← entity.id    (for click→detail)
  }>,
  todayMarker?: boolean,               // default true
  onItemClick?: (id) => void,          // optional; default opens entity detail
})
```

- `date` + `title` required; everything else optional.
- Default to `mode:'timeline'`. Use `mode:'month'` only if the user explicitly asks for a month grid.
- Do not pass styling, widths, or colors-as-hex — `color` is a **type key**, the component owns the palette.

## Fixed Style (follow exactly — do not invent)

Inherits `kimi-design-skill` (read its `references/principles.md` + `tokens.json`). The component
renders; you never write this CSS — it's here so you know what you're getting and don't fight it.

- **Type→color** uses the shared memory palette (person `kimiBlue`, product `positiveGreen`,
  project `orange`, org/tool `purple`, benchmark `yellow`, concept `label-tertiary`). Same map across
  all memory components — never recolor per-widget.
- **Timeline mode**: vertical rail on the left (`separator.s1`), each item = `radius.full` type-dot +
  title (`labels.primary`) + relative date (`labels.tertiary`, tabular-nums). Group by month with a
  sticky month header (`labels.secondary`, serif optional). Today = `accent` dot + hairline.
- **Month mode**: 7-col grid, `radius.md` cells, weekday header in `labels.tertiary`. A day with
  entities shows up to 3 type-dots + "+N"; today cell ring = `accent`. Empty days stay quiet (no fill).
- Spacing from `spacing` tokens (rail gap `md`, item pad `sm`). Font `PingFang SC`. Honors light/dark
  via tokens automatically.
- Density cap: if `items > 120`, timeline groups by month-collapsed; month mode paginates by month.
  Never render a wall of hundreds of rows.

## Usage (the minimal code you write)

The host pre-injects `KW` (the component runtime) and the vault. Your whole job:

```html
<div id="root"></div>
<script>
window.DaimonWidget.onVaultData(function (vault) {
  KW.calendar('#root', {
    mode: 'timeline',
    items: vault.nodes.map(function (n) {
      return { date: n.created, title: n.name, color: n.type, id: n.id };
    }),
    todayMarker: true,
  });
});
</script>
```

That's it — one map + one call. No `<style>`, no layout, no colors. If the user wants a different
slice (e.g. only people, sorted by recency), filter/sort inside `.map`'s source array — still no
styling.

> Reuse note: this same `items` contract feeds the dashboard `layout.md` slot, so a Calendar can sit
> inside a multi-component memory dashboard without changes.
