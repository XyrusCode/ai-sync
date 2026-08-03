"""
element_order.py — conservative element ordering fixes for OpenXML documents.

Ordering rules are read from ECMA-376 / ISO 29500 XSD schema files, but they are
only applied to structure/property containers where reordering cannot change the
visible document sequence. Repeated XSD choices such as paragraph runs, fields,
hyperlinks, tracked changes, and OMML math are intentionally left untouched.

Public API:
  - fix_element_order_in_tree(root) — apply conservative order fixes
  - fix_settings(root) — reorder settings.xml
  - fix_body_order(body_element) — move sectPr to end of body
  - wrap_border_elements(ppr_element) — wrap misplaced borders into pBdr
  - fix_table_width_conservative(root) — align tcW with gridCol widths
  - reorder_children(parent, order_list) — generic child reordering
  - get_local_name(element) — strip namespace from tag
"""

from pathlib import Path
from xml.etree import ElementTree as ET

from .constants import W_NS, w

# ============================================================
# XSD schema parsing — builds ordering rules from XSD files
# ============================================================

_XSD_NS = 'http://www.w3.org/2001/XMLSchema'


def _xsd(tag):
    return f'{{{_XSD_NS}}}{tag}'


class _XsdParser:
    """Parse XSD files and extract element ordering rules."""

    def __init__(self):
        self.types = {}        # {(ns, type_name): (ct_element, target_ns, prefix_map)}
        self.groups = {}       # {(ns, group_name): (group_element, target_ns, prefix_map)}
        self.elements = {}     # {(ns, elem_name): type_name}
        self.type_to_elem = {} # {(ns, type_name): elem_name}

    def _load_xsd(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        target_ns = root.get('targetNamespace', '')

        prefix_map = {}
        for attr, val in root.attrib.items():
            if attr.startswith('{http://www.w3.org/2000/xmlns/}') or attr.startswith('xmlns:'):
                prefix = attr.split('}')[-1] if '}' in attr else attr.split(':')[-1]
                prefix_map[prefix] = val
            elif attr == 'xmlns':
                prefix_map[''] = val

        for ct in root.findall(_xsd('complexType')):
            name = ct.get('name')
            if name:
                self.types[(target_ns, name)] = (ct, target_ns, prefix_map)

        for grp in root.findall(_xsd('group')):
            name = grp.get('name')
            if name:
                self.groups[(target_ns, name)] = (grp, target_ns, prefix_map)

        for elem in root.findall(_xsd('element')):
            name = elem.get('name')
            type_name = elem.get('type')
            if name and type_name:
                self.elements[(target_ns, name)] = type_name
                if ':' in type_name:
                    prefix, local = type_name.split(':', 1)
                    type_ns = prefix_map.get(prefix, target_ns)
                    self.type_to_elem[(type_ns, local)] = name
                else:
                    self.type_to_elem[(target_ns, type_name)] = name

        for ct in root.findall(_xsd('complexType')):
            self._collect_inline_elements(ct, target_ns, prefix_map)

    def _resolve_ref(self, ref_str, default_ns, prefix_map):
        if ':' in ref_str:
            prefix, local = ref_str.split(':', 1)
            ns = prefix_map.get(prefix, default_ns)
            return (ns, local)
        return (default_ns, ref_str)

    def _collect_inline_elements(self, parent_elem, target_ns, prefix_map):
        for child in parent_elem:
            if child.tag == _xsd('element'):
                name = child.get('name')
                type_name = child.get('type')
                if name and type_name:
                    if ':' in type_name:
                        prefix, local = type_name.split(':', 1)
                        type_ns = prefix_map.get(prefix, target_ns)
                    else:
                        type_ns = target_ns
                        local = type_name
                    key = (type_ns, local)
                    if key not in self.type_to_elem:
                        self.type_to_elem[key] = name
            if child.tag in (_xsd('sequence'), _xsd('choice'), _xsd('all'),
                             _xsd('complexContent'), _xsd('extension'),
                             _xsd('complexType'), _xsd('group')):
                self._collect_inline_elements(child, target_ns, prefix_map)

    def _extract_sequence(self, container, target_ns, prefix_map, depth=0):
        if depth > 20:
            return []
        results = []
        for child in container:
            tag = child.tag
            if tag == _xsd('element'):
                name = child.get('name')
                ref = child.get('ref')
                if name:
                    results.append(name)
                elif ref:
                    _, local = self._resolve_ref(ref, target_ns, prefix_map)
                    results.append(local)
            elif tag == _xsd('sequence'):
                results.extend(self._extract_sequence(child, target_ns, prefix_map, depth + 1))
            elif tag == _xsd('choice'):
                results.extend(self._extract_choice(child, target_ns, prefix_map, depth + 1))
            elif tag == _xsd('group'):
                ref = child.get('ref')
                if ref:
                    ns, local = self._resolve_ref(ref, target_ns, prefix_map)
                    key = (ns, local)
                    if key in self.groups:
                        grp_elem, grp_ns, grp_pm = self.groups[key]
                        for gc in grp_elem:
                            if gc.tag in (_xsd('sequence'), _xsd('choice'), _xsd('all')):
                                results.extend(self._extract_sequence(gc, grp_ns, grp_pm, depth + 1))
        return results

    def _extract_choice(self, choice_elem, target_ns, prefix_map, depth=0):
        if depth > 20:
            return []
        results = []
        for child in choice_elem:
            tag = child.tag
            if tag == _xsd('element'):
                name = child.get('name')
                ref = child.get('ref')
                if name:
                    results.append(name)
                elif ref:
                    _, local = self._resolve_ref(ref, target_ns, prefix_map)
                    results.append(local)
            elif tag == _xsd('sequence'):
                results.extend(self._extract_sequence(child, target_ns, prefix_map, depth + 1))
            elif tag == _xsd('group'):
                ref = child.get('ref')
                if ref:
                    ns, local = self._resolve_ref(ref, target_ns, prefix_map)
                    key = (ns, local)
                    if key in self.groups:
                        grp_elem, grp_ns, grp_pm = self.groups[key]
                        for gc in grp_elem:
                            if gc.tag in (_xsd('sequence'), _xsd('choice'), _xsd('all')):
                                results.extend(self._extract_sequence(gc, grp_ns, grp_pm, depth + 1))
            elif tag == _xsd('choice'):
                results.extend(self._extract_choice(child, target_ns, prefix_map, depth + 1))
        return results

    def _get_type_order(self, ct_elem, target_ns, prefix_map):
        seq = ct_elem.find(_xsd('sequence'))
        if seq is not None:
            return self._extract_sequence(seq, target_ns, prefix_map)
        cc = ct_elem.find(_xsd('complexContent'))
        if cc is not None:
            ext = cc.find(_xsd('extension'))
            if ext is not None:
                base = ext.get('base')
                base_order = []
                if base:
                    ns, local = self._resolve_ref(base, target_ns, prefix_map)
                    key = (ns, local)
                    if key in self.types:
                        base_ct, base_ns, base_pm = self.types[key]
                        base_order = self._get_type_order(base_ct, base_ns, base_pm)
                ext_seq = ext.find(_xsd('sequence'))
                ext_order = []
                if ext_seq is not None:
                    ext_order = self._extract_sequence(ext_seq, target_ns, prefix_map)
                return base_order + ext_order
        choice = ct_elem.find(_xsd('choice'))
        if choice is not None:
            return self._extract_choice(choice, target_ns, prefix_map)
        return []

    def _type_to_element_name(self, ns, type_name):
        key = (ns, type_name)
        if key in self.type_to_elem:
            return self.type_to_elem[key]
        if type_name.startswith('CT_'):
            raw = type_name[3:]
            if raw:
                return raw[0].lower() + raw[1:]
        return None

    def _generate_orders(self):
        all_orders = {}
        for (ns, type_name), (ct_elem, target_ns, prefix_map) in self.types.items():
            order = self._get_type_order(ct_elem, target_ns, prefix_map)
            if not order:
                continue
            seen = set()
            unique = []
            for name in order:
                if name not in seen:
                    seen.add(name)
                    unique.append(name)
            if len(unique) < 2:
                continue
            elem_name = self._type_to_element_name(ns, type_name)
            if elem_name:
                if ns not in all_orders:
                    all_orders[ns] = {}
                all_orders[ns][elem_name] = unique
        return all_orders


def _parse_xsd_orders():
    """Load XSD files from schemas/ and return ordering rules.

    Returns {namespace_uri: {element_name: [child_names_in_order]}}.
    Returns empty dict if schemas directory is missing.
    """
    schemas_dir = Path(__file__).resolve().parent / 'schemas'
    if not schemas_dir.is_dir():
        return {}

    xsd_files = sorted(schemas_dir.glob('**/*.xsd'))
    if not xsd_files:
        return {}

    parser = _XsdParser()
    for xsd_file in xsd_files:
        try:
            parser._load_xsd(xsd_file)
        except Exception:
            continue

    orders = parser._generate_orders()

    # Fix known type → element name mapping issues.
    # XSD complexType naming convention (CT_Row → row) doesn't always match
    # the actual XML element name (tr). These are the known corrections.
    _WML_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    _NAME_FIXES = {'row': 'tr'}
    if _WML_NS in orders:
        wml = orders[_WML_NS]
        for wrong, right in _NAME_FIXES.items():
            if wrong in wml and right not in wml:
                wml[right] = wml.pop(wrong)

    return orders


# Module-level: prefer pre-built cache (compiled mode), fall back to XSD parsing (source mode)
def _load_orders():
    try:
        from ._xsd_cache import ORDERS
        return ORDERS
    except ImportError:
        return _parse_xsd_orders()


ORDERS = _load_orders()


# ============================================================
# Helper functions
# ============================================================

def get_local_name(element):
    """Extract local name from {namespace}tag format."""
    tag = element.tag
    if tag.startswith('{'):
        return tag.split('}')[1]
    return tag


def reorder_children(parent, order_list):
    """Reorder children of parent element according to order_list.

    Children not in order_list are placed at the end in original order.
    Returns True if any reordering was done.
    """
    children = list(parent)
    if not children:
        return False

    order_map = {name: i for i, name in enumerate(order_list)}

    def sort_key(elem):
        local_name = get_local_name(elem)
        if local_name in order_map:
            return (0, order_map[local_name])
        return (1, children.index(elem))

    sorted_children = sorted(children, key=sort_key)

    if [id(c) for c in children] == [id(c) for c in sorted_children]:
        return False

    for child in children:
        parent.remove(child)
    for child in sorted_children:
        parent.append(child)

    return True


def _move_child_to_front(parent, child_name):
    """Move a named child to the front of its parent, preserving all other order."""
    children = list(parent)
    for i, child in enumerate(children):
        if get_local_name(child) == child_name:
            if i == 0:
                return False
            parent.remove(child)
            parent.insert(0, child)
            return True
    return False


def _move_named_children_to_front(parent, ordered_names):
    """Move selected children to the front in ordered_names order.

    This is safe for wrappers whose first child is a property element, because
    all non-property content keeps its original relative order.
    """
    fixes = 0
    insert_at = 0
    for name in ordered_names:
        current_children = list(parent)
        found = None
        found_index = None
        for i, child in enumerate(current_children):
            if get_local_name(child) == name:
                found = child
                found_index = i
                break
        if found is None:
            continue
        if found_index != insert_at:
            parent.remove(found)
            parent.insert(insert_at, found)
            fixes += 1
        insert_at += 1
    return fixes


def _get_order(ns, elem_name):
    """Look up child ordering from ORDERS for a namespace + element."""
    return ORDERS.get(ns, {}).get(elem_name, [])


# ============================================================
# Special-case fix functions
# ============================================================

# Border element names that should be inside pBdr, not directly in pPr
_BORDER_ELEMENTS = {'top', 'left', 'bottom', 'right', 'between', 'bar'}


def fix_body_order(body_element):
    """Fix body element order: sectPr must be last.

    Body content (p, tbl, sdt, ...) is in document order, not schema order.
    Only sectPr needs to be moved to the end.
    Returns True if any fix was made.
    """
    children = list(body_element)
    if not children:
        return False

    sectpr = None
    sectpr_idx = None
    for i, child in enumerate(children):
        if get_local_name(child) == 'sectPr':
            sectpr = child
            sectpr_idx = i
            break

    if sectpr is None or sectpr_idx == len(children) - 1:
        return False

    body_element.remove(sectpr)
    body_element.append(sectpr)
    return True


def wrap_border_elements(ppr_element):
    """Fix misplaced border elements in pPr by wrapping them in pBdr.

    Returns number of elements wrapped.
    """
    misplaced_borders = []
    for child in list(ppr_element):
        if get_local_name(child) in _BORDER_ELEMENTS:
            misplaced_borders.append(child)

    if not misplaced_borders:
        return 0

    pbdr = ppr_element.find(w('pBdr'))
    if pbdr is None:
        pbdr = ppr_element.makeelement(w('pBdr'), {})
        inserted = False
        for i, child in enumerate(ppr_element):
            if get_local_name(child) in ['shd', 'tabs', 'suppressAutoHyphens', 'spacing', 'ind', 'jc']:
                ppr_element.insert(i, pbdr)
                inserted = True
                break
        if not inserted:
            ppr_element.append(pbdr)

    fixes = 0
    for border in misplaced_borders:
        ppr_element.remove(border)
        pbdr.append(border)
        fixes += 1

    pbdr_order = _get_order(W_NS, 'pBdr')
    if pbdr_order:
        reorder_children(pbdr, pbdr_order)

    return fixes


# ============================================================
# Main fix function
# ============================================================

_PROPERTY_CONTAINERS = {
    'pPr', 'rPr', 'pBdr',
    'tblPr', 'tblBorders', 'tblCellMar', 'tblPrEx',
    'trPr',
    'tcPr', 'tcBorders', 'tcMar',
    'sectPr',
    'numbering', 'abstractNum', 'lvl',
    'style', 'styles', 'docDefaults',
}


def _reorder_property_containers(root):
    """Reorder known property containers using XSD-derived child order."""
    fixes = 0
    for elem_name in sorted(_PROPERTY_CONTAINERS):
        order = _get_order(W_NS, elem_name)
        if not order:
            continue
        tag = f'{{{W_NS}}}{elem_name}'
        for parent in root.iter(tag):
            if reorder_children(parent, order):
                fixes += 1
    return fixes


def _fix_inline_property_positions(root):
    """Move pPr/rPr to their required first-child position without sorting content."""
    fixes = 0
    for paragraph in root.iter(w('p')):
        if _move_child_to_front(paragraph, 'pPr'):
            fixes += 1
    for run in root.iter(w('r')):
        if _move_child_to_front(run, 'rPr'):
            fixes += 1
    return fixes


def _fix_table_structure(root):
    """Move table/row/cell property children without changing content order."""
    fixes = 0
    for tbl in root.iter(w('tbl')):
        fixes += _move_named_children_to_front(tbl, ['tblPr', 'tblGrid'])
    for tr in root.iter(w('tr')):
        fixes += _move_named_children_to_front(tr, ['tblPrEx', 'trPr'])
    for tc in root.iter(w('tc')):
        if _move_child_to_front(tc, 'tcPr'):
            fixes += 1
    return fixes


def fix_element_order_in_tree(root):
    """Fix safe element-order issues in an XML tree.

    Returns number of fixes made.
    """
    fixes = 0

    # Special: wrap misplaced borders in pPr before reordering
    for ppr in root.iter(w('pPr')):
        fixes += wrap_border_elements(ppr)

    # Special: body uses document-content order, only move sectPr to end
    for body in root.iter(w('body')):
        if fix_body_order(body):
            fixes += 1

    fixes += _fix_inline_property_positions(root)
    fixes += _fix_table_structure(root)
    fixes += _reorder_property_containers(root)

    return fixes


def fix_settings(root):
    """Fix settings.xml element order using XSD-derived rules. Returns fix count."""
    settings_order = _get_order(W_NS, 'settings')
    if not settings_order:
        return 0

    settings_elem = root if get_local_name(root) == 'settings' else root.find(w('settings'))
    if settings_elem is not None and reorder_children(settings_elem, settings_order):
        return 1
    return 0


# ============================================================
# Table width fix (conservative) — not ordering, unique logic
# ============================================================

def fix_table_width_conservative(root):
    """Fix table cell width (tcW) to match grid column width (gridCol).

    CONSERVATIVE RULES — only fix when 100% safe:
    1. Only fix type="dxa" or no type attribute (dxa is default)
    2. Skip type="pct" (percentage) — intentional design choice
    3. Skip type="auto" — auto width should not be touched
    4. Only modify existing tcW — never create new elements
    5. Handle gridSpan correctly — sum of spanned columns
    6. Skip if no tblGrid — can't fix without reference
    7. Skip nested tables — too complex, might break layout

    Returns number of fixes made.
    """
    fixes = 0
    all_tables = root.findall('.//{%s}tbl' % W_NS)

    for tbl in all_tables:
        is_nested = False
        for outer_tbl in all_tables:
            if outer_tbl is tbl:
                continue
            for inner in outer_tbl.iter('{%s}tbl' % W_NS):
                if inner is tbl:
                    is_nested = True
                    break
            if is_nested:
                break
        if is_nested:
            continue

        tbl_grid = tbl.find('{%s}tblGrid' % W_NS)
        if tbl_grid is None:
            continue

        grid_cols = tbl_grid.findall('{%s}gridCol' % W_NS)
        if not grid_cols:
            continue

        grid_widths = []
        valid_grid = True
        for gc in grid_cols:
            w_val = gc.get('{%s}w' % W_NS)
            if w_val is None:
                valid_grid = False
                break
            try:
                grid_widths.append(int(w_val))
            except ValueError:
                valid_grid = False
                break

        if not valid_grid or not grid_widths:
            continue

        rows = tbl.findall('{%s}tr' % W_NS)
        for row in rows:
            cells = row.findall('{%s}tc' % W_NS)
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
                if tc_type is not None and tc_type not in ('dxa', ''):
                    col_idx += 1
                    continue

                grid_span = tc_pr.find('{%s}gridSpan' % W_NS)
                span_count = 1
                if grid_span is not None:
                    span_val = grid_span.get('{%s}val' % W_NS)
                    if span_val:
                        try:
                            span_count = int(span_val)
                        except ValueError:
                            span_count = 1

                if col_idx + span_count > len(grid_widths):
                    col_idx += span_count
                    continue

                expected_width = sum(grid_widths[col_idx:col_idx + span_count])

                current_width = tc_w.get('{%s}w' % W_NS)
                if current_width is None:
                    col_idx += span_count
                    continue

                try:
                    current_width_int = int(current_width)
                except ValueError:
                    col_idx += span_count
                    continue

                if expected_width > 0 and abs(current_width_int - expected_width) > expected_width * 0.05:
                    tc_w.set('{%s}w' % W_NS, str(expected_width))
                    fixes += 1

                col_idx += span_count

    return fixes
