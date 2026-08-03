# docx-js Creation

Use docx-js for new documents. Write a deterministic Node script that accepts `process.argv[2]`, writes that exact `.docx`, then run it with `{skill_path}/scripts/docx build script.js output.docx`.

## Document Shape

Formal documents should feel like finished Word files, not code dumps:

- Title/cover page when the task is a report, proposal, contract, brief, paper, or client-facing deliverable.
- Visible TOC after the title/cover for multi-section documents.
- Body headings use `HeadingLevel.HEADING_1/2/3` so TOC and navigation work.
- Header carries the document title or section name; footer page numbering uses the current page number only, without labels or total pages.
- Tables have padding, stable widths, and restrained borders.
- Figures preserve aspect ratio and include captions when they support an argument.
- Output filename matches the topic and user's language; Word requests end in `.docx`.

Visual defaults:
- Use one low-saturation palette with 3-4 tiers. Avoid pure `#FF0000`, `#0000FF`, and all-blue/all-purple documents.
- Give headings more space before than after; body text needs comfortable line height; table cells need small margins.
- Chinese body text normally uses a two-character first-line indent and explicit `eastAsia` font.

## Standard Pattern

Keep prose as data, then render it. This prevents JS quoting bugs in exams, contracts, bilingual reports, and quoted source text.

```js
const T = String.raw;

const sections = [
  {
    title: T`一、研究背景`,
    level: 1,
    page: 3,
    paragraphs: [
      T`用户侧储能收益来自峰谷价差、需量管理与辅助服务。`,
      T`合同文本 may define each party as a "Party" without breaking JS strings.`,
      T`试题可写：给正确读音画上"√"，用"____"画出关键句。`,
    ],
  },
];

for (const section of sections) {
  children.push(h1(section.title));
  for (const item of section.paragraphs) children.push(p(item));
}
```

`String.raw` avoids escaping ordinary quotes and backslashes. If text contains a backtick or `${`, escape it or store that text in JSON and read it at runtime. Do not globally replace quote characters in a JS file.

## Skeleton

Prefer this full-form style. `Paragraph.children` is the standard path for plain, styled, mixed, linked, and field content.

```js
import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, Packer, PageNumber,
  Paragraph, TextRun, convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node create.js /absolute/path/output.docx");

const outputDir = path.dirname(outputPath);
const assetDir = path.join(outputDir, "assets");
fs.mkdirSync(assetDir, { recursive: true });

// `name` is the docx-js single-font shorthand. Do not combine it with
// script-specific keys: when `name` is present docx-js ignores `eastAsia`.
const font = {
  ascii: "Times New Roman",
  hAnsi: "Times New Roman",
  cs: "Times New Roman",
  eastAsia: "SimSun",
};
const run = (text, options = {}) => new TextRun({ text, font, size: 24, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 160, line: 300 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});

const p = (text) => para(run(text), { indent: { firstLine: convertInchesToTwip(0.33) } });
const h1 = (text) => para(run(text, { bold: true, size: 30 }), { heading: HeadingLevel.HEADING_1 });

const doc = new Document({
  features: { updateFields: false },
  sections: [{
    headers: { default: new Header({ children: [para(run("Document Title", { bold: true }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(
      new TextRun({ children: [PageNumber.CURRENT] }),
      { alignment: AlignmentType.CENTER },
    )] }) },
    children: [
      h1("Document Title"),
      p("Body text."),
    ],
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
```

## Paragraph Few-Shot

```js
// Good: one shape for plain, styled, and mixed content.
para(run("Plain body text."));
para([run("Important: ", { bold: true }), run("details follow.")]);

// Wrong: docx-js emits both text and children, duplicating visible text.
new Paragraph({ text: "Title", children: [run("Title", { bold: true })] });
```

If a helper builds paragraph options, it should return `children`, not `text`.

```js
const heading = (text) => ({
  heading: HeadingLevel.HEADING_1,
  children: [run(text, { bold: true, size: 30 })],
});
new Paragraph(heading("Chapter 1"));
```

## Table Of Contents

For formal reports, include a TOC that is visible before fields are refreshed. Entries should mirror the actual H1/H2/H3 structure 1:1. Page numbers may be estimates because Word/WPS can refresh them.

```js
import { ImportedXmlComponent } from "docx";

const xmlEscape = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => {
    const indent = Math.max(0, level - 1) * 360;
    return `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
      <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
      <w:ind w:left="${indent}"/></w:pPr>
      <w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`;
  }).join("");

  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr>
    <w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-3&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}
      <w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent>
  </w:sdt>`).root[0]; // Keep .root[0]; docx-js 9.x adds a parser wrapper.
};

children.push(toc(sections.map(({ title, level, page }) => ({ title, level, page }))));
```

Avoid an empty TOC field as the only front-matter navigation. Use the helper above or the build-tested `assets/example.js`; do not invent a different TOC XML shape during document creation.

When a document contains a TOC, set `features.updateFields = true` so Word/WPS can refresh the TOC. For documents without TOC, keep `updateFields` false or omit it; current-page footers do not need open-time field updates. Avoid total page count unless the user asks for it.

## Native Equations

When the user requires Word-native equations, use OMML. Read `references/omml.md` before writing math helpers. Do not rely on validation to reorder math XML; the order of children inside `m:oMath` is the visible formula order.

## Footnotes

Use native footnotes for precise citations. `FootnoteReferenceRun` is a paragraph child; do not wrap it inside `TextRun`.

```js
const doc = new Document({
  footnotes: {
    1: { children: [para(run("Source details."))] },
  },
  sections: [{ children: [
    para([run("A precise claim"), new FootnoteReferenceRun(1), run(".")]),
  ] }],
});
```

## Internal And External Links

For multiple internal targets, avoid `new Bookmark(...)`; current docx-js versions can reuse numeric bookmark IDs. Use explicit `BookmarkStart`/`BookmarkEnd` pairs.

```js
const targetId = 101;

para([
  new BookmarkStart("method", targetId),
  run("Method"),
  new BookmarkEnd(targetId),
], { heading: HeadingLevel.HEADING_1 });

para(new InternalHyperlink({
  anchor: "method",
  children: [run("Jump to Method", { style: "Hyperlink", color: "0563C1" })],
}));

para(new ExternalHyperlink({
  link: "https://example.com",
  children: [run("External source", { style: "Hyperlink", color: "0563C1" })],
}));
```

Keep hyperlinks as a simple paragraph or simple run group unless the surrounding mixed content has already been build-tested. If every company/name/source must be linked, audit `word/_rels/document.xml.rels` and `w:hyperlink`; visible blue text is not enough.

## Images

Derive resource paths from `outputPath`; do not hardcode `/mnt/agents/output/charts`.

```js
const chartPath = path.join(assetDir, "chart.png");

para(new ImageRun({
  type: "png",
  data: fs.readFileSync(chartPath),
  transformation: { width: 500, height: 281 },
}));
```

Preserve aspect ratio. If you need cropping, crop the image file first instead of stretching the DOCX run.

## Tables

Give tables stable grids. For merged cells, use docx-js `columnSpan`/`rowSpan`; for `columnSpan`, set the cell width to the sum of spanned columns. For shading, use docx-js API names, not OOXML attribute names.

```js
import { ShadingType, Table, TableRow, TableCell, WidthType } from "docx";

const widths = [2400, 2400, 2400];
const cell = (text, options = {}) => new TableCell({
  children: [para(run(text))],
  margins: { top: 120, bottom: 120, left: 120, right: 120 },
  ...options,
});

new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: widths,
  rows: [
    new TableRow({ children: [
      cell("Header", {
        shading: { type: ShadingType.CLEAR, fill: "EEF3F6" },
        width: { size: widths[0], type: WidthType.DXA },
      }),
    ] }),
  ],
});
```

Do not write `shading: { val: "clear" }`; docx-js expects `type: ShadingType.CLEAR`.

## Sections

Put page size, margins, orientation, columns, section breaks, headers, and footers in section objects. Do not post-edit `w:sectPr` for normal document creation.

```js
sections: [
  { properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children: [...] },
  { properties: { type: SectionType.NEXT_PAGE, page: { size: { orientation: PageOrientation.LANDSCAPE } } }, children: [...] },
]
```

## Build Discipline

Before building, run `{skill_path}/scripts/setup_node_env check-docx /path/with/script`. It uses the same lookup path as build and tells you whether to install `docx`; if it reports `MISSING`, run the printed `npm install docx` command and check again. Then run `{skill_path}/scripts/docx build`. Do not fix ESM errors by editing `package.json`; the wrapper handles ESM `.js` in CommonJS workspaces.

`build` success means the package generated and validated; it is not a substitute for task-specific checks:

- Exams with A3 landscape/two columns: inspect `w:pgSz`, `w:cols`, margins, and whether requested PDF output exists.
- Long reports: extract final text and count words/characters; check headings, TOC, footnotes, hyperlinks, captions, and chart images.
- Legal/redline documents: if the user asked for revision mode, verify real `w:ins`/`w:del`, not just colored text.

For visual QA, run `{skill_path}/scripts/docx render <file.docx> <output-dir>` when LibreOffice is available. The command converts the DOCX to PDF, renders every page, and creates a contact sheet. Review every warning and the contact sheet before delivery. If no renderer is available, say that visual QA was unavailable; do not describe a structure-only validation as a rendered visual check.
