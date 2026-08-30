---
name: memory-widget
description: "Use when the user wants to SEE their own memory/vault as a visual widget - a dashboard, calendar, table, tag gallery, or relationship graph of the people/projects/concepts you remember about them. Triggers: '把我的记忆做成 dashboard', 'show my memory', 'visualize what you know about me', '我的记忆时间线/关系图/表格'. This is the data-class widget path: FIXED component styles, you only bind real vault data. For free-form / creative / one-off visuals that are NOT the user's memory data, use the Blueprint widget skill instead."
---

# Memory Widget

Render the user's **vault memory** as a widget — but you do **not** design the styling. You pick a
fixed component, bind real vault data to its contract, and emit it. Style is owned by the component
reference + Kimi design tokens; you only do the data wiring. This keeps every memory widget on-brand
and stops you re-inventing layout each time.

This works like `lark-base` and `kimi-design-skill`: a short menu here, detail in `references/`.

## 执行前必做 (read before you emit)

1. Read **`references/data-contract.md`** once — the exact shape of the vault data the host injects.
2. Read the **component reference** for each component you'll use (e.g. `references/calendar.md`).
   Follow its `Contract` (what data it eats) and `Fixed Style` (do not invent your own variant).
3. For styling tokens/components, the references inherit `kimi-design-skill`; read it when a
   reference tells you to. Do not invent colors, radii, spacing.

Do not emit a memory widget without having read the matching component reference.

## 数据来源 (how data reaches the widget)

The host injects the user's live vault into the widget — you never fetch or bake data:

```js
window.DaimonWidget.onVaultData(function (vault) {
  // vault.nodes:   [{ id, name, type, tags[], created, lastUpdated, content, linkCount }]
  // vault.edges:   [{ source, target }]            // entity↔entity, from body [[wikilinks]]
  // vault.about_user: { name, aliases[], facts[], topTags[] }
  render(vault);
});
```

Full field types + nuances live in `references/data-contract.md`. CSP blocks `fetch`/CDN — data only
arrives via this callback; the component runtime (`KW.*`) is pre-injected by the host.

## 组件菜单 (component menu — read the reference before using)

| 想要 | 组件 | reference | 状态 |
|---|---|---|---|
| 按时间看 entity 何时进入记忆 | **Calendar / Timeline** | `references/calendar.md` | ✅ ready |
| 全字段表格(可排序/筛选) | **Table** | `references/table.md` | ⏳ TODO |
| 按 tag 分组的卡片墙 | **Gallery** | `references/gallery.md` | ⏳ TODO |
| entity 关系网络 | **Graph** | `references/graph.md` | ⏳ TODO |
| 「关于你」画像头卡 | **Profile** | `references/profile.md` | ⏳ TODO |
| 多组件拼成 dashboard | **Layout** | `references/layout.md` | ⏳ TODO |

## 禁止行为

- 不自由写数据类 widget 的整套 CSS/布局 —— 用固定组件。
- 不自创组件变体(颜色/圆角/字体);有 reference 就照它,没有就按 kimi-design tokens 派生。
- 不 `fetch` / 不引 CDN / 不 bake 假数据。
- 数据饿死的视图(见下)不硬做。

## TODO / Deferred — 数据饿死,字段够了再补(别忘)

EDA 判定这几个视图当前 vault 数据撑不起,**先记着,等字段被 dream pipeline 填充到够用再补 reference**:

- [ ] **Board / Kanban** — 需要 `status` 分组列;现 status 仅 ~3% entity 有。触发:status 覆盖 > 30%。
- [ ] **Map** — 需要 `place`/地理字段;现 0。触发:place 字段开始被填充。
- [ ] **Number / Progress** — 需要 `number`/进度字段;现 0(entity 是定性的)。触发:出现量化字段。
- [ ] **Calendar 按真实事件日** — 现在只有 created/last_updated(记忆生成日,非事件)。触发:entity 带 `date` domain 字段(deadline/birthday)。

> 这些不是不做,是数据没到位硬做会饿死。字段一旦够,照 calendar.md 的体例补对应 reference 即可。
