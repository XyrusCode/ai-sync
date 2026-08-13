---
name: docx
description: "Create, edit, repair, and review Word documents (.docx). Use for docx-js document creation, in-place editing of existing .docx files, comments, tracked changes, and DOCX package validation/auto-repair."
---

# DOCX Skill

## Route

| Task | Route | Read |
|------|-------|------|
| Create a new `.docx` | `docx-js` script, then `{skill_path}/scripts/docx build` | `references/docx-js.md`, then `assets/example.js` |
| Create native Word equations | docx-js plus literal OMML helpers | `references/docx-js.md`, `references/omml.md` |
| Edit text/style in an existing `.docx` | `python-docx` for simple in-place edits | `references/editing.md` |
| Add comments or tracked changes | `DocxContext` editing module | `references/editing.md` |
| Convert swarm-assembled Markdown to `.docx` | `{skill_path}/scripts/docx md2docx <file.md>` | `references/md2docx-reference.md` |
| Validate or repair a `.docx` | `{skill_path}/scripts/docx validate <file.docx>` | this file |

**Output path:** write to the path the user requested. If its directory is not
writable (e.g. a container path like `/mnt/...` that does not exist here), fall
back to `./outputs/` under the current working directory, create it, and report
the final path. Never fail just because a hardcoded absolute directory is
missing.

**When to use `md2docx` (gate):** only for a multi-section Markdown report
assembled by a swarm writing skill — i.e. there is a `*.agent.final.md` or
several `*_sec{NN}.md` files produced by sub-agents, with standard Markdown
footnotes (`[^id]` + `[^id]: Title. Date. URL`) for citations. For a one-off
document the user asks you to write, author it natively with `docx-js` (the
Create route); hand-authored layout is cleaner than converted Markdown.

## Skill Map

```
docx/
├── SKILL.md                 # routing, required commands, validation contract
├── references/
│   ├── docx-js.md           # creation standard: JS skeleton, TOC, visual defaults, few-shots
│   ├── editing.md           # existing-document edits, comments, tracked changes
│   ├── omml.md              # native Word equation patterns and ordering traps
│   └── md2docx-reference.md # swarm Markdown → docx citation pipeline
├── assets/
│   └── example.js           # small build-tested docx-js seed
└── scripts/
    ├── docx                 # only entry point to call
    ├── setup_node_env       # detect Node docx dependency; optional explicit cache install
    ├── lint_docx_js.py      # static checks for docx-js authoring mistakes
    ├── validate_all.py      # repair + validation pipeline
    ├── md2docx/             # Markdown (standard footnotes) → docx citation pipeline
    └── docx_lib/            # OOXML/OPC checks and editing helpers
```

Progressive disclosure:
- New document creation: read `references/docx-js.md` first, then inspect `assets/example.js` before writing code.
- Native equation requirements: also read `references/omml.md`; keep math order explicit.
- Existing `.docx` edits: read `references/editing.md`; do not read creation docs unless rebuilding from scratch.
- Validation failures: use the error text first; read scripts only when changing the skill itself.

## Required Commands

Use the bundled entry point; do not stop after running `node` manually.
`{skill_path}` is the absolute directory containing the `SKILL.md` you just
read. In Kimi CLI, resolve it from the current workspace unless an explicit
skill path is provided:

```bash
DOCX_SKILL_DIR="${KIMI_DOCX_SKILL_DIR:-$(pwd)/.agents/skills/docx}"
```

```bash
# Build from a Node script. The script must write process.argv[2].
"$DOCX_SKILL_DIR/scripts/docx" build /absolute/path/create.js /absolute/path/output.docx

# Validate and auto-repair an existing DOCX package.
"$DOCX_SKILL_DIR/scripts/docx" validate /absolute/path/file.docx

# Run only docx-js static checks.
"$DOCX_SKILL_DIR/scripts/docx" lint /absolute/path/create.js

# Detect whether the script can resolve the docx npm package.
"$DOCX_SKILL_DIR/scripts/setup_node_env" check-docx /absolute/path/dir-containing-create-js
```

`build` runs: JavaScript syntax check -> docx-js lint -> Node generation -> DOCX auto-fix/validation.

`docx-js` does not provide an OpenXML SDK-style official validator. Treat `node --check`, docx-js lint, docx-js generation, bundled OOXML/OPC XSD validation, and the compact package checks below as the validation stack.

Use `{skill_path}/scripts/setup_node_env check-docx <script-dir>` before building. If it reports `MISSING`, run the printed `cd ... && npm install docx`, then rerun the check. `{skill_path}/scripts/docx build` uses the same lookup path: script directory, parent directories, skill directory, `NODE_PATH`, and global npm roots. It also handles ESM `.js` scripts even in a CommonJS workspace; do not edit `package.json` just to switch module type.

For Word tasks, the final artifact must be `.docx`. Markdown, extracted text, and `read_file` output are intermediate notes, not deliverables, unless the user explicitly asks for Markdown.

## Auto-Fix And Validation

The validator unzips the DOCX, applies safe repairs, repacks if needed, then reports remaining findings. Treat `validate` as a mutating repair pass on the final artifact, not a read-only checker.

Output contract:
- `Fixed:` deterministic auto-repairs already applied.
- `Warning:` likely compatible but worth reviewing.
- `Error:` the script or package still needs correction.

Auto-fixes:
- conservative WordprocessingML structure ordering: `sectPr`, property containers, table property/grid placement, `pPr/rPr/tcPr`
- conservative table `tcW` alignment with `tblGrid/gridCol`
- absolute relationship targets converted to relative targets
- `[Content_Types].xml` default/override normalization, including missing `.rels`
- misplaced root `media/` moved to `word/media/`
- old-style comment packages upgraded with missing `commentsExtended.xml`, `commentsIds.xml`, `commentsExtensible.xml`, `people.xml`, relationships, content types, and durable IDs

The repair pass does not reorder sequence-sensitive mixed content such as runs, fields, hyperlinks, comments/bookmarks, tracked changes, drawings, `mc:AlternateContent`, or OMML math.

Hard checks:
- bundled XSD validation for known OOXML/OPC XML roots, with `mc:Ignorable` extensions filtered for schema compatibility
- required package parts and relationship targets
- `[Content_Types].xml` conflicts and missing fixed-part overrides
- table grid consistency
- image display aspect ratio vs actual PNG/JPEG dimensions
- threaded comment file, durable ID, resolved-state, and document-anchor consistency
- `mc:Ignorable` prefixes declared on package XML roots
- duplicate bookmark/comment marker IDs

## Hard Rules

1. Creation uses docx-js, never `python-docx`.
2. Existing-document edits preserve the original file; do not rebuild unless the user asks for a redesign.
3. Comments and tracked changes go through `DocxContext`; do not hand-craft comment XML.
4. In docx-js creation scripts, follow the standard `run(...)` / `para(...)` full-form pattern in `references/docx-js.md`.
5. Formal documents should include a native table of contents unless inappropriate.
6. Use explicit `BookmarkStart`/`BookmarkEnd` for internal link targets; avoid `Bookmark` when there is more than one target.
7. Use absolute paths in scripts and commands.
8. You may inspect skill scripts and installed packages to understand API behavior. Do not patch the skill directory, runtime domain code, or global npm package files as a task fix; fix your generation/edit script, install dependencies in the script/project directory, or use a compatible API pattern.
9. After every create/edit operation, run `{skill_path}/scripts/docx validate` or `{skill_path}/scripts/docx build`.
10. A validation `Error:` is a blocker. Do not claim it is harmless; fix it or report the document as not cleanly validated. `Warning:` may be disclosed separately.
11. When LibreOffice is available, run `{skill_path}/scripts/docx render <file.docx> <output-dir>` and inspect the all-page contact sheet. If no DOCX renderer is available, disclose that visual QA could not be run; never call structure-only validation a rendered visual pass.

## Delivery Checklist

- The final `.docx` exists at the requested path.
- `{skill_path}/scripts/docx build` or `{skill_path}/scripts/docx validate` passes.
- No placeholders remain.
- Output filename matches the topic and the user's language; do not deliver `output.docx`.
- Headers/footers and page numbers are present for formal documents unless inappropriate.
- Formal documents include a TOC unless inappropriate.
- Citations, if used, are real and attached to precise claims with native footnotes.
- When a renderer is available, the rendered contact sheet and every low-content warning have been reviewed.
