# OMML Native Equations

Use OMML when the user asks for native Word equations. Keep helpers small and explicit; do not hand-build a whole math engine.

## Ordering Rule

`m:oMath` is sequence-sensitive. Its children render in document order.

```xml
<!-- Good: renders A = [matrix] + B -->
<m:oMath>
  <m:r><m:t>A = </m:t></m:r>
  <m:m>...</m:m>
  <m:r><m:t> + B</m:t></m:r>
</m:oMath>
```

Do not sort OMML children by schema order. A schema list says which child types are allowed, not how to rearrange a formula.

## Minimal JS Pattern

docx-js can carry OMML as raw XML inside an `ImportedXmlComponent`.

```js
import { ImportedXmlComponent, Paragraph } from "docx";

const importXml = (xml) => ImportedXmlComponent.fromXmlString(xml).root[0];
const math = importXml;

const mr = (text) => `<m:r><m:t>${escapeXml(text)}</m:t></m:r>`;
const mArg = (inner) => `<m:e>${inner}</m:e>`;

const equation = new Paragraph({
  children: [math(`
    <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      ${mr("A = ")}
      <m:m>
        <m:mr>${mArg(mr("1"))}${mArg(mr("0"))}</m:mr>
        <m:mr>${mArg(mr("0"))}${mArg(mr("1"))}</m:mr>
      </m:m>
    </m:oMath>
  `)],
});
```

Use XML escaping for text inserted into `m:t`.

```js
const escapeXml = (s) => String(s)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");
```

Avoid docx-js math class guessing for complex equations. If a task needs matrices, determinants, radicals, fractions, or augmented matrices, raw OMML via `importXml(...)` is more predictable than experimenting with undocumented constructor shapes. Keep `.root[0]`; docx-js 9.x wraps parsed XML in a non-OOXML container without it.

## Common Structures

Fraction:

```xml
<m:f>
  <m:num><m:r><m:t>a+b</m:t></m:r></m:num>
  <m:den><m:r><m:t>c</m:t></m:r></m:den>
</m:f>
```

Radical:

```xml
<m:rad>
  <m:e><m:r><m:t>x+1</m:t></m:r></m:e>
</m:rad>
```

Subscript and superscript:

```xml
<m:sSub><m:e><m:r><m:t>a</m:t></m:r></m:e><m:sub><m:r><m:t>i</m:t></m:r></m:sub></m:sSub>
<m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup>
```

Matrix:

```xml
<m:m>
  <m:mPr><m:baseJc m:val="center"/></m:mPr>
  <m:mr><m:e><m:r><m:t>1</m:t></m:r></m:e><m:e><m:r><m:t>2</m:t></m:r></m:e></m:mr>
  <m:mr><m:e><m:r><m:t>3</m:t></m:r></m:e><m:e><m:r><m:t>4</m:t></m:r></m:e></m:mr>
</m:m>
```

Delimiter, useful for determinants and augmented matrices:

```xml
<m:d>
  <m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr>
  <m:e>...</m:e>
</m:d>
```

## Practical Guidance

- Split very complex expressions into adjacent `m:oMath` objects if that makes ordering clearer.
- For augmented matrices, use stretch delimiters (`m:d`) for brackets and a deliberate separator column or delimiter for the vertical bar.
- Keep labels such as `A =`, `det`, determinant bars, matrices, and `= 0` in the same `m:oMath` and in visible order when possible.
- True fractions use `m:f/m:num/m:den`; true radicals use `m:rad`. Do not put `1/2` or `√2` inside plain `m:t` when the user asks for native equations.
- Run `{skill_path}/scripts/docx build`; then inspect validation errors. Validator repairs will not reorder OMML for you.
