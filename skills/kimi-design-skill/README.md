# kimi-design-skill

AI-agent Skill for generating Kimi-style Web and Mobile UI with token-first design system, component contracts, and progressive disclosure.

适用于 Claude Code / Cursor / Codex 等 Agent 环境，用于生成、修改和审阅符合 Kimi Design System 规范的 Web 与 Mobile UI。

---

## 快速安装

```bash
npx skills add https://dev.msh.team/xujianxuan/kimi-design-skill.git --skill kimi-design-skill
```

也可以直接把这段话发给有 shell 权限的 AI Agent：

> 帮我安装 kimi-design-skill。请把 `https://dev.msh.team/xujianxuan/kimi-design-skill.git` 克隆到 `~/.claude/skills/kimi-design-skill`，安装完成后检查 `SKILL.md`、`references/`、`assets/` 是否存在。

已经安装过的话，用这段话更新：

> 帮我更新 kimi-design-skill。请进入 `~/.claude/skills/kimi-design-skill` 执行 `git pull`，然后告诉我当前最新 commit。

---

## 核心能力

- 🎨 **Token-first 设计系统**：`references/tokens.json` 是颜色、字体、圆角、阴影的唯一真相源
- 📐 **9 大 Web 组件规范**：Button、Modal、Dialog、Menu、Toast、Tooltip、Radio/Checkbox、Form、Segmented Control 等，含完整状态（hover / active / disabled / loading / focus-visible）
- 📱 **Web & Mobile 双平台**：Web 遵循 `web-best-practices.md`，Mobile 遵循 `components-mobile.md`
- ⚡ **动画规范**：频率决策框架、timing/duration 表、easing 曲线、entrance/exit 模式、micro-interactions
- 🎯 **图标系统**：267 枚 outline linear 图标，1.8px stroke，语义索引 + 尺寸映射
- 📊 **图表配色**：数据可视化专用 token 集合
- 🧩 **渐进式读取**：Level A（原则 + Token）→ Level B（平台组件 + 最佳实践）→ 条件读取（动画 / 图标 / 图表）

---

## 触发关键词

装好后，Claude Code 会在对话里自动发现并调用这个 skill。触发请求包括：

- "帮我做一个 Kimi 风格的网页"
- "按 Kimi Design System 设计这个页面"
- "Review 一下这个 UI 是否符合 Kimi 规范"
- "把这段文案做成 Kimi 风格的界面"
- "生成一个符合 Kimi 设计系统的登录页"
- "优化这个按钮的 hover 和 focus 状态"
- "为 Mobile 适配这个 Web 页面"

Skill 本身是结构化工作流，Agent 会逐步引导：

1. **平台判断** — Web 还是 Mobile？默认 Web
2. **读取 Level A** — 先加载 `principles.md` + `tokens.json`
3. **读取 Level B** — Web → `components-web.md` + `web-best-practices.md`；Mobile → `components-mobile.md`
4. **条件读取** — 有动画 → `animation.md`；有图标 → `icon-system.md`；有图表 → `chart-colors.md`
5. **组件级读取** — 涉及具体组件时，读取 `references/components-web/*.md`
6. **生成/审阅** — 严格按 token 和组件契约输出，不发明任意值

---

## 目录结构

```
kimi-design-skill/
├── SKILL.md                          ← Skill 主文件：渐进读取、核心要求、源所有权
├── README.md                         ← 本文件
├── assets/
│   └── icons/                        ← 267 枚 SVG 图标（outline linear, 1.8px stroke）
├── references/
│   ├── principles.md                 ← 9 条设计原则（Quiet Utility / Token First / Semantic Hierarchy 等）
│   ├── tokens.json                   ← 设计令牌：color / typography / radius / spacing / effect
│   ├── animation.md                  ← 动画规范：频率决策、timing、easing、GPU、accessibility
│   ├── icon-system.md                ← 图标规则：风格、尺寸系统、颜色、选择流程
│   ├── components-web.md             ← Web 组件索引 + 全局规则
│   ├── components-mobile.md          ← Mobile 组件草稿索引
│   ├── web-best-practices.md         ← Web 页面级规范：布局、间距、密度、交互完整性
│   ├── components-web/
│   │   ├── button.md                 ← Button：primary/secondary/outline，size 26/32/44，完整状态
│   │   ├── modal.md                  ← Modal：small/medium/large，enter/exit 动画
│   │   ├── dialog.md                 ← Dialog：纯文本二元确认，固定 360px
│   │   ├── menu.md                   ← Menu：上下文操作列表
│   │   ├── toast.md                  ← Toast：success/error/info/loading/caution，top-center
│   │   ├── tooltip.md                ← Tooltip：default/coach-mark，四方向
│   │   ├── selection-control.md      ← Radio + Checkbox（circle + square），统一 Circle 基础
│   │   ├── segmented-control.md      ← Segmented Control：pill 分段控制器
│   │   ├── toggle.md                 ← Toggle：开关组件
│   │   ├── form.md                   ← Form：字段、区段、Radio/Checkbox 组合
│   │   ├── header.md                 ← Header：三栏布局导航栏
│   │   └── card.md                   ← Card：轻量内容容器
│   │   └── chart-colors.md           ← 图表配色：数据可视化专用色板
│   └── icons/
│       ├── manifest.json             ← 267 枚图标完整机器索引
│       ├── categories/               ← 按领域分类：general / arrows / chat / input / navigation 等 15 类
│       └── test-cases.md             ← 图标语义索引测试用例
├── chart-colors-reference.html       ← 图表配色可视化参考
└── icon-semantic-index-test.html     ← 图标语义索引测试页
```

---

## 核心原则速览

1. **Quiet Utility** — 界面应 calm、clear、product-focused，避免 ornamental 背景和 heavy effects
2. **Token First** — 所有视觉值从 `tokens.json` 取用，不硬编码
3. **Semantic Hierarchy** — 用颜色、字体、间距传达结构，避免多个 competing emphasis
4. **Platform Fit** — Web 和 Mobile 不共享布局，Web 支持 hover/denser info，Mobile 支持 touch/pressed
5. **Components Are Contracts** — 组件不只是默认状态，包含完整 size/variant/state/accessibility 契约
6. **Purposeful Motion** — 动画解释状态变化，不装饰；保持在 300ms 以内
7. **Detail Quality** — 光学对齐、间距 rhythm、focus state、empty state、overflow handling

完整原则见 `references/principles.md`。

---

## 平台兼容性

| 平台 | 状态 | 说明 |
|---|---|---|
| Claude Code | ✅ 支持 | 原生 Skill 工作流，渐进读取最完整 |
| Cursor / 本地 Agent | ✅ 支持 | 需要能读写文件并执行 shell 命令 |
| Codex | ✅ 支持 | 适合生成 UI、浏览器视觉检查 |
| 普通 Chatbot | ⚠️ 受限 | 无文件系统时无法读取 token 和组件规范 |

---

## 使用示例

复制下面任意一条给 Agent，附上你的需求或素材：

> 帮我按 Kimi Design System 做一个登录页，包含输入框、按钮和错误提示状态。

> Review 这个页面的按钮间距和字体层级，看是否符合 Kimi 规范。

> 把这份产品分析文档做成 Kimi 风格的 Web 页面，左侧导航 + 右侧内容区。

> 帮我优化这个表单的交互状态：hover、focus、error、disabled 都要按 Kimi 组件规范来。

> 为这个 Web 页面做 Mobile 适配，保持 Kimi 风格一致。

---

## Token 体系速查

```
color.brand.kimiBlue          → #1783ff
color.status.danger           → #ff3849
color.status.positiveGreen    → #16c456
color.background.primary      → #ffffff
color.background.secondary    → #f5f5f5
color.labels.primary          → rgba(0,0,0,0.9)
color.labels.secondary        → rgba(0,0,0,0.6)
color.fills.f1                → rgba(0,0,0,0.03)
color.separator.s1            → rgba(0,0,0,0.13)
radius.lg                     → 12px
radius.md                     → 10px
typography.webUI.b2Regular    → 14px / 20px / weight 400
typography.webUI.t2Emphasized → 16px / 24px / weight 500
spacing.lg                    → 16px
spacing.xl                    → 20px
spacing.3xl                   → 32px
```

完整 token 见 `references/tokens.json`。

---

## 常见问题

**Q: 我能自定义 token 颜色吗？**

A: 优先使用现有 token。如果确实缺失，记录 token gap，不要自己发明永久 token。

**Q: Web 和 Mobile 组件规范冲突时怎么办？**

A: 用 `web-best-practices.md` 或 `components-mobile.md` 选择组件和变体，再用组件 spec 实现它。Platform Fit 原则优先。

**Q: 没有匹配的组件文件时怎么办？**

A: 从 `tokens.json` 和 `principles.md` 推导新组件，遵循平台最佳实践。不发明任意颜色、圆角或间距。

**Q: 怎么更新到最新版？**

A: 重新运行安装命令，或在本地 skill 目录执行 `git pull`。

---

## 贡献指南

Bug、规范补充、新组件需求——欢迎提 Issue 或 PR。改动请优先：

- 新增组件时，在 `references/components-web/*.md` 中按现有结构编写完整 spec
- 新增 token 时，同步更新 `references/tokens.json`
- 新增图标时，同步更新 `references/icons/manifest.json` 和对应 `categories/*.json`
- 踩过的坑写到 `references/principles.md` 或对应组件文件的注意事项中

---

## License

MIT © 2026 xujianxuan
