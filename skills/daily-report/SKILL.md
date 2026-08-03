---
name: daily-report
description: Generate a professional daily intelligence brief PDF covering global geopolitics, macro policy, industrial supply chains, and tech trends. Use when user needs a comprehensive daily report similar to institutional research formats.
dependencies: []
---

# Daily Intelligence Brief Generator

Generate a professional daily report analyzing global events, macro trends, industrial developments, and policy shifts.

## Workflow

### Step 0: User Preference Discovery

Ask user if they have specific focus areas before generating:

> "将为您生成通用版日报（覆盖全球政经、产业、科技）。如需定制，请告诉我关注的领域（如科技/消费/文化等）。"

| 偏好类型 | 示例 | 处理方式 |
|----------|------|----------|
| 无偏好（默认） | - | 通用5领域模板 |
| 科技产业 | 半导体、AI、新能源 | 产业章节深入展开 |
| 宏观政经 | 中美、关税、货币政策 | 前置为"今日主线"深度分析 |
| 消费生活 | 品牌动态、零售、美食、旅行 | 增加消费趋势板块 |
| 文化娱乐 | 影视、音乐、艺术、出版 | 替换默认模板中的产业部分 |

### Step 1: Intelligence Gathering

Search for today's critical developments across these domains:

**A. Geopolitics & Security**
- Military conflicts, territorial disputes, sanctions
- Diplomatic breakthroughs or breakdowns
- Supply chain disruptions (shipping routes, key chokepoints)

**B. China Macro & Policy**
- National People's Congress, policy meetings
- GDP targets, fiscal/monetary policy signals
- Regulatory changes affecting key sectors

**C. Global Monetary Policy**
- Central bank decisions (Fed, ECB, BOJ, PBOC)
- Inflation data, employment reports
- Interest rate expectations and market pricing

**D. Industrial & Supply Chain**
- Semiconductor, EV, battery, renewable energy developments
- Trade flows, inventory levels, capacity utilization
- Technology breakthroughs or bottlenecks

**E. Tech Governance & Markets**
- AI regulation, data privacy, antitrust actions
- Major tech earnings, M&A, strategic shifts
- Cryptocurrency/digital asset regulatory developments

**Search Strategy:**
- Use WebSearch with site filters: `site:bloomberg.com OR site:reuters.com OR site:ft.com OR site:wsj.com`
- Check official sources: government portals, central bank statements
- Cross-verify with at least 2 independent sources for major claims

### Step 2: Content Selection Criteria

Apply **two layers of filtering**:

**Layer 1: User Preferences** (from Step 0)
- Prioritize stories matching user's specified industries/regions/themes
- If user wants "半导体", ensure at least one deep-dive semiconductor story
- If user wants "中美", weight US-China related news higher in selection

**Layer 2: Universal Quality Filters**

Filter remaining stories through these lenses:

| Criterion | Question to Ask |
|-----------|-----------------|
| **Impact** | Does this affect global markets, supply chains, or major economies? |
| **Novelty** | Is this a new development or just noise/rehash? |
| **Actionability** | Can readers adjust portfolios or strategies based on this? |
| **Duration** | Will this matter in 1 week? 1 month? 1 year? |

Select **4-6** most valuable topics. Prioritize:
1. One major breaking/developing story (lead item)
2. China macro/policy (if relevant)
3. One industrial/supply chain data point
4. Global monetary policy summary
5. Tech/regulatory development

### Step 3: Report Structure

Generate markdown following this exact template:

```markdown
---
title: "每日全球情报解读"
date: "YYYY年M月D日"
---

# 每日全球情报解读 | YYYY年M月D日

## 一、今日主线：[核心事件标题]

### 发生了什么（确认事实）
- **时间线**：用 bullet points 列出关键时间节点（附信息来源）
- **最新进展**：截至报告时间的最新动态

### 为什么是现在（因果链）
| 时间 | 事件 | 意义 |
|------|------|------|
| YYYY-MM | [前置事件] | [为何重要] |
| ... | ... | ... |

**关键变量**
| 变量 | 当前状态 | 阈值 | 监测方式 |
|------|----------|------|----------|
| [指标1] | [数值/状态] | [触发条件] | [数据来源] |

### 市场与资产影响（数据截点：HH:MM CST）
- **能源/大宗**：具体价格变动、百分比
- **权益市场**：主要指数期货/现货变动
- **汇率/固收**：美元指数、关键国债收益率

### 情景推演
| 情景 | 触发条件 | 市场反应 | 概率评估 |
|------|----------|----------|----------|
| 基准情形 | [条件] | [影响] | XX% |
| 上行风险 | [条件] | [影响] | XX% |
| 下行风险 | [条件] | [影响] | XX% |

**当前位置**：[一句话定位当前处于哪种情景]

---

## 二、[主题二：中国宏观/政策/产业]

### [子标题]
- **核心事实**：关键数据/政策内容
- **时间表**（如适用）

### 机构分歧与依据（如适用）
| 机构 | 观点/预测 | 核心依据 |
|------|-----------|----------|
| [机构A] | [观点] | [依据] |

### 结构解释
- 深层机制分析（2-3点）
- 为什么表面数字可能误导

### 对研究的意义
- 投资/策略启示

---

## 三、[主题三：产业/供应链数据]

### 数字本身与参照系
- **核心数字**：XXX（同比/环比，历史对比）
- **参照系**：行业平均、国际对比、历史趋势

### 突破与瓶颈（如适用）
- **突破领域**：
- **瓶颈领域**：

### 机制解释
1. [因果链条]
2. [因果链条]

---

## 四、全球货币政策与流动性地图

### 三组数据拼方向
| 经济体 | 关键数据 | 方向 | 对风险资产边际影响 |
|--------|----------|------|-------------------|
| 美国 | [数据] | [方向] | [影响] |
| 欧洲 | [数据] | [方向] | [影响] |
| 日本 | [数据] | [方向] | [影响] |

### 综合判断
- [3-4点关键结论]

---

## 五、[主题五：科技/治理/其他重要议题]

### 完整事件脉络
- **背景**：[前置条件]
- **发展**：[时间线]
- **关键条款/细节**：[具体信息]

### 影响评估
- [分析要点]

---

## 附：数据来源与免责声明

**主要数据来源**：Bloomberg, Reuters, Wind, 官方政府网站, 上市公司公告

**免责声明**：本报告仅供信息参考，不构成投资建议。数据截至报告生成时间，后续可能有更新。
```

### Step 4: Generate and Save Files

**Archive Location**: Save both markdown and PDF to the user's workspace directory (e.g., `~/.workspace/daily_report/`)

```bash
# Set workspace directory (customize to your environment)
WORKSPACE_DIR="${HOME}/.workspace/daily_report"

# Create archive directory if not exists
mkdir -p "$WORKSPACE_DIR"

# Save markdown
cp daily_report_YYYYMMDD.md "$WORKSPACE_DIR/"
```

### Step 5: Convert to PDF

**Important**: Only PDF should be the final output. Use Chrome/Chromium headless for PDF generation:

```bash
# Set workspace directory
WORKSPACE_DIR="${HOME}/.workspace/daily_report"

# Convert HTML to PDF using Chrome (macOS)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless \
  --disable-gpu \
  --print-to-pdf=daily_report_YYYYMMDD.pdf \
  --run-all-compositor-stages-before-draw \
  daily_report_YYYYMMDD.html

# Or use Chromium on Linux
# chromium-browser --headless --disable-gpu --print-to-pdf=daily_report_YYYYMMDD.pdf ...

# Copy PDF to archive
cp daily_report_YYYYMMDD.pdf "$WORKSPACE_DIR/"
```

### Step 6: Deliver to User

**Send the PDF file directly to the user** via messaging tool:

```bash
# Use message tool with filePath parameter
WORKSPACE_DIR="${HOME}/.workspace/daily_report"
message send --filePath="$WORKSPACE_DIR/daily_report_YYYYMMDD.pdf"
```

**Do NOT**:
- Create Feishu Wiki documents
- Create Feishu Cloud documents
- Generate HTML files (PDF only)

## Content Quality Guidelines

### ✅ DO
- Lead with **what happened** (facts), then **so what** (analysis)
- Include **specific numbers**: prices, percentages, dates
- Use **tables** for comparisons and scenario analysis
- Cite **sources** for key claims (Reuters, Bloomberg, official statements)
- Include **time stamps** for data ("截至3月3日17:00 CST")
- Provide **probability-weighted scenarios** where appropriate
- Add **"对研究的意义"** section explaining actionable insights
- Archive files to your workspace directory (e.g., `~/.workspace/daily_report/`)
- **IMPORTANT**: Always add a blank line before markdown tables to ensure proper rendering

### ❌ DON'T
- Include breaking news without verification
- Use vague qualifiers ("可能", "或许") without probability context
- Overwhelm with minor stories - focus on 4-6 high-impact topics
- Ignore China macro if there's relevant policy news
- Forget to update the date/time in headers
- Create Feishu online documents (PDF delivery only)

## Style Conventions

| Element | Format |
|---------|--------|
| Section headers | `## 一、今日主线：` |
| Sub-headers | `###` level |
| Data tables | Pipe tables with alignment |
| Key metrics | Bold with specific values |
| Time references | 24-hour format, CST timezone |
| Percentages | Use % symbol (e.g., +76%) |
| Currency | USD, CNY, EUR (spell out first use) |

## Markdown Table Format (CRITICAL)

**Always follow this exact format for tables:**

```markdown
**Table Title**

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Important rules:**
1. **Blank line required** between the table title/description and the table itself
2. Header separator line must use `|----------|` format (at least 3 dashes per column)
3. Align columns using colons: `|:---------|` (left), `|----------|` (left default), `|---------:|` (right), `|:--------:|` (center)
4. No blank lines between table rows

**Example - Key Variables Table:**
```markdown
**关键变量**

| 变量 | 当前状态 | 阈值 | 监测方式 |
|------|----------|------|----------|
| 关税规模 | 25% | 全面取消 | 白宫公告 |
| 汇率 | 7.25 | >7.5 | 外汇市场 |
```

**Example - Scenario Analysis Table:**
```markdown
| 情景 | 触发条件 | 市场反应 | 概率评估 |
|------|----------|----------|----------|
| 基准情形 | 维持现状 | 震荡整理 | 50% |
| 上行风险 | 政策利好 | 反弹5% | 30% |
| 下行风险 | 冲突升级 | 下跌10% | 20% |
```

## Example Invocation

**User**: "生成日报"

**Agent**: "生成前请问有特别关注的领域吗？（如半导体/新能源/中美等，或按通用模板）"

**User**: "重点关注半导体"

**Agent actions**:
1. 搜索半导体相关新闻（TSMC、SMIC、供应链等）
2. 调整结构：主线 + 半导体深度 + 其他领域简要
3. 生成并发送 PDF