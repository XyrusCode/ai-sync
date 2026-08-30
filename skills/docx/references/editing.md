# Editing Existing DOCX Files

Preserve the existing document package whenever possible. For simple text/style edits use `python-docx`; for comments and tracked changes use the bundled `DocxContext` module. Do not recreate an existing designed document with docx-js unless the user asks for a rebuild.

If the user uploads a DOC/DOCX and asks to edit, comment, revise, annotate, fill a template, or redesign it, treat the original package as the source of truth. `read_file`/Markdown extraction is only an overview; it can drop comments, tracked changes, fields, images, text boxes, headers, footers, footnotes, numbering, and styles.

## Simple In-Place Edits

```python
from docx import Document

doc = Document("/absolute/path/input.docx")

for para in doc.paragraphs:
    if "old text" in para.text:
        for run in para.runs:
            run.text = run.text.replace("old text", "new text")

doc.save("/absolute/path/output.docx")
```

Run validation after saving:

```bash
{skill_path}/scripts/docx validate /absolute/path/output.docx
```

Use `python-docx` for straightforward edits only. It is not a safe route for threaded comments, tracked changes, complex section surgery, or rebuilding a designed document. It may also normalize parts it touches, so keep the edit scoped and validate the output package.

## Comments And Tracked Changes

```python
import sys
sys.path.insert(0, "/absolute/path/docx/scripts")

from docx_lib.editing import (
    DocxContext,
    add_comment, reply_comment, resolve_comment, delete_comment,
    insert_paragraph, insert_text, propose_deletion,
    enable_track_changes,
)

with DocxContext("/absolute/path/input.docx", "/absolute/path/output.docx") as ctx:
    comment_id = add_comment(ctx, "paragraph containing target",
                             "Comment text", highlight="specific phrase")
    reply_comment(ctx, comment_id=comment_id, reply="Noted.")
    resolve_comment(ctx, comment_id=comment_id)

    enable_track_changes(ctx)
    insert_text(ctx, "The method was applied",
                after="method", new_text=" and materials")
    propose_deletion(ctx, "This paragraph should be removed",
                     target="should be removed")
```

Rules:
- `para_text` must uniquely identify one paragraph.
- `highlight`, `after`, and `target` must appear exactly once. If matching is ambiguous, refine the paragraph text or local context; do not guess with fuzzy matching.
- Use the ID returned by `add_comment`; do not assume the new comment is `"0"`.
- `DocxContext` saves and repacks automatically on clean exit.
- Do not hand-edit `comments.xml`, `commentsExtended.xml`, `commentsIds.xml`, `commentsExtensible.xml`, or tracked-change XML. The package needs synchronized IDs, relationships, content types, namespaces, and anchors.
- Ordinary comments, threaded replies, and resolved state are different. Use `add_comment`, `reply_comment`, and `resolve_comment`; do not append reply text into the parent comment body.
- Threaded replies need `commentsExtended.xml` parent links plus durable IDs in `commentsIds.xml`, metadata in `commentsExtensible.xml`, author entries in `people.xml`, and a document anchor at the root comment's range. If validation reports a `COMMENTS:` error, Word may hide the reply or resolved state.
- New tracked changes should use `w:id`, `w:author`, and `w:date`; do not add Office-version extension attributes such as `w16du:dateUtc`.
- `enable_track_changes(ctx)` only turns on the document setting. Visible redlines require actual `<w:ins>` and `<w:del>` elements from helpers such as `insert_text` and `propose_deletion`.
- Run `{skill_path}/scripts/docx validate output.docx` after editing. Validation may repair and repack the output; keep editing from the validated file if another pass is needed.

For review workflows, audit the final package before delivery:

```bash
{skill_path}/scripts/docx validate /absolute/path/output.docx
unzip -p /absolute/path/output.docx word/comments.xml | head
unzip -p /absolute/path/output.docx word/commentsExtended.xml | head
unzip -p /absolute/path/output.docx word/document.xml | grep -E 'w:ins|w:del|commentReference' | head
```

Do not present a file as "replied", "resolved", or "tracked changes complete" if validation still has `Error:` lines.
