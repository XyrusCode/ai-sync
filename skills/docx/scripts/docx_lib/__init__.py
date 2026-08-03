"""docx_lib - Shared library for DOCX editing, validation, and repair."""

from .business_rules import (
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
    fix_relationship_paths,
)
from .constants import A_NS, NS, R_NS, W14_NS, W15_NS, W_NS, WP_NS, r, w
from .element_order import (
    fix_body_order,
    fix_element_order_in_tree,
    fix_settings,
    fix_table_width_conservative,
    reorder_children,
    wrap_border_elements,
)
from .schema_validation import validate_xml_schemas

__all__ = [
    'W_NS', 'W14_NS', 'W15_NS', 'R_NS', 'WP_NS', 'A_NS', 'NS', 'w', 'r',
    'fix_body_order', 'fix_element_order_in_tree', 'fix_settings',
    'fix_table_width_conservative', 'reorder_children', 'wrap_border_elements',
    'check_comment_anchor_integrity', 'check_comments_integrity',
    'check_cjk_run_fonts',
    'check_content_types_integrity', 'check_id_uniqueness',
    'check_image_aspect_ratio', 'check_namespace_declarations',
    'check_relationship_integrity', 'check_section_margins',
    'check_table_grid_consistency', 'fix_comment_metadata',
    'fix_content_types', 'fix_relationship_paths',
    'validate_xml_schemas',
]
