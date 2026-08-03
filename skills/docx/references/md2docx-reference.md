# Markdown → Word Citation Reference

Convert a swarm-assembled Markdown report (with standard Markdown footnotes)
into a Word document whose citations are real footnotes, endnotes, or hyperlink
cross-references.

## When to Use

Use this pipeline **only** for multi-section Markdown assembled from several
`*_sec{NN}.md` sections into a final report such as `*.agent.final.md`.

For any one-off document the user asks you to write, author it natively with
`docx-js` (the Create route). This pipeline is the normalization exit for
assembled Markdown, not a general Markdown→Word converter.

## Citation Input Format

The source Markdown uses **standard Markdown footnotes**. The model writes the
source metadata inline; there is no external citation database.

```markdown
正文断言[^kimi-k26]，再次引用同源[^kimi-k26]。另一来源[^foundry]。

[^kimi-k26]: Introducing Kimi K2.6 in Microsoft Foundry. 2026-04-22. https://techcommunity.microsoft.com/blog/.../4513125
[^foundry]: Azure AI Foundry Overview. 2026-01-01. https://learn.microsoft.com/foundry
```

- Reference in body: `[^id]`. Definition: `[^id]: <text containing the URL>`.
- The `id` is just a handle; pick a short stable token (e.g. URL-derived) and
  reuse the same id for the same source. The **URL is the deduplication key**.
- Display numbers (1, 2, 3 …) are assigned automatically by first appearance,
  after deduplicating by URL — you never write or maintain numbers yourself.

## Quick Start

```bash
{skill_path}/scripts/docx md2docx <markdown_file> \
    --style <footnote|endnote|hyperlink> \
    -o <exact/output.docx>        # or --output-dir <dir> for auto-named output
    [--clean]                     # remove intermediate .converted.md / .base.docx
    [--no-validate]               # skip the post-build validation (on by default)
```

The result is validated automatically; on success the converter prints
`Conversion complete (validated): <path>`.

**Citation guard**: if the source still uses old-style `[^N^]` markers with no
standard footnote definitions, the converter aborts (rather than emit empty
footnotes). Check a file first with:

```bash
python3 {skill_path}/scripts/md2docx/citation_md.py --check <markdown_file>
```

## Style Selection

| Style | Use Case | Citation Location |
|-------|----------|-------------------|
| **footnote** (default) | Research reports, policy analysis, general reports | Page bottom |
| **endnote** | Academic papers, books, long scholarly documents | End of document |
| **hyperlink** | WPS compatibility | Reference list at end of body |

## Pipeline

```
Markdown (standard footnotes)
    │
    ├─ 1. Parse footnote definitions → {id: text, url}
    ├─ 2. Deduplicate by URL; renumber by first body appearance → Pandoc superscript markers
    ├─ 3. Strip the footnote definition block
    │
    ├─ 4. Pandoc → base.docx
    │
    └─ 5. OOXML post-processing (by style)
         ├─ footnote: first use → footnote object, repeats → NOTEREF
         ├─ endnote:  first use → endnote object,  repeats → NOTEREF
         └─ hyperlink: REF field → bibliography bookmark
```

## Output Files

- `{name}.{style}.docx` — final Word document
- `{name}.converted.md` — intermediate Markdown (`[^id]` replaced by Pandoc superscript markers, definitions removed)
- `{name}.base.docx` — Pandoc raw output (intermediate)

## Technical Details

- **Dedup**: footnotes sharing a URL collapse to one note; the first body use is
  a real note, later uses are NOTEREF cross-references to the same number.
- **Clickable**: superscript numbers link to the corresponding note.
- **Unresolved**: a `[^id]` reference with no definition is left as-is and logged.
- **Strict UTF-8**: the Markdown is read with `encoding='utf-8'`, no fallback.

## Dependencies

- **Pandoc**: `brew install pandoc` / `apt install pandoc`
- **python-docx**: `pip install python-docx`
- **lxml**: `pip install lxml`

## Code Structure

```
scripts/md2docx/
├── md2docx_convert.py   # Main pipeline
├── citation_md.py       # Standard-footnote parser, URL dedup, superscript markers + display_db
├── docx_footnote.py     # Footnote OOXML post-processing (NOTEREF dedup)
├── docx_endnote.py      # Endnote OOXML post-processing (NOTEREF dedup)
├── docx_postprocess.py  # Hyperlink post-processing (python-docx)
└── docx_utils.py        # Shared: rels / content-types / footnote styles
```

## Reference Entry Points

- Overall routing: `../SKILL.md`
- Creating new documents from scratch: `docx-js.md`
