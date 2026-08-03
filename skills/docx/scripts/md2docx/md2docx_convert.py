#!/usr/bin/env python3
"""
Markdown → Word conversion pipeline (standard footnotes, no citation.jsonl).

Pipeline: load → footnote preprocessing (parse + URL dedup + ^N^) → Pandoc
          → OOXML post-processing (footnote / endnote / hyperlink) → output docx

The model writes standard Markdown footnotes inline:
    body         [^id]
    definition   [^id]: Title. Date. URL
This pipeline deduplicates by URL, renumbers by appearance, and emits a Word
document where the first use of each source is a real note and subsequent uses
are NOTEREF cross-references.
"""
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from citation_md import analyze, convert_citations_for_docx
from docx_endnote import process_word_document_with_endnotes
from docx_footnote import process_word_document_with_noteref
from docx_postprocess import process_word_document_with_hyperlinks

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STYLES = ('footnote', 'endnote', 'hyperlink')


def _validate(docx_path: str) -> bool:
    """Run the bundled DOCX validator; return True if it exits 0."""
    validator = Path(__file__).resolve().parent.parent / 'validate_all.py'
    if not validator.exists():
        logger.warning("validator not found; skipping validation")
        return True
    res = subprocess.run([sys.executable, str(validator), docx_path],
                         capture_output=True, text=True)
    out = (res.stdout + res.stderr).strip()
    if res.returncode == 0:
        logger.info(f"Validation PASSED: {Path(docx_path).name}")
        if out:
            logger.info(out)
        return True
    logger.error(f"Validation FAILED:\n{out}")
    return False


def convert_md_to_docx(
    md_path: str,
    output_dir: str = None,
    output: str = None,
    style: str = "footnote",
    clean: bool = False,
    validate: bool = True,
    allow_old_markers: bool = False,
) -> str:
    """Full Markdown → Word conversion pipeline.

    Args:
        md_path:     Path to Markdown file (standard footnotes)
        output_dir:  Output directory (None uses same directory as MD file)
        output:      Exact output .docx path (overrides output_dir + auto name)
        style:       footnote / endnote / hyperlink
        clean:       remove intermediate .converted.md / .base.docx afterwards
        validate:    run the bundled validator on the result
        allow_old_markers: do not abort when old-style [^N^] markers are present

    Returns:
        Path to generated docx file
    """
    if style not in STYLES:
        raise ValueError(f"style must be one of {STYLES}, got: {style}")

    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_dir = output_path.parent
    else:
        out_dir = Path(output_dir) if output_dir else md_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"{md_path.stem}.{style}.docx"

    logger.info(f"Document: {md_path.name} | Style: {style}")

    # ── 1. Load (strict UTF-8) ──
    markdown_content = md_path.read_text(encoding='utf-8')

    # ── 1b. Citation health guard ──
    rep = analyze(markdown_content)
    if rep['old_style_markers'] and rep['unique_citations'] == 0 and not allow_old_markers:
        raise RuntimeError(
            "Document uses old-style [^N^] citation markers with no standard "
            f"footnote definitions ({len(rep['old_style_markers'])} markers, e.g. "
            f"{rep['old_style_markers'][:5]}). This would produce empty footnotes. "
            "Fix the source to use standard Markdown footnotes "
            "([^id] + `[^id]: Title. Date. URL`), or pass --allow-old-markers to override."
        )
    if rep['unresolved']:
        logger.warning(
            f"{len(rep['unresolved'])} footnote reference(s) without a definition: "
            f"{rep['unresolved'][:20]}")

    # ── 2. Footnote preprocessing: parse + URL dedup + renumber → ^N^ ──
    converted_md, display_db, warnings = convert_citations_for_docx(markdown_content)
    for w in warnings:
        logger.warning(w)
    logger.info(f"{len(display_db)} unique citation(s) after URL dedup")

    # ── 3. Save intermediate MD (same dir as source to keep image relative paths) ──
    converted_md_path = md_path.parent / f"{md_path.stem}.converted.md"
    converted_md_path.write_text(converted_md, encoding='utf-8')

    # ── 4. Pandoc → base.docx ──
    base_docx_path = out_dir / f"{md_path.stem}.base.docx"
    pandoc_cmd = [
        'pandoc', str(converted_md_path),
        '-o', str(base_docx_path),
        '--from=markdown', '--to=docx',
        f'--resource-path={md_path.parent}',
        '--standalone',
    ]
    result = subprocess.run(pandoc_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Pandoc conversion failed: {result.stderr}")

    # ── 5. OOXML post-processing ──
    processors = {
        'footnote':  process_word_document_with_noteref,
        'endnote':   process_word_document_with_endnotes,
        'hyperlink': process_word_document_with_hyperlinks,
    }
    success = processors[style](str(base_docx_path), str(output_path), citation_db=display_db)
    if not success:
        raise RuntimeError(f"{style} generation failed")
    logger.info(f"Done: {output_path.name}")

    # ── 6. Validate ──
    if validate and not _validate(str(output_path)):
        raise RuntimeError(f"Generated docx failed validation: {output_path}")

    # ── 7. Clean intermediates ──
    if clean:
        for f in (converted_md_path, base_docx_path):
            try:
                f.unlink()
            except OSError:
                pass
        logger.info("Removed intermediate .converted.md / .base.docx")

    return str(output_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Markdown (standard footnotes) → Word with citation cross-references')
    parser.add_argument('md_file', help='Path to Markdown file')
    parser.add_argument('--output-dir', help='Output directory (default: same as MD file)')
    parser.add_argument('-o', '--output', help='Exact output .docx path (overrides --output-dir)')
    parser.add_argument('--style', choices=STYLES, default='footnote',
                        help='Citation style: footnote / endnote / hyperlink')
    parser.add_argument('--clean', action='store_true',
                        help='Remove intermediate .converted.md / .base.docx')
    parser.add_argument('--no-validate', dest='validate', action='store_false',
                        help='Skip the post-build DOCX validation')
    parser.add_argument('--allow-old-markers', action='store_true',
                        help='Do not abort on old-style [^N^] markers')

    args = parser.parse_args()

    try:
        out = convert_md_to_docx(
            args.md_file,
            output_dir=args.output_dir,
            output=args.output,
            style=args.style,
            clean=args.clean,
            validate=args.validate,
            allow_old_markers=args.allow_old_markers,
        )
        print(f"\n{'='*60}\nConversion complete (validated): {out}\n{'='*60}")
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
