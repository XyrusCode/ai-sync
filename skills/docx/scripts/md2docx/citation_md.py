#!/usr/bin/env python3
"""
Standard Markdown footnote → citation preprocessing (docx variant).

Input  : standard Markdown footnotes
             body      [^id]
             definition  [^id]: Title. Date. URL
Output : Markdown where body [^id] are replaced by Pandoc superscripts ^N^
         (footnote definition block stripped), plus a display_db mapping
             {N: {"text": <full definition text>, "url": <extracted url>}}

Numbering rule:
  - Deduplicate by URL: footnotes whose definitions share the same URL collapse
    to one display number.
  - Display numbers N=1,2,3... are assigned by first appearance of a body
    reference (after URL dedup).
  - The id string is only a handle; the URL is the dedup key. Definitions
    without a URL fall back to dedup-by-id.

Robustness:
  - Footnote markers inside fenced code blocks (``` / ~~~) and inline code
    (`...`) are ignored, so code samples are never rewritten.
  - URLs used as the dedup key are stripped of trailing punctuation.

CLI:
  python3 citation_md.py --check <file.md>
      Report citation health (standard defs, URL-bearing defs, unresolved
      old-style markers) and exit non-zero if the document would produce
      empty/broken footnotes.

No citation.jsonl, no global indices — the model writes the source metadata
inline and this module renumbers deterministically.
"""
import logging
import re
import sys

logger = logging.getLogger(__name__)

# A footnote definition line: `[^id]: text...` (id has no `]` or whitespace)
_RE_DEF = re.compile(r'^\[\^([^\]\s]+)\]:\s?(.*)$')
# A body reference: `[^id]` NOT immediately followed by `:` (which marks a def)
_RE_REF = re.compile(r'\[\^([^\]\s]+)\](?!:)')
# URL extractor (dedup key)
_RE_URL = re.compile(r'https?://\S+')
# Code spans to protect: fenced blocks and inline code
_RE_CODE_SPAN = re.compile(r'```.*?```|~~~.*?~~~|``.*?``|`[^`\n]*`', re.DOTALL)
# Fence open/close marker (line-level)
_RE_FENCE = re.compile(r'^\s*(```|~~~)')

_URL_TRAILING = '.,;:!?)]}>"\'、，。；：）】》”’'


def _clean_url(url: str) -> str:
    """Strip trailing punctuation that a greedy \\S+ match may have swallowed."""
    return url.rstrip(_URL_TRAILING)


def _extract_url(text: str) -> str:
    m = _RE_URL.search(text)
    return _clean_url(m.group(0)) if m else ''


def _parse_definitions(lines: list[str]) -> tuple[dict[str, str], set]:
    """Parse footnote definitions, supporting indented continuation lines.

    Lines inside fenced code blocks are skipped (a `[^id]:` inside a code
    sample is not a real definition).

    Returns (id -> full definition text, set of line indices that are part of
    a definition block and should be stripped from the body).
    """
    defs: dict[str, str] = {}
    strip_idx: set = set()

    i = 0
    n = len(lines)
    in_fence = False
    while i < n:
        if _RE_FENCE.match(lines[i]):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        m = _RE_DEF.match(lines[i])
        if not m:
            i += 1
            continue
        fid, first = m.group(1), m.group(2)
        parts = [first.strip()]
        strip_idx.add(i)
        j = i + 1
        # Continuation: indented lines (>=4 spaces or a tab), or blank lines
        # that are followed by more indented content.
        while j < n:
            line = lines[j]
            if line.strip() == '':
                k = j + 1
                while k < n and lines[k].strip() == '':
                    k += 1
                if k < n and (lines[k].startswith('    ') or lines[k].startswith('\t')):
                    strip_idx.update(range(j, k))
                    j = k
                    continue
                break
            if line.startswith('    ') or line.startswith('\t'):
                parts.append(line.strip())
                strip_idx.add(j)
                j += 1
                continue
            break
        text = ' '.join(p for p in parts if p).strip()
        if fid in defs:
            logger.warning(f"Duplicate footnote definition id [^{fid}], keeping first")
        else:
            defs[fid] = text
        i = j

    return defs, strip_idx


def _map_outside_code(text: str, fn):
    """Apply fn to every non-code segment of text; copy code spans verbatim."""
    out = []
    last = 0
    for m in _RE_CODE_SPAN.finditer(text):
        out.append(fn(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(fn(text[last:]))
    return ''.join(out)


def _noncode_segments(text: str) -> list[str]:
    """Return the non-code segments of text, in order."""
    segs = []
    last = 0
    for m in _RE_CODE_SPAN.finditer(text):
        segs.append(text[last:m.start()])
        last = m.end()
    segs.append(text[last:])
    return segs


def _resolve(markdown_content: str):
    """Shared core: parse defs, build body, assign URL-deduped display numbers.

    Returns dict with: body, defs, id_url, id_to_num, display_db, unresolved.
    """
    lines = markdown_content.split('\n')
    defs, strip_idx = _parse_definitions(lines)
    id_url = {fid: _extract_url(text) for fid, text in defs.items()}
    body = '\n'.join(line for idx, line in enumerate(lines) if idx not in strip_idx)

    id_to_num: dict[str, int] = {}
    url_to_num: dict[str, int] = {}
    display_db: dict[int, dict] = {}
    next_num = 1
    unresolved: set = set()

    def _assign(fid: str) -> int:
        nonlocal next_num
        if fid in id_to_num:
            return id_to_num[fid]
        url = id_url.get(fid, '')
        if url and url in url_to_num:
            num = url_to_num[url]
        else:
            num = next_num
            next_num += 1
            display_db[num] = {'text': defs[fid], 'url': url}
            if url:
                url_to_num[url] = num
        id_to_num[fid] = num
        return num

    # Build numbering by first body appearance, skipping code segments.
    for seg in _noncode_segments(body):
        for m in _RE_REF.finditer(seg):
            fid = m.group(1)
            if fid not in defs:
                unresolved.add(fid)
                continue
            _assign(fid)

    return {
        'body': body, 'defs': defs, 'id_url': id_url,
        'id_to_num': id_to_num, 'display_db': display_db, 'unresolved': unresolved,
    }


def convert_citations_for_docx(markdown_content: str) -> tuple[str, dict[int, dict], list[str]]:
    """Convert standard md footnotes to ^N^ superscripts + display_db.

    Returns (converted_markdown, display_db, warnings).
    """
    warnings: list[str] = []
    r = _resolve(markdown_content)

    if not r['defs']:
        logger.info("No footnote definitions found; passing markdown through unchanged")
        return markdown_content, {}, warnings

    if r['unresolved']:
        warnings.append(
            f"{len(r['unresolved'])} footnote reference(s) without a definition, left as-is: "
            f"{sorted(r['unresolved'])[:20]}"
        )

    id_to_num = r['id_to_num']

    def _sub(m):
        fid = m.group(1)
        return f'^{id_to_num[fid]}^' if fid in id_to_num else m.group(0)

    converted = _map_outside_code(r['body'], lambda seg: _RE_REF.sub(_sub, seg))

    logger.info(
        f"Resolved {len(id_to_num)} footnote id(s) into {len(r['display_db'])} unique "
        f"citation(s) after URL dedup"
    )
    return converted, r['display_db'], warnings


def analyze(markdown_content: str) -> dict:
    """Citation-health report used by --check and by the convert guard."""
    r = _resolve(markdown_content)
    defs = r['defs']
    defs_with_url = sum(1 for u in r['id_url'].values() if u)
    # old-style caret markers like [^40^] that resolve to no definition
    old_style = sorted(fid for fid in r['unresolved'] if re.fullmatch(r'\d+\^?', fid))
    return {
        'defs_total': len(defs),
        'defs_with_url': defs_with_url,
        'unique_citations': len(r['display_db']),
        'resolved_refs': len(r['id_to_num']),
        'unresolved': sorted(r['unresolved']),
        'old_style_markers': old_style,
    }


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Standard Markdown footnote citation checker")
    p.add_argument('--check', metavar='FILE', required=True, help='Markdown file to check')
    args = p.parse_args(argv)

    text = open(args.check, encoding='utf-8').read()
    rep = analyze(text)
    print(f"definitions:            {rep['defs_total']}")
    print(f"  with URL:             {rep['defs_with_url']}")
    print(f"unique citations:       {rep['unique_citations']}")
    print(f"resolved references:    {rep['resolved_refs']}")
    print(f"unresolved references:  {len(rep['unresolved'])} {rep['unresolved'][:20]}")
    print(f"old-style [^N^] markers:{len(rep['old_style_markers'])} {rep['old_style_markers'][:20]}")

    problems = []
    if rep['unresolved']:
        problems.append("references without a matching definition")
    if rep['defs_total'] and rep['defs_with_url'] == 0:
        problems.append("no footnote definition contains a URL (URL dedup impossible)")
    if rep['old_style_markers'] and rep['unique_citations'] == 0:
        problems.append("document uses old-style [^N^] markers with no standard definitions")
    if problems:
        print("FAIL: " + "; ".join(problems))
        return 1
    print("OK: citations are standard Markdown footnotes")
    return 0


if __name__ == '__main__':
    sys.exit(main())
