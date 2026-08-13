"""XSD validation for DOCX package XML parts.

This is intentionally small: use OOXML/OPC schemas where they map cleanly,
and leave package graph checks to business_rules.py.
"""

from copy import deepcopy
from pathlib import Path

CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W15_NS = 'http://schemas.microsoft.com/office/word/2012/wordml'
W16CID_NS = 'http://schemas.microsoft.com/office/word/2016/wordml/cid'
W16CEX_NS = 'http://schemas.microsoft.com/office/word/2018/wordml/cex'
MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'

_SCHEMA_BY_ROOT_NS = {
    CT_NS: 'ecma/opc-contentTypes.xsd',
    RELS_NS: 'ecma/opc-relationships.xsd',
    W_NS: 'ISO-IEC29500-4_2016/wml.xsd',
    W15_NS: 'microsoft/wml-2012.xsd',
    W16CID_NS: 'microsoft/wml-cid-2016.xsd',
    W16CEX_NS: 'microsoft/wml-cex-2018.xsd',
}

_SCHEMA_CACHE = {}


def _split_tag(tag):
    if tag.startswith('{') and '}' in tag:
        ns, local = tag[1:].split('}', 1)
        return ns, local
    return '', tag


def _mce_filtered_doc(doc):
    """Return a copy with Markup Compatibility extensions hidden from XSD.

    The bundled ISO WML schemas do not model mc:Ignorable processing. Word and
    docx-js commonly emit w14/w15 extension attributes that are valid through
    MC rules but fail plain XSD validation. Filtering is read-only and does not
    change the package.
    """
    root = deepcopy(doc.getroot())

    ignorable_namespaces = set()
    root_ns, _root_local = _split_tag(root.tag)
    if root_ns == W_NS:
        # WordprocessingML parts commonly carry Office extension attributes
        # such as w14:paraId/w14:textId. Some real-world producers omit a
        # complete mc:Ignorable declaration; filter the known extension
        # namespaces for XSD compatibility and let business checks enforce the
        # package-level invariants.
        ignorable_namespaces.update({W15_NS, W16CID_NS, W16CEX_NS})
        ignorable_namespaces.add('http://schemas.microsoft.com/office/word/2010/wordml')
    for elem in root.iter():
        ignorable = elem.get(f'{{{MC_NS}}}Ignorable')
        if not ignorable:
            continue
        for prefix in ignorable.split():
            ns = elem.nsmap.get(prefix)
            if ns:
                ignorable_namespaces.add(ns)

    for elem in root.iter():
        for attr_name in list(elem.attrib):
            ns, _local = _split_tag(attr_name)
            if ns == MC_NS or ns in ignorable_namespaces:
                del elem.attrib[attr_name]

    for elem in list(root.iter()):
        for child in list(elem):
            ns, local = _split_tag(child.tag)
            if ns != MC_NS or local != 'AlternateContent':
                continue

            replacement_parent = None
            for candidate in list(child):
                candidate_ns, candidate_local = _split_tag(candidate.tag)
                if candidate_ns == MC_NS and candidate_local == 'Fallback':
                    replacement_parent = candidate
                    break
            if replacement_parent is None:
                for candidate in list(child):
                    candidate_ns, candidate_local = _split_tag(candidate.tag)
                    if candidate_ns == MC_NS and candidate_local == 'Choice':
                        replacement_parent = candidate
                        break

            insert_at = list(elem).index(child)
            elem.remove(child)
            if replacement_parent is not None:
                for replacement in list(replacement_parent):
                    elem.insert(insert_at, replacement)
                    insert_at += 1

    for elem in list(root.iter()):
        for child in list(elem):
            ns, _local = _split_tag(child.tag)
            if ns in ignorable_namespaces:
                elem.remove(child)

    from lxml import etree
    return etree.ElementTree(root)


def _schemas_dir():
    return Path(__file__).resolve().parent / 'schemas'


def _get_schema(schema_rel):
    if schema_rel in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_rel]

    try:
        from lxml import etree
    except ImportError:
        _SCHEMA_CACHE[schema_rel] = None
        return None

    schema_path = _schemas_dir() / schema_rel
    schema = etree.XMLSchema(etree.parse(str(schema_path)))
    _SCHEMA_CACHE[schema_rel] = schema
    return schema


def validate_xml_schemas(extract_dir, max_errors_per_part=3):
    """Validate known XML package parts against bundled XSD schemas.

    Returns compact error strings. Unknown XML roots are skipped instead of
    guessed; those are usually custom XML or app-specific extension parts.
    """
    try:
        from lxml import etree
    except ImportError:
        return ["XSD: missing python package 'lxml'"]

    errors = []
    extract_dir = Path(extract_dir)

    for xml_path in sorted(extract_dir.rglob('*.xml')):
        rel = str(xml_path.relative_to(extract_dir)).replace('\\', '/')
        try:
            doc = etree.parse(str(xml_path))
        except etree.XMLSyntaxError as exc:
            errors.append(f"XML: {rel}: {exc.msg}")
            continue

        ns, _local = _split_tag(doc.getroot().tag)
        schema_rel = _SCHEMA_BY_ROOT_NS.get(ns)
        if schema_rel is None:
            continue

        schema = _get_schema(schema_rel)
        if schema is None:
            errors.append("XSD: missing python package 'lxml'")
            continue

        validation_doc = _mce_filtered_doc(doc)

        if schema.validate(validation_doc):
            continue

        for err in list(schema.error_log)[:max_errors_per_part]:
            errors.append(f"XSD: {rel}:{err.line}: {err.message}")

    return errors
