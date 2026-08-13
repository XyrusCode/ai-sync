---
name: xlsx
description: "Create and analyze Excel spreadsheets (.xlsx/.csv). Supports formula-driven analysis, charts, conditional formatting, styled reports, and financial modeling (three-statement models, DCF, comps analysis). Use when the user mentions Excel, spreadsheet, .xlsx, .csv, or asks for data analysis with formulas."
---

<role>
- You must eventually deliver an Excel file (.xlsx)
- Do not provide readme documentation or extra files unless requested
</role>

<Technology Stack>

## Excel File Creation: Python + openpyxl/pandas

**✅ REQUIRED Technology Stack for Excel Creation:**
- **Runtime**: Python 3
- **Primary Library**: openpyxl (for Excel file creation, styling, formulas)
- **Data Processing**: pandas (for data manipulation, then export via openpyxl)
- **Execution**: Write a Python script in the workspace and run it with `python` through the Bash tool

**🔧 Execution Environment:**
- Daimon's managed interpreter is already first on the Bash tool's PATH. Run workspace scripts with `python`; do not hard-code the interpreter path

**Python Excel Creation Pattern:**
```python
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
import pandas as pd

# Create workbook
wb = Workbook()
ws = wb.active
ws.title = "Data"

# Add data
ws['A1'] = "Header1"
ws['B1'] = "Header2"

# Apply styling
ws['A1'].font = Font(bold=True, color="FFFFFF")
ws['A1'].fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")

# Save
wb.save('output.xlsx')
```

</Technology Stack>

<Financial Sub Skills>

## Finance Sub-Skills

For finance tasks, load only the needed sub skill. Use the active finance sub skill as the primary authority for methodology, model structure, workbook construction, layout, fonts, colors, formatting logic, and finance-specific review or validation standards. For content not covered by the active finance sub skill, follow this parent `xlsx` skill. If a finance sub skill defines stricter review, validation, checking, or delivery requirements, follow the finance sub skill first.

Default coordination:
1. `comps-analysis` is usually standalone. Combine it with another valuation workflow only when the user explicitly asks, and then refer to the method and reference
2. `DCF ` usually builds on `3 statement model`. If the user asks for a DCF,  first leverage`3 statement model`, then build on it and extend with `DCF `, unless the user explicitly asks to skip the three-statement model or wants a very simple version.
3. Other model-based `PE` / `IB` valuation tasks such as `LBO` usually start from `3 statement model`, unless the user asks for a presentation-only output or provides a completed model.

### 1. `3 statement model`
- Entry file: `./reference/3_statement_model_skill.md`
- Use when the task needs a full operating model, linked `Income Statement` / `Balance Sheet` / `Cash Flow`, supporting schedules, balance checks, or a forecast-model foundation for `DCF ` or other model-based `PE` / `IB` valuation work.
- If the end goal is `DCF ` or another model-based valuation, this is the default first build step unless the user provides a completed model, explicitly asks not to generate the three-statement model, or asks for a very simple version.

### 2. `DCF `
- Entry file: `./reference/DCF_SKILL.md`
- Use for DCF valuation, `NOPAT`, `UFCF`, `WACC`, terminal value, discounting, `EV -> Equity Value -> Implied Share Price`, sensitivity tables, or DCF review / standardization work.
- The DCF format reference is embedded inside `./reference/DCF_SKILL.md`, please refer to the format when building
- If the user needs a DCF build and no completed forecast model exists, first use `3 statement model`, then extend that workbook with `DCF `, unless the user explicitly asks to skip the three-statement model or wants a very simple version.
- When the user asks to build valuation and does not specifically ask a model category, build DCF for the user using the relevant sub-skills as needed

### 3. `comps-analysis`
- Entry file: `./reference/comps-analysis/Comps_analysis SKILL.md`
- Optional references: `./reference/comps-analysis/references/workbook_format.md`, `./reference/comps-analysis/references/model_construction.md`, `./reference/comps-analysis/references/calculation_guide.md`
- Use for standalone public comps, peer tables, trading multiples, valuation ranges, implied valuation from market multiples, or comps review / standardization work.
- Do not pair it with `3 statement model` or `DCF ` unless the user explicitly wants a combined valuation deliverable.

Finance outputs must remain formula-linked, auditable, and Excel-native. It is strictly forbidden to calculate derived model outputs in Python or any external tool and then paste finished hardcoded numbers into Excel; if a value can be linked by workbook formulas, it MUST remain formula-driven in the delivered file. If external market or company data is fetched, source citation rules in this parent skill still apply unless the active finance sub skill is stricter. **Important**

### Finance Sub-Skill Execution Protocol (**MANDATORY**)
- If a finance task is routed to one or more finance sub skills, you MUST read the FULL content of each applicable sub skill before building anything.
- For finance tasks, data faithfulness is critical: if the user provides attachments, read them carefully and use them as the primary source where applicable; when searching externally, prioritize high-quality sources such as company filings and annual reports, SEC filings, iFinD, and reliable market data sources such as Yahoo Finance
- In all finance models, static hardcoded values are allowed only for true inputs, assumptions, or historical/raw reported data. Any derived, calculated, rolled-forward, allocated, projected, or valuation output must be generated by Excel formulas, including the other models that have not been covered yet
- It is absolutely prohibited to use Python or any external calculation layer to compute derived model results and then fill those completed values into the workbook. Build the logic in Excel formulas so the workbook remains linked, traceable, and updateable.
- If the active finance sub skill references format files, layout references, templates, or example pages, you MUST also read those referenced files before starting the workbook.
- You MUST fully follow the active sub skill's methodology, workbook structure, layout, fonts, colors, formula logic, checks, and delivery standards. Do not simplify or partially apply them.
- The active finance sub skill has higher priority than this parent skill for methodology, model construction, formatting, review, and validation. Use this parent skill only to solve uncovered situations
- For `3 statement model` and `DCF ` work, `Raw Data` must remain historical-only, and historical mapping must first reconcile to reported totals before being used as the forecast opening balance.
- For `3 statement model` and `DCF ` work, the model is NOT deliverable unless all required checks pass, including visible `Balance Check`, `BS Cash <- CF Ending Cash` by year, retained earnings roll-forward, and any stricter sub-skill validation requirements.
- If required validation checks (e.g., Balance Check, BS Cash reconciliation) cannot be performed in code, do not present the workbook as fully validated or fully compliant with the skill standard.

</Financial Sub Skills>

<External Data in Excel>

When creating Excel files with externally fetched data:

**Source Citation (MANDATORY):**
- ALL external data MUST have source citations in final Excel
- **🚨 This applies to ALL external tools**: `datasource`, `web_search`, API calls, or any fetched data
- Use **two separate columns**: `Source Name` | `Source URL`
- Do NOT use HYPERLINK function (use plain text to avoid formula errors)
- **⛔ FORBIDDEN**: Delivering Excel with external data but NO source citations
- Example:

| Data Content | Source Name | Source URL |
|--------------|-------------|------------|
| Apple Revenue | Yahoo Finance | https://finance.yahoo.com/... |
| China GDP | World Bank API | world_bank_open_data |

- If citation per-row is impractical, create a dedicated "Sources" sheet

</External Data in Excel>


<Analyze rule>

<Important Guideline>
- All formula values must be in numeric format, not text. Be careful when writing via openpyxl
- Check that cells referenced by formulas are not misaligned. When result is 0 or null, re-check referenced cells
- No circular references — every calculated cell must resolve to a valid value
- For financial/fiscal data, present numbers in currency format (add currency symbol before numbers)
- If scenario assumptions are required for formulas, complete them in advance — never leave "Manual calculation required" placeholders
</Important Guideline>


<Excel Creation Workflow>

## Excel Creation Workflow

**CRITICAL: Verify EACH sheet immediately after creation, NOT after all sheets are done!**

```
For each sheet in workbook:
    1. PLAN   → Design this sheet's structure, formulas, references
    2. CREATE → Write data, formulas, styling for this sheet
    3. SAVE   → Save the workbook (wb.save())
    4. CHECK  → Verify formulas, references, styling in code
    5. NEXT   → Only proceed to next sheet after current sheet is correct

After ALL sheets:
    6. RECALC → Attempt to recalculate all formulas (see below)
    7. VERIFY → Read the verification status; do not infer results from empty caches
    8. REPORT → Report derived values only after real recalculation or independent QA
    9. DELIVER → Disclose deferred recalculation when no calculation engine is available
```

### Formula Recalculation (MANDATORY)

openpyxl writes formula strings but does NOT compute cached results. Without recalculation, formula cells appear empty in WPS, Google Sheets, or programmatic reads.

**After saving the final workbook, recalculate all formulas:**

```bash
python "${KIMI_SKILL_DIR}/scripts/xlsx_tools.py" recalc output.xlsx
```

The script tries formulas library → libreoffice → calcMode=auto fallback. Interpret its JSON result precisely:

- `status: "success"` with `method: "formulas"` or `method: "libreoffice"` means a calculation engine ran. The `formulas` method calculates only the separate verification copy named in `verification_file`.
- `status: "deferred"` with `method: "calcMode_auto"` means **no formula calculation happened**. The original file only requests recalculation when Excel/WPS opens it. Treat all formula results as unverified and disclose that limitation.

**WARNING**: `formulas` library's `write()` strips charts and styling. The script writes a separate verification file — always deliver the original openpyxl-generated file.

### Post-Recalculation Verification

```bash
python "${KIMI_SKILL_DIR}/scripts/xlsx_tools.py" verify output.xlsx
```

Checks for: formula errors (#REF!, #VALUE!, etc.), missing formula caches, forbidden functions (FILTER/UNIQUE/XLOOKUP), and implicit array formulas (MATCH(TRUE(),...)). Interpret `status` as follows:

- `status: "pass"`: no detected errors, warnings, or missing formula caches.
- `status: "pass_with_warnings"`: cached formula results exist, but compatibility warnings remain.
- `status: "unverified"`: one or more formula cells have no cached result; this is **not** proof of zero formula errors.
- `status: "fail"`: a deterministic error was detected.

Exit code 0 means no deterministic error was detected; it does not turn `unverified` into `pass`. When results are unverified, independently calculate and reconcile any derived values mentioned in the final response from the raw inputs, or omit those values. If recalculation is deferred, the independent QA command must print every derived value that the final response will report; copy those values from the command output instead of recomputing or estimating them in prose, and omit any value that was not printed and checked. Independent QA must not replace the workbook's formulas with hardcoded outputs.

### Excel Formulas Are ALWAYS the First Choice

Wherever a formula CAN be used, it MUST be used.

✅ **CORRECT** - Use Excel formulas:
```python
ws['C2'] = '=A2+B2'           # Sum
ws['D2'] = '=C2/B2*100'       # Percentage
ws['E2'] = '=SUM(A2:A100)'    # Aggregation
```

❌ **FORBIDDEN** - Pre-calculate in Python and paste static values:
```python
result = value_a + value_b
ws['C2'] = result    # BAD: Static value, not a formula
```

**Only use static values when**: data is from external sources, values are constants, or formula would create circular reference.

### Formula Error Prevention

Common formula errors to watch for: #VALUE!, #DIV/0!, #REF!, #NAME?, #N/A.

1. **ZERO TOLERANCE**: Any formula error must be fixed before delivery.
2. **DO NOT assume errors will "auto-resolve"** when opened in Excel.
3. **Zero-value cells**: If a formula returns 0, verify the referenced cells actually contain data.
4. **Off-by-one references**: Ensure formulas reference correct cells (not headers, not out-of-range).
5. **Implicit array formulas**: Patterns like `MATCH(TRUE(), A1:A10>0, 0)` work in LibreOffice but show #N/A in MS Excel (requires CSE Ctrl+Shift+Enter). Rewrite using alternatives:
   - ❌ `=MATCH(TRUE(), A1:A10>0, 0)` → #N/A in Excel
   - ✅ `=SUMPRODUCT((A1:A10>0)*ROW(A1:A10))-ROW(A1)+1`
   - ✅ Or use a helper column with explicit TRUE/FALSE values

### Error Discipline

DO NOT rationalize away formula errors:
- ❌ "These errors will disappear when the user opens the file in Excel" — WRONG, fix them
- ❌ "The #REF! is because openpyxl doesn't evaluate formulas" — WRONG, fix the formula
- ❌ "The #VALUE! will resolve when opened in Excel" — WRONG, fix it
- ❌ "Zero values are expected" — VERIFY each one; many are reference errors

Files with ANY formula errors CANNOT be delivered to users.

### Forbidden Patterns

- Creating all sheets first, then verifying once at the end
- Skipping the planning step for any sheet
- Ignoring formula errors and proceeding to next sheet

</Excel Creation Workflow>

<VLOOKUP Usage Rules>
**When to Use**: User requests lookup/match/search; Multiple tables share keys (ProductID, EmployeeID); Master-detail relationships; Code-to-name mapping; Cross-file data with common keys; Keywords: "based on", "from another table", "match against"

**Syntax**: `=VLOOKUP(lookup_value, table_array, col_index_num, FALSE)` — lookup column MUST be leftmost in table_array
**Best Practices**: Use FALSE for exact match; Lock range with `$A$2:$D$100`; Wrap with `IFERROR(...,"N/A")`; Cross-sheet: `Sheet2!$A$2:$C$100`
**Errors**: #N/A=not found; #REF!=col_index exceeds columns. **Alt**: INDEX/MATCH when lookup column not leftmost
```python
ws['D2'] = '=IFERROR(VLOOKUP(A2,$G$2:$I$50,3,FALSE),"N/A")'
```
</VLOOKUP Usage Rules>

<Baseline error>
**Forbidden Formula Errors**:
1. Formula errors: #VALUE!, #DIV/0!, #REF!, #NAME?, #NULL!, #NUM!, #N/A - NEVER include
2. Off-by-one references (wrong cell/row/column)
3. Text starting with `=` interpreted as formula
4. Static values instead of formulas (use formulas for calculations)
5. Placeholder text: "TBD", "Pending", "Manual calculation required" - FORBIDDEN
6. Missing units in headers; Inconsistent units in calculations
7. Currency without format symbols (¥/$)
8. Result of 0 must be verified - often indicates reference error

**🚨 FORBIDDEN FUNCTIONS (Incompatible with older Excel versions)**:

The following functions are **NOT supported** in Excel 2019 and earlier. Files using these functions will **FAIL to open** in older Excel versions. Use traditional alternatives instead.

| ❌ Forbidden Function | ✅ Alternative |
|----------------------|----------------|
| `FILTER()` | Use AutoFilter, or SUMIF/COUNTIF/INDEX-MATCH |
| `UNIQUE()` | Use Remove Duplicates feature, or helper column with COUNTIF |
| `SORT()`, `SORTBY()` | Use Excel's Sort feature (Data → Sort) |
| `XLOOKUP()` | Use `INDEX()` + `MATCH()` combination |
| `XMATCH()` | Use `MATCH()` |
| `SEQUENCE()` | Use ROW() or manual fill |
| `LET()` | Define intermediate calculations in helper cells |
| `LAMBDA()` | Use named ranges or VBA |
| `RANDARRAY()` | Use `RAND()` with fill-down |
| `ARRAYFORMULA()` | Google Sheets only - use Ctrl+Shift+Enter array formulas |
| `QUERY()` | Google Sheets only - use SUMIF/COUNTIF/PivotTable |
| `IMPORTRANGE()` | Google Sheets only - copy data manually |

**Why these are forbidden**:
- These are Excel 365/2021+ dynamic array functions or Google Sheets functions
- Older Excel versions (2019, 2016, etc.) cannot parse these formulas
- The file will show errors when opened in older Excel

**Example - Converting FILTER to INDEX-MATCH**:
```
❌ WRONG: =FILTER(A2:C100, B2:B100="Active")
✅ CORRECT: Use AutoFilter on the data range, or create a PivotTable
```

**⚠️ Off-By-One Prevention**: Before saving, verify each formula references correct cells. Common errors: referencing headers, wrong row/column offset. If result is 0 or unexpected → check references first.

**💰 Financial Values**: Store in smallest unit (15000000 not 1.5M). Use Excel format for display: `"¥#,##0"`. Never use scaled units requiring conversion in formulas.

</Baseline error>

</Analyze rule>

<Style Rules>

Use python-openpyxl package to design the style of excel. Apply styling directly in openpyxl code.

**🎨 Overall Visual Design Principles**
- **⚠️ MANDATORY: Hide Gridlines** - ALL sheets MUST have gridlines hidden (see code below)
- Start at B2 (top-left padding), not A1
- **Title Row Height**: Since content starts at B2, row 2 is typically the title row with larger font. Always increase row 2 height to prevent text clipping: `ws.row_dimensions[2].height = 30` (adjust based on font size)
- **⚠️ MANDATORY: Do NOT use wrap text by default** - keep `wrap_text` off unless the user explicitly asks for it or the active sub skill explicitly requires it
- **Professionalism First**: Adopt business-style color schemes, avoid over-decoration that impairs data readability
- **Consistency**: Use uniform formatting, fonts, and color schemes for similar data types
- **Clear Hierarchy**: Establish information hierarchy through font size, weight, and color intensity
- **Appropriate White Space**: Use reasonable margins and row heights to avoid content crowding
- Please arrange the appropriate width and height dimensions for each cell, and do not have a cell that is not wide enough and too high, resulting in a display scale imbalance

---

**📐 Merged Cells Guide**

Use `ws.merge_cells()` for titles, headers spanning columns, or grouped labels. Apply style to **top-left cell only**.

```python
# Merge and style
ws.merge_cells('B2:F2')
ws['B2'] = "Report Title"
ws['B2'].font = Font(size=18, bold=True)
ws['B2'].alignment = Alignment(horizontal='center', vertical='center')
```

**Rules**:
- ✅ Use for: titles, section headers, category labels spanning columns
- ❌ Avoid in: data areas, formula ranges, PivotTable source data
- Always set `alignment` on merged cells for proper text positioning

---

**🎨 Style Selection Guide**
- **Minimalist Monochrome Style**: Default for ALL non-financial tasks (Black/White/Grey + Blue accent only)
- **Professional Finance Style**: For general financial/fiscal analysis (stock, GDP, salary, public finance), if it's fiancial sub skills relevant, refer to the sub skills

---

<Minimalist_Monochrome_Style>
## 📊 Minimalist Monochrome Style (DEFAULT)

### 🎨 Core Color Principle (STRICTLY ENFORCED)

**Base Colors (ONLY these 3):**
- **White (#FFFFFF)** - Background, content areas
- **Black (#000000)** - Primary text, key headers
- **Grey (various shades)** - Structure, secondary elements, borders

**Accent Color (ONLY Blue for differentiation):**
- When you need to highlight, differentiate, or emphasize, use **Blue** with varying lightness/saturation
- NO other colors allowed (no green, red, orange, purple, etc.) except for regional financial indicators and the font color conventions below (blue=input, green=cross-sheet, red=external)

### ⚠️ STRICTLY FORBIDDEN

- ❌ **NO** Green, Red, Orange, Purple, Yellow, Pink or any other colors
- ❌ **NO** Rainbow or multi-color schemes
- ❌ **NO** Saturated/vibrant colors except Blue accents
- ❌ **NO** Color gradients using multiple hue families

### Python Color Palette

Monochrome hex values: background `FFFFFF`/`F5F5F5`/`F9F9F9`, headers `000000`/`333333`, border `D0D0D0`, blue accent `0066CC`/`4A90D9`/`E6F0FA`. Always `ws.sheet_view.showGridLines = False`.
</Minimalist_Monochrome_Style>

<Professional_Finance_Style>
## 💎 Professional Finance Style (For Financial Tasks)

Use this style when the task involves: stock, GDP, salary, revenue, profit, budget, ROI, public finance, or any fiscal analysis.

### 🚨 CRITICAL: Regional Color Convention for Financial Data

| **Region** | **Price Up** | **Price Down** |
| --- | --- | --- |
| **China (Mainland)** | **Red** | **Green** |
| **Outside China (International)** | **Green** | **Red** |

### Python Color Palette

Finance hex values: background `ECF0F1`, header `122B49`, accent `FFF3E0`, negative `FF0000`.

</Professional_Finance_Style>

---

<Conditional_Formatting>

## Conditional Formatting (PROACTIVE USE)

| Data Type | Format | Key API |
|-----------|--------|---------|
| Numeric | Data Bars | `DataBarRule(start_type='min', end_type='max', color='4A90D9')` |
| Distribution | Color Scales | `ColorScaleRule(start_color='FFFFFF', end_color='4A90D9')` |
| KPIs | Icon Sets | `IconSetRule(icon_style='3TrafficLights1', values=[0,33,67])` |
| Thresholds | Highlight | `CellIsRule(operator='greaterThan', formula=['100000'], fill=...)` |

Icon styles: `3TrafficLights1`, `3Arrows`, `3Symbols`, `5Rating`.

```python
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule, IconSetRule, CellIsRule

# Data Bar
ws.conditional_formatting.add('C2:C100', DataBarRule(start_type='min', end_type='max', color='4A90D9', showValue=True))

# 3-Color Scale (Red→Yellow→Green)
ws.conditional_formatting.add('D2:D100', ColorScaleRule(start_type='min', start_color='F8696B', mid_type='percentile', mid_value=50, mid_color='FFEB84', end_type='max', end_color='63BE7B'))

# Icon Set
ws.conditional_formatting.add('E2:E100', IconSetRule(icon_style='3TrafficLights1', type='percent', values=[0, 33, 67], showValue=True))
```

**Best Practices**: Apply to 2-4 key columns per sheet; use consistent color meanings; combine Data Bars + Icons for impact.

</Conditional_Formatting>

---

**📝 Text Color Style (MUST FOLLOW)**
- **Blue font**: Fixed values/input values
- **Black font**: Cells with calculation formulas
- **Green font**: Cells referencing other sheets
- **Red font**: Cells with external reference
- For finance models, these color rules are hard minimum standards and must remain consistent sheet by sheet unless the active finance sub skill is stricter.
- For finance models, if a formula combines references with arithmetic, it is a calculation formula and must be black, not green.

---

**📏 Border Styles**
- In general cases, do not add borders to cells to make the whole content appear more focused
- Do not use a table border line unless you need to use a border line to reflect the calculation results
- Sometimes, you can use 1px borders within models, thicker for section breaks


<Cover Page Design>

**Every Excel deliverable MUST include a Cover Page as the FIRST sheet.**

## Cover Page Structure

| Row | Content | Style |
|-----|---------|-------|
| 2-3 | **Report Title** | Large font (18-20pt), Bold, Centered |
| 5 | Subtitle/Description | Medium font (12pt), Gray color |
| 7-15 | **Key Metrics Summary** | Table format with highlights |
| 17-20 | **Sheet Index** | List of all sheets with descriptions |
| 22+ | Notes & Instructions | Small font, Gray |

## Required Elements

**1. Report Title** - Clear, descriptive title of the workbook

**2. Key Metrics Summary** - 3-6 most important numbers/findings:

**3. Sheet Index** - Navigation guide:
```
| Sheet Name | Description |
|------------|-------------|
| Raw Data | Original dataset (100 rows) |
| Analysis | Sales breakdown by region |
| Pivot Summary | Interactive pivot analysis |
```

**4. PivotTable Notice** (MANDATORY when workbook contains PivotTables):
```
⚠️ IMPORTANT: This workbook contains PivotTables.
   Please refresh data after opening:
   - Windows: Select PivotTable → Right-click → Refresh
   - Mac: Select PivotTable → PivotTable Analyze → Refresh
   - Or press Ctrl+Alt+F5 to refresh all
```

## Cover Page Styling

- **Background**: Clean white or light gray (#F5F5F5)
- **Title row height**: 30-40pt for prominence
- **No gridlines**: Hide gridlines on Cover sheet for clean look
- **Column width**: Merge cells A-G for title area
- **Color scheme**: Match the workbook's theme (monochrome/finance)


## Hide gridlines
Make sure the gridlines of covers still keep hiden
</Cover Page Design>

</Style Rules>

<Visual chart>

## ⚠️ CRITICAL: You MUST Create REAL Excel Charts

**Stronger Requirement (Proactive Visualization)**:
- If the user asks for charts/visuals, you MUST actively create charts instead of waiting for explicit per-table requests.
- When a workbook has multiple prepared datasets/tables, ensure **each prepared dataset has at least one corresponding chart** unless the user explicitly says otherwise.
- If any dataset is not visualized, explain why and ask for confirmation before delivery.

**Trigger Keywords** - When user mentions ANY of these, you MUST create actual embedded charts:
- "visual", "chart", "graph", "visualization", "visual table", "diagram"
- "show me a chart", "create a chart", "add charts", "with graphs"

**❌ ABSOLUTELY FORBIDDEN**:
- Creating a "CHARTS DATA" sheet with data + instructions "Go to Insert > Charts"
- Telling user to manually create charts themselves
- Marking "Add visual charts" as completed without actual charts

**✅ REQUIRED**:
- **Default**: Create embedded Excel charts inside the .xlsx file using openpyxl
- **Only if user explicitly requests**: Create standalone PNG/JPG image files separately

**Mandatory Workflow**:
```
1. Create Excel with openpyxl (data, styling)
2. Add charts using openpyxl.chart module
3. Save file
4. Verify charts have data by reopening and checking
```

**openpyxl Chart Guide**

```python
from openpyxl.chart import BarChart, LineChart, PieChart, Reference

chart = BarChart()
chart.type = "col"
chart.title = "Sales by Category"
data_ref = Reference(ws, min_col=2, min_row=1, max_row=4)
cats_ref = Reference(ws, min_col=1, min_row=2, max_row=4)
chart.add_data(data_ref, titles_from_data=True)  # titles_from_data=True → legend uses header row
chart.set_categories(cats_ref)
ws.add_chart(chart, "E2")
```

| Chart Type | Class | Key Config |
|------------|-------|------------|
| Column/Bar | `BarChart()` | `type="col"` (vertical) or `type="bar"` (horizontal) |
| Line | `LineChart()` | Same pattern as above |
| Pie | `PieChart()` | No axes needed, no `set_categories` |
| Area | `AreaChart()` | `grouping="standard"` |

| Data Type | Best Chart |
|-----------|-----------|
| Trend | Line |
| Compare | Column/Bar |
| Composition | Pie (≤6 items) |
| Distribution | Histogram |
| Composition | Pie/Doughnut | Percentages (≤6 items) |
| Distribution | Histogram | Data spread |
| Correlation | Scatter | Relationships |

**Chart Color Scheme**:
- Monochrome: `333333`, `666666`, `0066CC`, `4A90D9`
- Finance: `122B49`, `274C77`, `3B6796`, `D9E2F3`

</Visual chart>

<Attention items>

## Other Requirements

- Final delivery must contain at least one .xlsx file
- Every table must have content, not just headers
- Check formula cells returning null — verify referenced cells have values
- Arrange row heights and column widths proportionally
- All calculations use real data unless user requests simulated data
- Mark units in table headers, not after numbers in cells
- Use the required style template (Monochrome default; Finance for financial tasks)
- When using external data (web search, API), include `Source Name` + `Source URL` columns in final Excel

</Attention items>
