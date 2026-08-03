import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  Document,
  Footer,
  Header,
  HeadingLevel,
  ImportedXmlComponent,
  Packer,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
  convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error("Usage: node example.js /absolute/path/output.docx");
}

const outputDir = path.dirname(outputPath);
const assetDir = path.join(outputDir, "assets");
fs.mkdirSync(assetDir, { recursive: true });

const T = String.raw;
const title = T`Document Title`;
const palette = {
  dark: "263238",
  primary: "37474F",
  light: "78909C",
  border: "D8E0E3",
  fill: "EEF3F6",
};

const font = {
  ascii: "Times New Roman",
  hAnsi: "Times New Roman",
  cs: "Times New Roman",
  eastAsia: "SimSun",
};

const run = (text, options = {}) =>
  new TextRun({
    text,
    font,
    size: 24,
    ...options,
  });

const para = (children, options = {}) =>
  new Paragraph({
    spacing: { after: 160, line: 300 },
    ...options,
    children: Array.isArray(children) ? children : [children],
  });

const bodyPara = (text, options = {}) =>
  para(run(text), {
    indent: { firstLine: convertInchesToTwip(0.33) },
    ...options,
  });

const heading = (text, level = 1) =>
  para(run(text, { bold: true, size: level === 1 ? 30 : 26, color: palette.dark }), {
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
  });

const cell = (text, options = {}) =>
  new TableCell({
    children: [para(run(text))],
    margins: { top: 120, bottom: 120, left: 120, right: 120 },
    ...options,
  });

const xmlEscape = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const toc = (entries) => {
  const cached = entries
    .map(({ title: entryTitle, level, page }) => {
      const indent = Math.max(0, level - 1) * 360;
      return `<w:p>
        <w:pPr>
          <w:pStyle w:val="TOC${level}"/>
          <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
          <w:ind w:left="${indent}"/>
        </w:pPr>
        <w:r><w:t>${xmlEscape(entryTitle)}</w:t></w:r>
        <w:r><w:tab/></w:r>
        <w:r><w:t>${xmlEscape(page)}</w:t></w:r>
      </w:p>`;
    })
    .join("");

  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr>
    <w:sdtContent>
      <w:p>
        <w:r>
          <w:fldChar w:fldCharType="begin" w:dirty="true"/>
          <w:instrText xml:space="preserve"> TOC \\o &quot;1-3&quot; \\h \\z \\u </w:instrText>
          <w:fldChar w:fldCharType="separate"/>
        </w:r>
      </w:p>
      ${cached}
      <w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent>
  </w:sdt>`).root[0]; // Keep .root[0]; docx-js 9.x adds a parser wrapper.
};

const metricTable = () => {
  const widths = [2600, 2600, 2600];
  const headerCell = (text) =>
    cell(text, {
      shading: { type: ShadingType.CLEAR, fill: palette.fill },
      width: { size: widths[0], type: WidthType.DXA },
    });

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: widths,
    rows: [
      new TableRow({
        children: [headerCell("Metric"), headerCell("Current"), headerCell("Note")],
      }),
      new TableRow({
        children: [
          cell("Revenue"),
          cell("12.4M"),
          cell(T`Quoted text such as "Company" is safe in data literals.`),
        ],
      }),
    ],
  });
};

const sections = [
  {
    title: T`一、研究背景`,
    level: 1,
    page: 3,
    paragraphs: [
      T`中文正文使用 eastAsia 字体和首行缩进，避免回退到 Calibri。`,
      T`试题、合同、访谈稿可直接包含"√"、"Party"、"____"等文本。`,
    ],
  },
  {
    title: T`1.1 数据与方法`,
    level: 2,
    page: 4,
    paragraphs: [
      T`正文先作为数据组织，再由 helper 渲染成 Paragraph 和 TextRun。`,
    ],
  },
  {
    title: T`二、核心指标`,
    level: 1,
    page: 5,
    paragraphs: [
      T`表格设置稳定列宽，单元格底纹使用 ShadingType.CLEAR。`,
    ],
    table: metricTable,
  },
];

const children = [
  para(run(title, { bold: true, size: 36, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { after: 360 },
  }),
  para(run("目录", { bold: true, size: 30, color: palette.dark }), {
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 120 },
  }),
  para(run(T`右键目录，选择"更新域"刷新页码。`, { italics: true, color: palette.light })),
  toc(
    sections.map(({ title: entryTitle, level, page }) => ({
      title: entryTitle,
      level,
      page,
    })),
  ),
];

for (const section of sections) {
  children.push(heading(section.title, section.level));
  for (const paragraph of section.paragraphs) {
    children.push(bodyPara(paragraph));
  }
  if (section.table) {
    children.push(section.table());
  }
}

const doc = new Document({
  features: { updateFields: true },
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: 1440,
            bottom: 1440,
            left: 1440,
            right: 1440,
          },
        },
      },
      headers: {
        default: new Header({
          children: [
            para(run(title, { bold: true, color: palette.primary }), {
              alignment: AlignmentType.CENTER,
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            para(
              new TextRun({ children: [PageNumber.CURRENT] }),
              {
              alignment: AlignmentType.CENTER,
              },
            ),
          ],
        }),
      },
      children,
    },
  ],
});

const buffer = await Packer.toBuffer(doc);
fs.writeFileSync(outputPath, buffer);
