#!/usr/bin/env python3
"""
validate_all.py - Unified validation: element order fix + business rules check
One unzip, two checks

Usage: python validate_all.py <file.docx>

Combines:
  - fix_element_order: Auto-fix XML element ordering issues
  - validate_business_rules: Business rule validation (table grid, image aspect, comments)
"""

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# Import from shared library
from docx_lib import (
    check_comment_anchor_integrity,
    check_comments_integrity,
    check_cjk_run_fonts,
    check_content_types_integrity,
    check_id_uniqueness,
    check_image_aspect_ratio,
    check_namespace_declarations,
    check_relationship_integrity,
    check_section_margins,
    check_table_grid_consistency,
    fix_comment_metadata,
    fix_content_types,
    fix_element_order_in_tree,
    fix_relationship_paths,
    fix_settings,
    fix_table_width_conservative,
    validate_xml_schemas,
)

_DOC_NAMESPACE_REPAIRS = {
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
}


def _collect_root_namespace_declarations(extract_dir):
    """Capture original root xmlns declarations before ElementTree rewrites."""
    declarations = {}
    for rel_path in ("word/document.xml", "word/styles.xml", "word/settings.xml"):
        xml_path = Path(extract_dir) / rel_path
        if not xml_path.exists():
            continue
        try:
            raw = xml_path.read_text(encoding="utf-8")
        except Exception:
            continue
        root_match = re.search(r"<\w+:?\w+\b[^>]*>", raw)
        if not root_match:
            continue
        found = {}
        for match in re.finditer(r'xmlns:([A-Za-z_][\w.-]*)\s*=\s*"([^"]+)"', root_match.group(0)):
            found[match.group(1)] = match.group(2)
        declarations[rel_path] = found
    return declarations


def fix_namespace_declarations(extract_dir, original_declarations=None):
    """Restore root namespace declarations that ET can drop during rewrites."""
    fixes = 0
    original_declarations = original_declarations or {}

    for rel_path in ("word/document.xml", "word/styles.xml", "word/settings.xml"):
        xml_path = Path(extract_dir) / rel_path
        if not xml_path.exists():
            continue

        try:
            raw = xml_path.read_text(encoding="utf-8")
        except Exception:
            continue

        root_match = re.search(r"<\w+:?\w+\b[^>]*>", raw)
        if not root_match:
            continue

        root_tag = root_match.group(0)
        ignorable_prefixes = set()
        try:
            root = ET.parse(xml_path).getroot()
            ignorable_prefixes = set(
                root.get("{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable", "").split()
            )
        except Exception:
            pass
        original_for_file = original_declarations.get(rel_path, {})

        missing = []
        for prefix, uri in _DOC_NAMESPACE_REPAIRS.items():
            if f"xmlns:{prefix}=" in root_tag:
                continue
            should_restore = (
                original_for_file.get(prefix) == uri
                or uri in raw
            )
            if should_restore and (not ignorable_prefixes or prefix in ignorable_prefixes or uri in raw):
                missing.append((prefix, uri))

        if not missing:
            continue

        replacement = root_tag[:-1] + "".join(
            f' xmlns:{prefix}="{uri}"' for prefix, uri in missing
        ) + ">"
        xml_path.write_text(raw.replace(root_tag, replacement, 1), encoding="utf-8")
        fixes += 1

    return fixes


def validate_and_fix(docx_path):
    """
    One unzip, two checks:
    1. Fix element order (modifies XML in place)
    2. Business rule validation (read-only)

    Returns: (fix_count, errors)
    """
    docx_path = Path(docx_path)

    if not docx_path.exists():
        return 0, [f"FILE: not found: {docx_path}"], []

    with tempfile.TemporaryDirectory() as tmpdir:
        extract_dir = Path(tmpdir) / 'extracted'

        # 1. Unzip
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            return 0, ["STRUCTURE: File corrupted or not valid docx"], []

        total_fixes = 0
        errors = []

        required_parts = [
            '[Content_Types].xml',
            '_rels/.rels',
            'word/document.xml',
        ]
        for rel_path in required_parts:
            if not (extract_dir / rel_path).exists():
                errors.append(f"STRUCTURE: missing required part: {rel_path}")

        if errors:
            return total_fixes, errors, []

        original_namespace_declarations = _collect_root_namespace_declarations(extract_dir)

        # 2. Fix element order in XML files
        xml_files = [
            ('word/document.xml', False),
            ('word/styles.xml', False),
            ('word/numbering.xml', False),
            ('word/settings.xml', True),  # needs special handling
        ]

        for rel_path, is_settings in xml_files:
            xml_path = extract_dir / rel_path
            if xml_path.exists():
                try:
                    tree = ET.parse(xml_path)
                except ET.ParseError as exc:
                    errors.append(f"XML: {rel_path}: {exc}")
                    continue
                root = tree.getroot()
                fixes = fix_element_order_in_tree(root)
                if is_settings:
                    fixes += fix_settings(root)
                # Fix table width consistency in document.xml
                if rel_path == 'word/document.xml':
                    fixes += fix_table_width_conservative(root)
                if fixes > 0:
                    tree.write(xml_path, encoding='UTF-8', xml_declaration=True)
                    total_fixes += fixes

        # Fix header/footer files
        word_dir = extract_dir / 'word'
        for xml_file in list(word_dir.glob('header*.xml')) + list(word_dir.glob('footer*.xml')):
            try:
                tree = ET.parse(xml_file)
            except ET.ParseError as exc:
                errors.append(f"XML: {xml_file.relative_to(extract_dir)}: {exc}")
                continue
            root = tree.getroot()
            fixes = fix_element_order_in_tree(root)
            if fixes > 0:
                tree.write(xml_file, encoding='UTF-8', xml_declaration=True)
                total_fixes += fixes

        # 3. OPC package-level fixes (relationship paths + content types)
        total_fixes += fix_relationship_paths(extract_dir)
        total_fixes += fix_content_types(extract_dir)
        total_fixes += fix_comment_metadata(extract_dir)
        total_fixes += fix_content_types(extract_dir)

        # 3b. Fix misplaced media directory (SDK sometimes puts images at /media/ instead of /word/media/)
        root_media = extract_dir / 'media'
        word_media = extract_dir / 'word' / 'media'
        if root_media.is_dir() and not word_media.is_dir():
            import shutil as _shutil
            word_media.mkdir(parents=True, exist_ok=True)
            for f in root_media.iterdir():
                _shutil.move(str(f), str(word_media / f.name))
            root_media.rmdir()
            total_fixes += 1

        total_fixes += fix_namespace_declarations(extract_dir, original_namespace_declarations)

        # 4. Business rule validation
        doc_xml = extract_dir / 'word' / 'document.xml'
        warnings = []
        if doc_xml.exists():
            try:
                tree = ET.parse(doc_xml)
                root = tree.getroot()
            except ET.ParseError as exc:
                errors.append(f"XML: word/document.xml: {exc}")
                root = None
            if root is not None:
                errors.extend(check_table_grid_consistency(root))
                errors.extend(check_image_aspect_ratio(root, extract_dir))
                warnings.extend(check_section_margins(root))
                warnings.extend(check_cjk_run_fonts(root))

        errors.extend(check_content_types_integrity(extract_dir))
        errors.extend(check_relationship_integrity(extract_dir))
        errors.extend(check_comment_anchor_integrity(extract_dir))
        errors.extend(check_comments_integrity(extract_dir))

        # 5. Namespace and ID checks
        errors.extend(check_namespace_declarations(extract_dir))

        if doc_xml.exists():
            try:
                tree = ET.parse(doc_xml)
                root = tree.getroot()
                errors.extend(check_id_uniqueness(root))
            except ET.ParseError:
                pass

        errors.extend(validate_xml_schemas(extract_dir))

        # 6. Repack if fixes were made
        if total_fixes > 0:
            backup_path = docx_path.with_suffix('.docx.bak')
            shutil.copy2(docx_path, backup_path)

            try:
                with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    all_files = [f for f in extract_dir.rglob('*') if f.is_file()]

                    def sort_key(f):
                        rel = str(f.relative_to(extract_dir))
                        if rel == '[Content_Types].xml':
                            return (0, rel)
                        elif rel.startswith('_rels'):
                            return (1, rel)
                        elif rel.startswith('word/_rels'):
                            return (2, rel)
                        else:
                            return (3, rel)

                    for file_path in sorted(all_files, key=sort_key):
                        arcname = file_path.relative_to(extract_dir)
                        zf.write(file_path, arcname)
            except Exception:
                # Repack failed — restore original from backup
                shutil.copy2(backup_path, docx_path)
                backup_path.unlink()
                raise

            backup_path.unlink()

        return total_fixes, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_all.py <file.docx>")
        sys.exit(1)

    docx_path = sys.argv[1]

    fixes, errors, warnings = validate_and_fix(docx_path)

    if fixes:
        print(f"Fixed: applied {fixes} conservative auto-fix(es)")

    for warn in warnings:
        print(f"Warning: {warn}")

    if errors:
        for err in errors:
            print(f"Error: {err}")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
