"""
business_rules.py - Package checks and conservative fixes not covered by XSD.

Checks:
  - gridCol/tcW width consistency (table not skewed)
  - Image cx/cy proportional scaling (not distorted)
  - Comments file and document anchor sync integrity
  - Section margin heuristic
  - mc:Ignorable namespace consistency
  - Bookmark/comment marker ID uniqueness

Auto-fixes:
  - Absolute → relative relationship paths
  - Content type normalization
"""

import random
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

from .constants import A_NS, R_NS, W14_NS, W15_NS, W_NS, WP_NS

RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
W16CID_NS = 'http://schemas.microsoft.com/office/word/2016/wordml/cid'
W16CEX_NS = 'http://schemas.microsoft.com/office/word/2018/wordml/cex'
OFFICE_DOC_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument'
IMAGE_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
COMMENTS_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
COMMENTS_EXT_REL = 'http://schemas.microsoft.com/office/2011/relationships/commentsExtended'
COMMENTS_IDS_REL = 'http://schemas.microsoft.com/office/2016/09/relationships/commentsIds'
COMMENTS_EXTENSIBLE_REL = 'http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible'
PEOPLE_REL = 'http://schemas.microsoft.com/office/2011/relationships/people'

_LATIN_ONLY_FONT_NAMES = {
    'arial',
    'calibri',
    'cambria',
    'courier new',
    'georgia',
    'helvetica',
    'times new roman',
    'verdana',
}


def _contains_cjk(text):
    return any(
        '\u3400' <= char <= '\u4dbf'
        or '\u4e00' <= char <= '\u9fff'
        or '\uf900' <= char <= '\ufaff'
        for char in text
    )


def check_cjk_run_fonts(root):
    """Warn when an explicitly-fonted CJK run cannot select a CJK face."""
    missing_east_asia = 0
    latin_east_asia = {}
    for run in root.findall('.//{%s}r' % W_NS):
        text = ''.join(node.text or '' for node in run.findall('.//{%s}t' % W_NS))
        if not _contains_cjk(text):
            continue
        run_properties = run.find('{%s}rPr' % W_NS)
        if run_properties is None:
            continue
        fonts = run_properties.find('{%s}rFonts' % W_NS)
        if fonts is None:
            continue
        east_asia = (fonts.get('{%s}eastAsia' % W_NS) or '').strip()
        if not east_asia:
            missing_east_asia += 1
        elif east_asia.casefold() in _LATIN_ONLY_FONT_NAMES:
            latin_east_asia[east_asia] = latin_east_asia.get(east_asia, 0) + 1

    warnings = []
    if missing_east_asia:
        warnings.append(
            f"DOCX_FONT: {missing_east_asia} explicitly-fonted CJK run(s) omit w:eastAsia; "
            "declare a CJK font or verify the intended style inheritance"
        )
    for font_name, count in sorted(latin_east_asia.items()):
        warnings.append(
            f"DOCX_FONT: {count} CJK run(s) explicitly set w:eastAsia='{font_name}', "
            "a Latin-only font; use an explicit CJK eastAsia face"
        )
    return warnings


def check_table_grid_consistency(root):
    """Check table gridCol and tcW width consistency.

    Args:
        root: ElementTree root of document.xml

    Returns:
        List of error strings
    """
    errors = []
    tables = root.findall('.//{%s}tbl' % W_NS)

    for tbl_idx, tbl in enumerate(tables, 1):
        tbl_grid = tbl.find('{%s}tblGrid' % W_NS)
        if tbl_grid is None:
            errors.append(f"TABLE[{tbl_idx}]: missing tblGrid (required for proper rendering)")
            continue

        grid_cols = tbl_grid.findall('{%s}gridCol' % W_NS)
        grid_widths = []
        for gc in grid_cols:
            w_val = gc.get('{%s}w' % W_NS)
            try:
                grid_widths.append(int(w_val) if w_val else None)
            except ValueError:
                grid_widths.append(None)

        first_row = tbl.find('{%s}tr' % W_NS)
        if first_row is None:
            continue

        cells = first_row.findall('{%s}tc' % W_NS)
        col_idx = 0
        for cell in cells:
            if col_idx >= len(grid_widths):
                break
            tc_pr = cell.find('{%s}tcPr' % W_NS)
            if tc_pr is None:
                col_idx += 1
                continue

            tc_w = tc_pr.find('{%s}tcW' % W_NS)
            if tc_w is None:
                col_idx += 1
                continue

            tc_type = tc_w.get('{%s}type' % W_NS)
            if tc_type not in (None, '', 'dxa'):
                col_idx += 1
                continue

            span_count = 1
            grid_span = tc_pr.find('{%s}gridSpan' % W_NS)
            if grid_span is not None:
                try:
                    span_count = int(grid_span.get('{%s}val' % W_NS, '1'))
                except ValueError:
                    span_count = 1

            if col_idx + span_count > len(grid_widths):
                break
            expected_widths = grid_widths[col_idx:col_idx + span_count]
            if any(w is None for w in expected_widths):
                col_idx += span_count
                continue
            expected_width = sum(expected_widths)

            tc_width = tc_w.get('{%s}w' % W_NS)
            if tc_width and expected_width:
                try:
                    tc_width_int = int(tc_width)
                except ValueError:
                    errors.append(f"TABLE[{tbl_idx}]: tc[{col_idx}].tcW is not numeric")
                    col_idx += span_count
                    continue
                if abs(tc_width_int - expected_width) > expected_width * 0.05:
                    errors.append(
                        f"TABLE[{tbl_idx}]: gridCol[{col_idx}..{col_idx + span_count - 1}] sum={expected_width} != tc[{col_idx}].tcW={tc_width_int} (will skew)"
                    )
            col_idx += span_count

    return errors


def _parse_xml(path):
    try:
        return ET.parse(path), None
    except ET.ParseError as exc:
        return None, f"XML: {path.name}: {exc}"


def get_image_dimensions(data):
    """Read actual image dimensions from binary data (supports PNG/JPEG).

    Args:
        data: bytes - Raw image file data

    Returns:
        Tuple (width, height) or (None, None) if unable to parse
    """
    try:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            width, height = struct.unpack('>II', data[16:24])
            return width, height

        if data[:2] == b'\xff\xd8':
            i = 2
            while i < len(data) - 9:
                if data[i] == 0xff:
                    marker = data[i+1]
                    if marker in (0xc0, 0xc2):
                        height, width = struct.unpack('>HH', data[i+5:i+9])
                        return width, height
                    elif marker == 0xd9:
                        break
                    elif marker in (0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0x01, 0x00):
                        i += 2
                    else:
                        length = struct.unpack('>H', data[i+2:i+4])[0]
                        i += 2 + length
                else:
                    i += 1
    except Exception:
        pass
    return None, None


def check_image_aspect_ratio(root, extract_dir):
    """Check if image display dimensions match actual image file aspect ratio.

    Args:
        root: ElementTree root of document.xml
        extract_dir: Path to extracted docx directory

    Returns:
        List of error strings
    """
    errors = []
    extract_dir = Path(extract_dir)

    # Parse document.xml.rels
    rels_map = {}
    rels_path = extract_dir / 'word' / '_rels' / 'document.xml.rels'
    if rels_path.exists():
        rels_tree = ET.parse(rels_path)
        rels_root = rels_tree.getroot()
        for rel in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            rid = rel.get('Id')
            target = rel.get('Target')
            if rid and target:
                if not target.startswith('/'):
                    target = 'word/' + target
                else:
                    target = target[1:]
                rels_map[rid] = target

    drawings = root.findall('.//{%s}drawing' % W_NS)

    for img_idx, drawing in enumerate(drawings, 1):
        extent = drawing.find('.//{%s}extent' % WP_NS)
        if extent is None:
            continue

        cx = extent.get('cx')
        cy = extent.get('cy')
        if not cx or not cy:
            continue

        cx_val = int(cx)
        cy_val = int(cy)
        if cy_val == 0:
            continue

        display_ratio = cx_val / cy_val

        blip = drawing.find('.//{%s}blip' % A_NS)
        if blip is None:
            continue

        embed_id = blip.get('{%s}embed' % R_NS)
        if not embed_id or embed_id not in rels_map:
            continue

        image_path = extract_dir / rels_map[embed_id]
        if not image_path.exists():
            continue

        data = image_path.read_bytes()
        actual_width, actual_height = get_image_dimensions(data)
        if actual_width is None or actual_height is None or actual_height == 0:
            continue

        actual_ratio = actual_width / actual_height

        if abs(display_ratio - actual_ratio) / actual_ratio > 0.05:
            filename = image_path.name
            errors.append(
                f"IMAGE[{img_idx}] {filename}: display={display_ratio:.2f} != actual={actual_ratio:.2f} (distorted)"
            )

    return errors


def check_comments_integrity(extract_dir):
    """Check comments 4-file sync integrity.

    Args:
        extract_dir: Path to extracted docx directory

    Returns:
        List of error strings
    """
    errors = []
    extract_dir = Path(extract_dir)

    has_comments = (extract_dir / 'word' / 'comments.xml').exists()
    has_comments_extended = (extract_dir / 'word' / 'commentsExtended.xml').exists()
    has_comments_ids = (extract_dir / 'word' / 'commentsIds.xml').exists()
    has_comments_extensible = (extract_dir / 'word' / 'commentsExtensible.xml').exists()

    if has_comments:
        comments_tree, parse_error = _parse_xml(extract_dir / 'word' / 'comments.xml')
        if parse_error:
            return [f"XML: word/comments.xml: {parse_error.split(': ', 1)[-1]}"]
        comments_root = comments_tree.getroot()
        comments = comments_root.findall('.//{%s}comment' % W_NS)

        comment_ids = {}
        comment_para_ids = set()
        for idx, comment in enumerate(comments):
            comment_id = comment.get('{%s}id' % W_NS)
            if comment_id:
                if comment_id in comment_ids:
                    errors.append(
                        f"COMMENTS: duplicate comment w:id='{comment_id}' (first at index {comment_ids[comment_id]})"
                    )
                else:
                    comment_ids[comment_id] = idx

            para = comment.find('{%s}p' % W_NS)
            if para is not None:
                para_id = para.get('{%s}paraId' % W14_NS)
                if para_id:
                    comment_para_ids.add(para_id)

        if comment_para_ids:
            if not has_comments_extended:
                errors.append("COMMENTS: has threaded replies but missing commentsExtended.xml")
            if not has_comments_ids:
                errors.append("COMMENTS: has threaded replies but missing commentsIds.xml")

            if has_comments_extended:
                ext_tree, parse_error = _parse_xml(extract_dir / 'word' / 'commentsExtended.xml')
                if parse_error:
                    errors.append(f"XML: word/commentsExtended.xml: {parse_error.split(': ', 1)[-1]}")
                    ext_tree = None
                if ext_tree is not None:
                    ext_root = ext_tree.getroot()
                    ext_para_ids = set()
                    for idx, elem in enumerate(ext_root.findall('.//{%s}commentEx' % W15_NS)):
                        para_id = elem.get('{%s}paraId' % W15_NS)
                        if para_id:
                            if para_id in ext_para_ids:
                                errors.append(f"COMMENTS: duplicate commentsExtended paraId '{para_id}'")
                            else:
                                ext_para_ids.add(para_id)
                    for para_id in sorted(comment_para_ids - ext_para_ids):
                        errors.append(f"COMMENTS: commentsExtended.xml missing paraId '{para_id}'")
                    for para_id in sorted(ext_para_ids - comment_para_ids):
                        errors.append(f"COMMENTS: commentsExtended.xml has orphan paraId '{para_id}'")

                    for elem in ext_root.findall('.//{%s}commentEx' % W15_NS):
                        parent_id = elem.get('{%s}paraIdParent' % W15_NS)
                        if parent_id and parent_id not in comment_para_ids:
                            errors.append(
                                f"COMMENTS: commentsExtended.xml paraIdParent '{parent_id}' has no matching comment"
                            )

            if has_comments_ids:
                ids_tree, parse_error = _parse_xml(extract_dir / 'word' / 'commentsIds.xml')
                if parse_error:
                    errors.append(f"XML: word/commentsIds.xml: {parse_error.split(': ', 1)[-1]}")
                    ids_tree = None
                if ids_tree is not None:
                    ids_root = ids_tree.getroot()
                    ids_para_ids = {
                        elem.get('{%s}paraId' % W16CID_NS)
                        for elem in ids_root.findall('.//{%s}commentId' % W16CID_NS)
                        if elem.get('{%s}paraId' % W16CID_NS)
                    }
                    durable_ids = {}
                    durable_ids_by_para_id = {}
                    for idx, elem in enumerate(ids_root.findall('.//{%s}commentId' % W16CID_NS)):
                        para_id = elem.get('{%s}paraId' % W16CID_NS)
                        durable_id = elem.get('{%s}durableId' % W16CID_NS)
                        if durable_id:
                            if durable_id in durable_ids:
                                errors.append(f"COMMENTS: duplicate durableId '{durable_id}'")
                            else:
                                durable_ids[durable_id] = idx
                            if para_id:
                                durable_ids_by_para_id[para_id] = durable_id
                    for para_id in sorted(comment_para_ids - ids_para_ids):
                        errors.append(f"COMMENTS: commentsIds.xml missing paraId '{para_id}'")
                    for para_id in sorted(ids_para_ids - comment_para_ids):
                        errors.append(f"COMMENTS: commentsIds.xml has orphan paraId '{para_id}'")

                    if has_comments_extensible:
                        cex_tree, parse_error = _parse_xml(extract_dir / 'word' / 'commentsExtensible.xml')
                        if parse_error:
                            errors.append(f"XML: word/commentsExtensible.xml: {parse_error.split(': ', 1)[-1]}")
                        else:
                            cex_ids = set()
                            for elem in cex_tree.getroot().findall('.//{%s}commentExtensible' % W16CEX_NS):
                                durable_id = elem.get('{%s}durableId' % W16CEX_NS)
                                if durable_id:
                                    if durable_id in cex_ids:
                                        errors.append(f"COMMENTS: duplicate commentsExtensible durableId '{durable_id}'")
                                    else:
                                        cex_ids.add(durable_id)
                            known_durable_ids = set(durable_ids)
                            for durable_id in sorted(cex_ids - known_durable_ids):
                                errors.append(f"COMMENTS: commentsExtensible.xml has orphan durableId '{durable_id}'")
                            for durable_id in sorted(known_durable_ids - cex_ids):
                                errors.append(f"COMMENTS: commentsExtensible.xml missing durableId '{durable_id}'")

    return errors


def check_section_margins(root):
    """Check section margins for potential issues.

    Detects:
    - Zero margins on non-cover/backcover sections (likely bug)
    - Last section with zero margins affecting body content

    Args:
        root: ElementTree root of document.xml

    Returns:
        List of warning strings
    """
    warnings = []

    # Find all sectPr elements
    # sectPr can be in: body > sectPr (last section) or p > pPr > sectPr (section breaks)
    body = root.find('.//{%s}body' % W_NS)
    if body is None:
        return warnings

    sections = []

    # Section breaks within paragraphs
    for para in body.findall('.//{%s}p' % W_NS):
        pPr = para.find('{%s}pPr' % W_NS)
        if pPr is not None:
            sectPr = pPr.find('{%s}sectPr' % W_NS)
            if sectPr is not None:
                sections.append(('inline', sectPr))

    # Final section at body end
    final_sectPr = body.find('{%s}sectPr' % W_NS)
    if final_sectPr is not None:
        sections.append(('final', final_sectPr))

    if len(sections) < 2:
        # Single section document, no issue
        return warnings

    # Check each section's margins
    MIN_MARGIN_TWIPS = 360  # 0.25 inch minimum for body content

    for idx, (sect_type, sectPr) in enumerate(sections):
        pgMar = sectPr.find('{%s}pgMar' % W_NS)
        if pgMar is None:
            continue

        # Get margin values
        margins = {
            'top': pgMar.get('{%s}top' % W_NS, '1440'),
            'bottom': pgMar.get('{%s}bottom' % W_NS, '1440'),
            'left': pgMar.get('{%s}left' % W_NS, '1440'),
            'right': pgMar.get('{%s}right' % W_NS, '1440'),
        }

        # Convert to int, handle negative values
        try:
            margin_values = {k: abs(int(v)) for k, v in margins.items()}
        except ValueError:
            continue

        # Check if all margins are zero or very small
        all_zero = all(v < MIN_MARGIN_TWIPS for v in margin_values.values())

        if all_zero:
            # First section (cover) and last section (backcover) can have zero margins
            is_first = (idx == 0)
            is_last = (idx == len(sections) - 1 and sect_type == 'final')

            if is_last and len(sections) > 2:
                # Final section with zero margins might affect preceding content
                # if there are sections between first and last without their own sectPr
                warnings.append(
                    "MARGIN: final section has zero margins - may affect body content if intermediate sections lack sectPr"
                )
            elif not is_first and not is_last:
                # Middle section with zero margins is likely a bug
                warnings.append(
                    f"MARGIN: section[{idx+1}] has zero margins (top={margin_values['top']}, left={margin_values['left']}) - body content may touch page edges"
                )

    return warnings


def check_namespace_declarations(extract_dir):
    """Check that mc:Ignorable namespace prefixes are declared on the root element.

    Args:
        extract_dir: Path to extracted docx directory

    Returns:
        List of error strings
    """
    import re
    errors = []
    extract_dir = Path(extract_dir)

    xml_files = [
        extract_dir / 'word' / 'document.xml',
        extract_dir / 'word' / 'styles.xml',
        extract_dir / 'word' / 'settings.xml',
    ]

    for xml_path in xml_files:
        if not xml_path.exists():
            continue

        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue

        root = tree.getroot()
        ignorable = root.get(f'{{{MC_NS}}}Ignorable', '')
        if not ignorable:
            continue

        # ET doesn't expose xmlns declarations, parse raw XML header
        declared_prefixes = set()
        try:
            raw = xml_path.read_bytes()[:4096].decode('utf-8', errors='replace')
            root_match = re.search(r'<\w+:?\w+\s([^>]+?)/?>', raw)
            if root_match:
                for m in re.finditer(r'xmlns:(\w+)\s*=\s*"[^"]*"', root_match.group(1)):
                    declared_prefixes.add(m.group(1))
        except Exception:
            continue

        for prefix in ignorable.split():
            if prefix not in declared_prefixes:
                fname = xml_path.relative_to(extract_dir)
                errors.append(
                    f"NAMESPACE: {fname} mc:Ignorable lists '{prefix}' but xmlns:{prefix} not declared"
                )

    return errors


def check_id_uniqueness(root):
    """Check that bookmark and comment marker IDs are unique.

    Args:
        root: ElementTree root of document.xml

    Returns:
        List of error strings
    """
    errors = []

    for elem_name in ('bookmarkStart', 'bookmarkEnd', 'commentRangeStart', 'commentRangeEnd', 'commentReference'):
        seen = {}
        for elem in root.iter(f'{{{W_NS}}}{elem_name}'):
            id_val = elem.get(f'{{{W_NS}}}id')
            if id_val is None:
                continue
            if id_val in seen:
                errors.append(
                    f"ID: duplicate {elem_name} w:id='{id_val}' (first at index {seen[id_val]})"
                )
            else:
                seen[id_val] = len(seen)

    return errors


# ============================================================
# OPC package-level auto-fixes
# ============================================================

_PART_CONTENT_TYPES = {
    '/word/document.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
    '/word/styles.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml',
    '/word/settings.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml',
    '/word/numbering.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml',
    '/word/footnotes.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml',
    '/word/endnotes.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml',
    '/word/comments.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml',
    '/word/commentsExtended.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtended+xml',
    '/word/commentsIds.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.commentsIds+xml',
    '/word/commentsExtensible.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtensible+xml',
    '/word/fontTable.xml': 'application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml',
    '/word/theme/theme1.xml': 'application/vnd.openxmlformats-officedocument.theme+xml',
    '/docProps/core.xml': 'application/vnd.openxmlformats-package.core-properties+xml',
    '/docProps/app.xml': 'application/vnd.openxmlformats-officedocument.extended-properties+xml',
}


def fix_relationship_paths(extract_dir):
    """Convert absolute relationship targets to relative paths.

    OOXML (ECMA-376 Part 2) requires relative paths in .rels files.
    Some SDK versions generate absolute paths (starting with '/'),
    which Word rejects but WPS tolerates.

    Returns:
        Number of fixes made
    """
    fixes = 0
    extract_dir = Path(extract_dir)

    for rels_path in extract_dir.rglob('*.rels'):
        try:
            tree = ET.parse(rels_path)
        except ET.ParseError:
            continue

        modified = False
        rels_dir = rels_path.parent.parent

        for rel in tree.getroot():
            if rel.tag != f'{{{RELS_NS}}}Relationship':
                continue

            target = rel.get('Target', '')
            target_mode = rel.get('TargetMode', '')

            if target_mode == 'External' or not target.startswith('/'):
                continue

            abs_path = target[1:]
            try:
                target_full = extract_dir / abs_path
                rel_path = target_full.relative_to(rels_dir)
                new_target = str(rel_path).replace('\\', '/')
            except ValueError:
                new_target = abs_path

            rel.set('Target', new_target)
            modified = True
            fixes += 1

        if modified:
            ET.register_namespace('', RELS_NS)
            tree.write(rels_path, encoding='UTF-8', xml_declaration=True)

    return fixes


def fix_content_types(extract_dir):
    """Normalize [Content_Types].xml: fix Default extension mappings, add missing Overrides.

    Fixes the case where document.main content type is used as the Default
    for all .xml files (non-standard, Word may reject).

    Returns:
        Number of fixes made
    """
    fixes = 0
    extract_dir = Path(extract_dir)
    ct_path = extract_dir / '[Content_Types].xml'

    if not ct_path.exists():
        return 0

    try:
        tree = ET.parse(ct_path)
    except ET.ParseError:
        return 0

    root = tree.getroot()
    modified = False

    specific_part_types = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml',
    }

    for child in list(root):
        if child.tag == f'{{{CT_NS}}}Default':
            ext = child.get('Extension', '').lower()
            ct = child.get('ContentType', '')
            if ext == 'xml' and ct in specific_part_types:
                child.set('ContentType', 'application/xml')
                modified = True
                fixes += 1

    required_defaults = {
        'rels': 'application/vnd.openxmlformats-package.relationships+xml',
        'xml': 'application/xml',
    }
    existing_defaults = {
        child.get('Extension', '').lower(): child
        for child in root
        if child.tag == f'{{{CT_NS}}}Default'
    }
    for ext, expected in required_defaults.items():
        default = existing_defaults.get(ext)
        if default is None:
            default = ET.SubElement(root, f'{{{CT_NS}}}Default')
            default.set('Extension', ext)
            default.set('ContentType', expected)
            modified = True
            fixes += 1
        elif default.get('ContentType') != expected and ext == 'xml':
            default.set('ContentType', expected)
            modified = True
            fixes += 1

    existing_overrides = set()
    for child in root:
        if child.tag == f'{{{CT_NS}}}Override':
            existing_overrides.add(child.get('PartName', ''))

    for file_path in extract_dir.rglob('*.xml'):
        rel = '/' + str(file_path.relative_to(extract_dir)).replace('\\', '/')
        if rel == '/[Content_Types].xml' or '/_rels/' in rel:
            continue
        if rel in existing_overrides:
            continue

        # Static mapping (known fixed-path parts)
        ct = _PART_CONTENT_TYPES.get(rel)

        # Dynamic patterns (numbered parts like header1.xml, footer2.xml)
        if ct is None:
            fname = file_path.name
            if fname.startswith('header') and fname.endswith('.xml'):
                ct = 'application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml'
            elif fname.startswith('footer') and fname.endswith('.xml'):
                ct = 'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml'

        if ct is not None:
            override = ET.SubElement(root, f'{{{CT_NS}}}Override')
            override.set('PartName', rel)
            override.set('ContentType', ct)
            modified = True
            fixes += 1

    if modified:
        ET.register_namespace('', CT_NS)
        tree.write(ct_path, encoding='UTF-8', xml_declaration=True)

    return fixes


def _new_long_hex():
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def _ensure_xml_part(path, root_tag, ns, ignorable_prefix=None):
    if path.exists():
        return False
    root = ET.Element(f'{{{ns}}}{root_tag}')
    if ignorable_prefix:
        root.set(f'{{{MC_NS}}}Ignorable', ignorable_prefix)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding='UTF-8', xml_declaration=True)
    return True


def _ensure_document_relationship(extract_dir, target, rel_type):
    rels_path = Path(extract_dir) / 'word' / '_rels' / 'document.xml.rels'
    if not rels_path.exists():
        rels_path.parent.mkdir(parents=True, exist_ok=True)
        root = ET.Element(f'{{{RELS_NS}}}Relationships')
        ET.ElementTree(root).write(rels_path, encoding='UTF-8', xml_declaration=True)

    tree = ET.parse(rels_path)
    root = tree.getroot()
    existing_types = {rel.get('Type') for rel in root if rel.tag == f'{{{RELS_NS}}}Relationship'}
    existing_targets = {rel.get('Target') for rel in root if rel.tag == f'{{{RELS_NS}}}Relationship'}
    if rel_type in existing_types or target in existing_targets:
        return False

    next_id = 1
    for rel in root:
        rid = rel.get('Id', '')
        if rid.startswith('rId'):
            try:
                next_id = max(next_id, int(rid[3:]) + 1)
            except ValueError:
                pass

    rel = ET.SubElement(root, f'{{{RELS_NS}}}Relationship')
    rel.set('Id', f'rId{next_id}')
    rel.set('Type', rel_type)
    rel.set('Target', target)
    ET.register_namespace('', RELS_NS)
    tree.write(rels_path, encoding='UTF-8', xml_declaration=True)
    return True


def fix_comment_metadata(extract_dir):
    """Backfill deterministic modern comment companion metadata.

    This is safe when a document already has comments.xml: it does not move
    anchors or alter comment text. It only gives each comment paragraph the
    metadata Word needs for resolved state and threaded replies.
    """
    fixes = 0
    extract_dir = Path(extract_dir)
    comments_path = extract_dir / 'word' / 'comments.xml'
    if not comments_path.exists():
        return 0

    try:
        comments_tree = ET.parse(comments_path)
    except ET.ParseError:
        return 0

    comments_root = comments_tree.getroot()
    records = []
    comments_modified = False

    for comment in comments_root.findall(f'{{{W_NS}}}comment'):
        paras = comment.findall(f'{{{W_NS}}}p')
        if not paras:
            para = ET.SubElement(comment, f'{{{W_NS}}}p')
            paras = [para]
            comments_modified = True
            fixes += 1
        primary_para = paras[-1]
        for para in paras:
            if not para.get(f'{{{W14_NS}}}paraId'):
                para.set(f'{{{W14_NS}}}paraId', _new_long_hex())
                comments_modified = True
                fixes += 1
            if not para.get(f'{{{W14_NS}}}textId'):
                para.set(f'{{{W14_NS}}}textId', _new_long_hex())
                comments_modified = True
                fixes += 1
        records.append({
            'para_id': primary_para.get(f'{{{W14_NS}}}paraId'),
            'author': comment.get(f'{{{W_NS}}}author'),
            'date': comment.get(f'{{{W_NS}}}date'),
        })

    if comments_modified:
        ET.register_namespace('w', W_NS)
        ET.register_namespace('w14', W14_NS)
        comments_tree.write(comments_path, encoding='UTF-8', xml_declaration=True)

    if not records:
        return fixes

    word_dir = extract_dir / 'word'
    if _ensure_xml_part(word_dir / 'commentsExtended.xml', 'commentsEx', W15_NS, 'w15'):
        fixes += 1
    if _ensure_xml_part(word_dir / 'commentsIds.xml', 'commentsIds', W16CID_NS, 'w16cid'):
        fixes += 1
    if _ensure_xml_part(word_dir / 'commentsExtensible.xml', 'commentsExtensible', W16CEX_NS, 'w16cex'):
        fixes += 1
    if _ensure_xml_part(word_dir / 'people.xml', 'people', W15_NS, 'w15'):
        fixes += 1

    if _ensure_document_relationship(extract_dir, 'comments.xml', COMMENTS_REL):
        fixes += 1
    if _ensure_document_relationship(extract_dir, 'commentsExtended.xml', COMMENTS_EXT_REL):
        fixes += 1
    if _ensure_document_relationship(extract_dir, 'commentsIds.xml', COMMENTS_IDS_REL):
        fixes += 1
    if _ensure_document_relationship(extract_dir, 'commentsExtensible.xml', COMMENTS_EXTENSIBLE_REL):
        fixes += 1
    if _ensure_document_relationship(extract_dir, 'people.xml', PEOPLE_REL):
        fixes += 1

    ext_path = word_dir / 'commentsExtended.xml'
    try:
        ext_tree = ET.parse(ext_path)
        ext_root = ext_tree.getroot()
        ext_para_ids = {
            elem.get(f'{{{W15_NS}}}paraId')
            for elem in ext_root.findall(f'{{{W15_NS}}}commentEx')
            if elem.get(f'{{{W15_NS}}}paraId')
        }
        ext_modified = False
        for record in records:
            para_id = record['para_id']
            if para_id and para_id not in ext_para_ids:
                elem = ET.SubElement(ext_root, f'{{{W15_NS}}}commentEx')
                elem.set(f'{{{W15_NS}}}paraId', para_id)
                elem.set(f'{{{W15_NS}}}done', '0')
                ext_para_ids.add(para_id)
                ext_modified = True
                fixes += 1
        if ext_modified:
            ET.register_namespace('w15', W15_NS)
            ext_tree.write(ext_path, encoding='UTF-8', xml_declaration=True)
    except ET.ParseError:
        pass

    ids_path = word_dir / 'commentsIds.xml'
    durable_by_para = {}
    try:
        ids_tree = ET.parse(ids_path)
        ids_root = ids_tree.getroot()
        durable_ids = set()
        for elem in ids_root.findall(f'{{{W16CID_NS}}}commentId'):
            para_id = elem.get(f'{{{W16CID_NS}}}paraId')
            durable_id = elem.get(f'{{{W16CID_NS}}}durableId')
            if para_id and durable_id:
                durable_by_para[para_id] = durable_id
                durable_ids.add(durable_id)
        ids_modified = False
        for record in records:
            para_id = record['para_id']
            if not para_id or para_id in durable_by_para:
                continue
            durable_id = _new_long_hex()
            while durable_id in durable_ids:
                durable_id = _new_long_hex()
            elem = ET.SubElement(ids_root, f'{{{W16CID_NS}}}commentId')
            elem.set(f'{{{W16CID_NS}}}paraId', para_id)
            elem.set(f'{{{W16CID_NS}}}durableId', durable_id)
            durable_by_para[para_id] = durable_id
            durable_ids.add(durable_id)
            ids_modified = True
            fixes += 1
        if ids_modified:
            ET.register_namespace('w16cid', W16CID_NS)
            ids_tree.write(ids_path, encoding='UTF-8', xml_declaration=True)
    except ET.ParseError:
        pass

    extensible_path = word_dir / 'commentsExtensible.xml'
    try:
        cex_tree = ET.parse(extensible_path)
        cex_root = cex_tree.getroot()
        cex_durable_ids = {
            elem.get(f'{{{W16CEX_NS}}}durableId')
            for elem in cex_root.findall(f'{{{W16CEX_NS}}}commentExtensible')
            if elem.get(f'{{{W16CEX_NS}}}durableId')
        }
        cex_modified = False
        for record in records:
            durable_id = durable_by_para.get(record['para_id'])
            if not durable_id or durable_id in cex_durable_ids:
                continue
            elem = ET.SubElement(cex_root, f'{{{W16CEX_NS}}}commentExtensible')
            elem.set(f'{{{W16CEX_NS}}}durableId', durable_id)
            if record.get('date'):
                elem.set(f'{{{W16CEX_NS}}}dateUtc', record['date'])
            cex_durable_ids.add(durable_id)
            cex_modified = True
            fixes += 1
        if cex_modified:
            ET.register_namespace('w16cex', W16CEX_NS)
            cex_tree.write(extensible_path, encoding='UTF-8', xml_declaration=True)
    except ET.ParseError:
        pass

    people_path = word_dir / 'people.xml'
    try:
        people_tree = ET.parse(people_path)
        people_root = people_tree.getroot()
        existing_authors = {
            person.get(f'{{{W15_NS}}}author')
            for person in people_root.findall(f'{{{W15_NS}}}person')
        }
        people_modified = False
        for record in records:
            author = record.get('author')
            if author and author not in existing_authors:
                person = ET.SubElement(people_root, f'{{{W15_NS}}}person')
                person.set(f'{{{W15_NS}}}author', author)
                existing_authors.add(author)
                people_modified = True
                fixes += 1
        if people_modified:
            ET.register_namespace('w15', W15_NS)
            people_tree.write(people_path, encoding='UTF-8', xml_declaration=True)
    except ET.ParseError:
        pass

    return fixes


def _relationship_target_path(extract_dir, rels_path, target):
    if target.startswith('/'):
        return Path(extract_dir) / target.lstrip('/')
    source_dir = rels_path.parent.parent
    return source_dir / target


def _parse_relationships(rels_path):
    tree = ET.parse(rels_path)
    root = tree.getroot()
    return [
        rel for rel in root.findall(f'{{{RELS_NS}}}Relationship')
    ]


def _relationship_type_set(rels_path):
    try:
        return {
            rel.get('Type')
            for rel in _parse_relationships(rels_path)
            if rel.get('Type')
        }
    except ET.ParseError as exc:
        return {f'__PARSE_ERROR__:{exc}'}


def check_content_types_integrity(extract_dir):
    """Check OPC content types not covered by individual part schemas."""
    errors = []
    extract_dir = Path(extract_dir)
    ct_path = extract_dir / '[Content_Types].xml'
    try:
        tree = ET.parse(ct_path)
    except ET.ParseError as exc:
        return [f"CONTENT_TYPES: malformed [Content_Types].xml: {exc}"]

    root = tree.getroot()
    defaults = {}
    overrides = {}
    conflicting_overrides = set()

    for child in root:
        if child.tag == f'{{{CT_NS}}}Default':
            ext = child.get('Extension')
            ctype = child.get('ContentType')
            if not ext or not ctype:
                continue
            low_ext = ext.lower()
            old = defaults.get(low_ext)
            if old is not None and old != ctype:
                errors.append(f"CONTENT_TYPES: conflicting Default for .{low_ext}")
            defaults[low_ext] = ctype
        elif child.tag == f'{{{CT_NS}}}Override':
            part_name = child.get('PartName')
            ctype = child.get('ContentType')
            if not part_name or not ctype:
                continue
            old = overrides.get(part_name)
            if old is not None and old != ctype:
                errors.append(f"CONTENT_TYPES: conflicting Override for {part_name}")
                conflicting_overrides.add(part_name)
            overrides[part_name] = ctype

    required_defaults = {
        'rels': 'application/vnd.openxmlformats-package.relationships+xml',
        'xml': 'application/xml',
    }
    for ext, expected in required_defaults.items():
        if defaults.get(ext) != expected:
            errors.append(f"CONTENT_TYPES: missing Default .{ext}={expected}")

    for part_name, expected in _PART_CONTENT_TYPES.items():
        if part_name in conflicting_overrides:
            continue
        if (extract_dir / part_name.lstrip('/')).exists() and overrides.get(part_name) != expected:
            errors.append(f"CONTENT_TYPES: missing Override {part_name}")

    return errors


def check_relationship_integrity(extract_dir):
    """Check OPC relationship graph consistency."""
    errors = []
    extract_dir = Path(extract_dir)

    root_rels = extract_dir / '_rels' / '.rels'
    try:
        root_relationships = _parse_relationships(root_rels)
    except ET.ParseError as exc:
        return [f"RELATIONSHIP: malformed _rels/.rels: {exc}"]

    office_targets = [
        rel.get('Target')
        for rel in root_relationships
        if rel.get('Type') == OFFICE_DOC_REL
    ]
    if not office_targets:
        errors.append("RELATIONSHIP: _rels/.rels missing officeDocument relationship")

    document_rels = extract_dir / 'word' / '_rels' / 'document.xml.rels'
    if document_rels.exists():
        rel_types = _relationship_type_set(document_rels)
        if any(t.startswith('__PARSE_ERROR__:') for t in rel_types):
            parse_error = next(t.split(':', 1)[1] for t in rel_types if t.startswith('__PARSE_ERROR__:'))
            errors.append(f"RELATIONSHIP: malformed word/_rels/document.xml.rels: {parse_error}")
        else:
            required_document_rels = []
            if (extract_dir / 'word' / 'comments.xml').exists():
                required_document_rels.append(COMMENTS_REL)
            if (extract_dir / 'word' / 'commentsExtended.xml').exists():
                required_document_rels.append(COMMENTS_EXT_REL)
            if (extract_dir / 'word' / 'commentsIds.xml').exists():
                required_document_rels.append(COMMENTS_IDS_REL)
            if (extract_dir / 'word' / 'commentsExtensible.xml').exists():
                required_document_rels.append(COMMENTS_EXTENSIBLE_REL)
            if (extract_dir / 'word' / 'people.xml').exists():
                required_document_rels.append(PEOPLE_REL)

            for rel_type in required_document_rels:
                if rel_type not in rel_types:
                    short_name = rel_type.rsplit('/', 1)[-1]
                    errors.append(f"RELATIONSHIP: word/document.xml.rels missing {short_name} relationship")

    for rels_path in sorted(extract_dir.rglob('*.rels')):
        rel_display = str(rels_path.relative_to(extract_dir)).replace('\\', '/')
        try:
            relationships = _parse_relationships(rels_path)
        except ET.ParseError as exc:
            errors.append(f"RELATIONSHIP: malformed {rel_display}: {exc}")
            continue

        seen_ids = {}
        for idx, rel in enumerate(relationships):
            rid = rel.get('Id')
            rel_type = rel.get('Type', '')
            target = rel.get('Target', '')
            target_mode = rel.get('TargetMode', '')

            if rid:
                if rid in seen_ids:
                    errors.append(f"RELATIONSHIP: {rel_display} duplicate Id '{rid}'")
                else:
                    seen_ids[rid] = idx

            if not target:
                errors.append(f"RELATIONSHIP: {rel_display} {rid or '<no id>'} missing Target")
                continue

            if target_mode == 'External':
                if rel_type == IMAGE_REL:
                    errors.append(f"RELATIONSHIP: {rel_display} {rid or '<no id>'} external image target")
                continue

            if rel_type == IMAGE_REL and Path(target).suffix.lower() == '.undefined':
                errors.append(
                    f"IMAGE: {rel_display} {rid or '<no id>'} target has .undefined extension; set ImageRun type"
                )

            target_path = _relationship_target_path(extract_dir, rels_path, target)
            resolved_extract_dir = extract_dir.resolve()
            resolved_target_path = target_path.resolve(strict=False)
            try:
                resolved_target_path.relative_to(resolved_extract_dir)
            except ValueError:
                errors.append(f"RELATIONSHIP: {rel_display} {rid or '<no id>'} target escapes package")
                continue

            if not target_path.exists():
                errors.append(f"RELATIONSHIP: {rel_display} {rid or '<no id>'} missing target {target}")

    return errors


def check_comment_anchor_integrity(extract_dir):
    """Check document comment anchors against comments.xml."""
    errors = []
    extract_dir = Path(extract_dir)
    doc_path = extract_dir / 'word' / 'document.xml'
    comments_path = extract_dir / 'word' / 'comments.xml'

    try:
        doc_tree = ET.parse(doc_path)
    except ET.ParseError as exc:
        return [f"XML: word/document.xml: {exc}"]

    root = doc_tree.getroot()
    starts = [e.get(f'{{{W_NS}}}id') for e in root.iter(f'{{{W_NS}}}commentRangeStart')]
    ends = [e.get(f'{{{W_NS}}}id') for e in root.iter(f'{{{W_NS}}}commentRangeEnd')]
    refs = [e.get(f'{{{W_NS}}}id') for e in root.iter(f'{{{W_NS}}}commentReference')]
    marker_ids = set(i for i in starts + ends + refs if i is not None)

    if marker_ids and not comments_path.exists():
        errors.append("COMMENTS: document has comment markers but missing comments.xml")
        return errors

    comment_ids = set()
    comment_para_ids_by_id = {}
    if comments_path.exists():
        try:
            comments_tree = ET.parse(comments_path)
        except ET.ParseError as exc:
            errors.append(f"XML: word/comments.xml: {exc}")
            comments_tree = None
        if comments_tree is not None:
            comment_ids = {
                elem.get(f'{{{W_NS}}}id')
                for elem in comments_tree.getroot().findall(f'.//{{{W_NS}}}comment')
                if elem.get(f'{{{W_NS}}}id') is not None
            }
            for elem in comments_tree.getroot().findall(f'.//{{{W_NS}}}comment'):
                comment_id = elem.get(f'{{{W_NS}}}id')
                para = elem.find(f'{{{W_NS}}}p')
                if comment_id is not None and para is not None:
                    para_id = para.get(f'{{{W14_NS}}}paraId')
                    if para_id:
                        comment_para_ids_by_id[comment_id] = para_id

    reply_para_ids = set()
    comments_extended_path = extract_dir / 'word' / 'commentsExtended.xml'
    if comments_extended_path.exists():
        try:
            ext_tree = ET.parse(comments_extended_path)
        except ET.ParseError as exc:
            errors.append(f"XML: word/commentsExtended.xml: {exc}")
        else:
            for elem in ext_tree.getroot().findall(f'.//{{{W15_NS}}}commentEx'):
                if elem.get(f'{{{W15_NS}}}paraIdParent'):
                    para_id = elem.get(f'{{{W15_NS}}}paraId')
                    if para_id:
                        reply_para_ids.add(para_id)

    reply_comment_ids = {
        comment_id
        for comment_id, para_id in comment_para_ids_by_id.items()
        if para_id in reply_para_ids
    }

    for comment_id in sorted(set(starts) - set(ends)):
        if comment_id is not None:
            errors.append(f"COMMENTS: commentRangeStart id '{comment_id}' has no end")
    for comment_id in sorted(set(ends) - set(starts)):
        if comment_id is not None:
            errors.append(f"COMMENTS: commentRangeEnd id '{comment_id}' has no start")
    for comment_id in sorted(marker_ids - comment_ids):
        errors.append(f"COMMENTS: document references missing comment id '{comment_id}'")
    for comment_id in sorted(reply_comment_ids - marker_ids):
        errors.append(
            f"COMMENTS: threaded reply comment id '{comment_id}' has no document anchor; Word may hide the reply"
        )
    for comment_id in sorted(comment_ids - marker_ids - reply_comment_ids):
        errors.append(f"COMMENTS: comments.xml has orphan comment id '{comment_id}'")

    return errors
