#!/usr/bin/env python3
"""Static checks for common docx-js mistakes."""

from __future__ import annotations

import re
import sys
from pathlib import Path


class LintError:
    def __init__(self, path: Path, line: int, message: str):
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _skip_string(source: str, index: int) -> int:
    quote = source[index]
    index += 1
    while index < len(source):
        ch = source[index]
        if ch == "\\":
            index += 2
            continue
        if ch == quote:
            return index + 1
        index += 1
    return index


def _skip_template(source: str, index: int) -> int:
    index += 1
    while index < len(source):
        ch = source[index]
        if ch == "\\":
            index += 2
            continue
        if ch == "`":
            return index + 1
        index += 1
    return index


def _template_expression_ranges(source: str, index: int) -> tuple[list[tuple[int, int]], int]:
    ranges: list[tuple[int, int]] = []
    cursor = index + 1
    while cursor < len(source):
        ch = source[cursor]
        if ch == "\\":
            cursor += 2
            continue
        if ch == "`":
            return ranges, cursor + 1
        if source.startswith("${", cursor):
            close = _matching_delimiter(source, cursor + 1, "{", "}")
            if close == -1:
                return ranges, len(source)
            ranges.append((cursor + 2, close))
            cursor = close + 1
            continue
        cursor += 1
    return ranges, cursor


def _skip_comment(source: str, index: int) -> int:
    if source.startswith("//", index):
        end = source.find("\n", index + 2)
        return len(source) if end == -1 else end + 1
    if source.startswith("/*", index):
        end = source.find("*/", index + 2)
        return len(source) if end == -1 else end + 2
    return index


def _skip_ws_comments(source: str, index: int) -> int:
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue
        break
    return index


def _read_identifier(source: str, index: int) -> tuple[str | None, int]:
    match = re.match(r"[A-Za-z_$][\w$]*", source[index:])
    if not match:
        return None, index
    value = match.group(0)
    return value, index + len(value)


def _matching_delimiter(source: str, open_index: int, opener: str, closer: str) -> int:
    depth = 0
    index = open_index
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _top_level_segments(body: str) -> list[str]:
    segments: list[str] = []
    start = 0
    depth = 0
    index = 0
    while index < len(body):
        ch = body[index]
        if ch in ("'", '"'):
            index = _skip_string(body, index)
            continue
        if ch == "`":
            index = _skip_template(body, index)
            continue
        if body.startswith("//", index) or body.startswith("/*", index):
            index = _skip_comment(body, index)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            segments.append(body[start:index])
            start = index + 1
        index += 1
    segments.append(body[start:])
    return segments


def _statement_end(source: str, index: int) -> int:
    depth = 0
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            return index
        index += 1
    return index


def _top_level_props(body: str, object_bindings: dict[str, set[str]] | None = None) -> set[str]:
    object_bindings = object_bindings or {}
    props: set[str] = set()
    for segment in _top_level_segments(body):
        stripped = segment.strip()
        if re.fullmatch(r"[A-Za-z_$][\w$]*", stripped):
            props.add(stripped)
            continue
        if stripped.startswith("..."):
            spread = stripped[3:].strip()
            if spread.startswith("{"):
                close = _matching_delimiter(spread, 0, "{", "}")
                if close != -1:
                    props.update(_top_level_props(spread[1:close], object_bindings))
            elif spread in object_bindings:
                props.update(object_bindings[spread])
            continue
        match = re.match(r"([A-Za-z_$][\w$]*)(?:\s|/\*.*?\*/)*:", stripped, re.DOTALL)
        if match:
            props.add(match.group(1))
            continue
        quoted = re.match(r"""(["'])([^"']+)\1\s*:""", stripped)
        if quoted:
            props.add(quoted.group(2))
            continue
        computed = re.match(r"""\[\s*(["'])([^"']+)\1\s*\]\s*:""", stripped)
        if computed:
            props.add(computed.group(2))
    return props


def _constructor_is_paragraph(expr: str, constructor_aliases: set[str] | None = None) -> bool:
    constructor_aliases = constructor_aliases or set()
    cleaned = re.sub(r"/\*.*?\*/", "", expr, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", "", cleaned)
    if cleaned in constructor_aliases:
        return True
    return bool(
        re.fullmatch(r"(?:[A-Za-z_$][\w$]*\.)*Paragraph", cleaned)
        or re.fullmatch(r"(?:[A-Za-z_$][\w$]*\.)*[A-Za-z_$][\w$]*\[['\"]Paragraph['\"]\]", cleaned)
    )


def _parse_constructor_expr(source: str, index: int) -> tuple[str | None, int]:
    index = _skip_ws_comments(source, index)
    if index < len(source) and source[index] == "(":
        close = _matching_delimiter(source, index, "(", ")")
        if close == -1:
            return None, index
        return source[index + 1:close], close + 1

    start = index
    ident, index = _read_identifier(source, index)
    if ident is None:
        return None, start

    while True:
        index = _skip_ws_comments(source, index)
        if index < len(source) and source[index] == ".":
            index = _skip_ws_comments(source, index + 1)
            ident, index = _read_identifier(source, index)
            if ident is None:
                return None, start
            continue
        if index < len(source) and source[index] == "[":
            close = _matching_delimiter(source, index, "[", "]")
            if close == -1:
                return None, start
            index = close + 1
            continue
        break

    return source[start:index], index


def _collect_object_literal_bindings(source: str) -> dict[str, set[str]]:
    bindings: dict[str, set[str]] = {}
    index = 0
    decl_pattern = re.compile(r"\b(?:const|let|var)\b")
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue

        match = decl_pattern.match(source, index)
        if match is None:
            index += 1
            continue

        cursor = _skip_ws_comments(source, match.end())
        name, cursor = _read_identifier(source, cursor)
        if name is None:
            index = match.end()
            continue
        cursor = _skip_ws_comments(source, cursor)
        if cursor >= len(source) or source[cursor] != "=":
            index = match.end()
            continue
        cursor = _skip_ws_comments(source, cursor + 1)
        if cursor >= len(source) or source[cursor] != "{":
            index = match.end()
            continue
        close = _matching_delimiter(source, cursor, "{", "}")
        if close == -1:
            index = match.end()
            continue
        bindings[name] = _top_level_props(source[cursor + 1:close], bindings)
        index = close + 1

    return bindings


def _collect_import_paragraph_aliases(source: str) -> set[str]:
    aliases = {"Paragraph"}

    for match in re.finditer(r"\bimport\s*\{(?P<body>.*?)\}\s*from\s*['\"]docx['\"]", source, re.DOTALL):
        for segment in _top_level_segments(match.group("body")):
            stripped = segment.strip()
            alias = re.fullmatch(r"Paragraph\s+as\s+([A-Za-z_$][\w$]*)", stripped)
            if alias:
                aliases.add(alias.group(1))
            elif stripped == "Paragraph":
                aliases.add("Paragraph")

    for match in re.finditer(
        r"\b(?:const|let|var)\s*\{(?P<body>.*?)\}\s*=\s*require\s*\(\s*['\"]docx['\"]\s*\)",
        source,
        re.DOTALL,
    ):
        for segment in _top_level_segments(match.group("body")):
            stripped = segment.strip()
            alias = re.fullmatch(r"Paragraph\s*:\s*([A-Za-z_$][\w$]*)", stripped)
            if alias:
                aliases.add(alias.group(1))
            elif stripped == "Paragraph":
                aliases.add("Paragraph")

    return aliases


def _collect_paragraph_aliases(source: str) -> set[str]:
    aliases: set[str] = _collect_import_paragraph_aliases(source)
    alias_assignments: list[tuple[str, str]] = []
    index = 0
    decl_pattern = re.compile(r"\b(?:const|let|var)\b")
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue

        match = decl_pattern.match(source, index)
        if match is None:
            index += 1
            continue

        cursor = _skip_ws_comments(source, match.end())
        name, cursor = _read_identifier(source, cursor)
        if name is None:
            index = match.end()
            continue
        cursor = _skip_ws_comments(source, cursor)
        if cursor >= len(source) or source[cursor] != "=":
            index = match.end()
            continue
        expr_start = _skip_ws_comments(source, cursor + 1)
        expr_end = _statement_end(source, expr_start)
        expr = source[expr_start:expr_end].strip()
        alias_assignments.append((name, expr))
        if _constructor_is_paragraph(expr, aliases):
            aliases.add(name)
        index = expr_end + 1

    changed = True
    while changed:
        changed = False
        for name, expr in alias_assignments:
            if name not in aliases and _constructor_is_paragraph(expr, aliases):
                aliases.add(name)
                changed = True

    return aliases


def _props_from_returning_function(body: str, object_bindings: dict[str, set[str]]) -> set[str] | None:
    cursor = _skip_ws_comments(body, 0)
    if cursor < len(body) and body[cursor] == "(":
        inner = _skip_ws_comments(body, cursor + 1)
        if inner < len(body) and body[inner] == "{":
            close = _matching_delimiter(body, inner, "{", "}")
            if close != -1:
                return _top_level_props(body[inner + 1:close], object_bindings)
    if cursor < len(body) and body[cursor] == "{":
        close = _matching_delimiter(body, cursor, "{", "}")
        if close != -1:
            return _top_level_props(body[cursor + 1:close], object_bindings)
    return None


def _collect_function_return_bindings(source: str, object_bindings: dict[str, set[str]]) -> dict[str, set[str]]:
    bindings: dict[str, set[str]] = {}

    for match in re.finditer(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", source):
        name = match.group(1)
        open_brace = source.find("{", match.end() - 1)
        close_brace = _matching_delimiter(source, open_brace, "{", "}")
        if close_brace == -1:
            continue
        body = source[open_brace + 1:close_brace]
        ret = re.search(r"\breturn\b", body)
        if not ret:
            continue
        props = _props_from_returning_function(body[ret.end():], object_bindings)
        if props:
            bindings[name] = props

    decl_pattern = re.compile(r"\b(?:const|let|var)\b")
    index = 0
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue

        match = decl_pattern.match(source, index)
        if match is None:
            index += 1
            continue

        cursor = _skip_ws_comments(source, match.end())
        name, cursor = _read_identifier(source, cursor)
        if name is None:
            index = match.end()
            continue
        cursor = _skip_ws_comments(source, cursor)
        if cursor >= len(source) or source[cursor] != "=":
            index = match.end()
            continue

        expr_start = _skip_ws_comments(source, cursor + 1)
        expr_end = _statement_end(source, expr_start)
        expr = source[expr_start:expr_end]
        arrow = expr.find("=>")
        if arrow == -1:
            index = expr_end + 1
            continue

        scan = 0
        while scan < arrow:
            if expr[scan] in ("'", '"'):
                scan = _skip_string(expr, scan)
                continue
            if expr[scan] == "`":
                scan = _skip_template(expr, scan)
                continue
            if expr.startswith("//", scan) or expr.startswith("/*", scan):
                scan = _skip_comment(expr, scan)
                continue
            scan += 1
        if scan > arrow:
            index = expr_end + 1
            continue

        props = _props_from_returning_function(expr[arrow + 2:], object_bindings)
        if props:
            bindings[name] = props
        index = expr_end + 1

    return bindings


def _props_from_call_args(
    source: str,
    cursor: int,
    object_bindings: dict[str, set[str]],
    function_return_bindings: dict[str, set[str]],
) -> tuple[set[str] | None, int]:
    cursor = _skip_ws_comments(source, cursor)
    if cursor >= len(source) or source[cursor] != "(":
        return None, cursor

    close_paren = _matching_delimiter(source, cursor, "(", ")")
    if close_paren == -1:
        close_paren = cursor

    arg_index = _skip_ws_comments(source, cursor + 1)
    if arg_index < len(source) and source[arg_index] == "{":
        close_brace = _matching_delimiter(source, arg_index, "{", "}")
        if close_brace == -1:
            return None, cursor + 1
        return _top_level_props(source[arg_index + 1:close_brace], object_bindings), close_paren + 1

    arg_name, _arg_end = _read_identifier(source, arg_index)
    if arg_name and arg_name in object_bindings:
        return object_bindings[arg_name], close_paren + 1
    if arg_name and arg_name in function_return_bindings:
        after_name = _skip_ws_comments(source, _arg_end)
        if after_name < len(source) and source[after_name] == "(":
            return function_return_bindings[arg_name], close_paren + 1

    return None, close_paren + 1


def _previous_word(source: str, index: int) -> str | None:
    cursor = index - 1
    while cursor >= 0 and source[cursor].isspace():
        cursor -= 1
    end = cursor + 1
    while cursor >= 0 and re.match(r"[\w$]", source[cursor]):
        cursor -= 1
    if end == cursor + 1:
        return None
    return source[cursor + 1:end]


def _lint_shading_options(path: Path, source: str, object_bindings: dict[str, set[str]]) -> list[LintError]:
    errors: list[LintError] = []
    index = 0
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue

        if not source.startswith("shading", index):
            index += 1
            continue
        before_ok = index == 0 or not re.match(r"[\w$]", source[index - 1])
        after = index + len("shading")
        after_ok = after >= len(source) or not re.match(r"[\w$]", source[after])
        if not before_ok or not after_ok:
            index += 1
            continue

        line_index = index
        cursor = _skip_ws_comments(source, after)
        if cursor >= len(source) or source[cursor] != ":":
            index += 1
            continue
        cursor = _skip_ws_comments(source, cursor + 1)
        if cursor >= len(source):
            index += 1
            continue

        props: set[str] | None = None
        if source[cursor] == "{":
            close = _matching_delimiter(source, cursor, "{", "}")
            if close != -1:
                props = _top_level_props(source[cursor + 1:close], object_bindings)
                index = close + 1
            else:
                index += 1
        else:
            name, name_end = _read_identifier(source, cursor)
            if name and name in object_bindings:
                props = object_bindings[name]
                index = name_end
            else:
                index += 1

        if props and "val" in props and "type" not in props:
            line = source.count("\n", 0, line_index) + 1
            errors.append(
                LintError(
                    path,
                    line,
                    "docx-js shading options use type: ShadingType.CLEAR; "
                    "do not use OOXML val on the shading object.",
                )
            )

    return errors


def _has_mixed_single_and_script_fonts(props: set[str] | None) -> bool:
    return bool(props and "name" in props and props.intersection({"ascii", "hAnsi", "cs", "eastAsia"}))


def _font_shape_error(path: Path, source: str, index: int) -> LintError:
    return LintError(
        path,
        source.count("\n", 0, index) + 1,
        "docx-js font options must not combine name with ascii/hAnsi/cs/eastAsia; "
        "name selects the single-font branch and silently ignores script-specific fonts.",
    )


def _lint_font_options(path: Path, source: str, object_bindings: dict[str, set[str]]) -> list[LintError]:
    errors: list[LintError] = []
    reported_bindings: set[str] = set()

    declaration_pattern = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*font[\w$]*)\s*=", re.IGNORECASE)
    for match in declaration_pattern.finditer(source):
        cursor = _skip_ws_comments(source, match.end())
        if cursor >= len(source) or source[cursor] != "{":
            continue
        close = _matching_delimiter(source, cursor, "{", "}")
        if close == -1:
            continue
        props = _top_level_props(source[cursor + 1:close], object_bindings)
        if _has_mixed_single_and_script_fonts(props):
            errors.append(_font_shape_error(path, source, match.start()))
            reported_bindings.add(match.group(1))

    index = 0
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            index = _skip_template(source, index)
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue
        if not source.startswith("font", index):
            index += 1
            continue
        before_ok = index == 0 or not re.match(r"[\w$]", source[index - 1])
        after = index + len("font")
        after_ok = after >= len(source) or not re.match(r"[\w$]", source[after])
        if not before_ok or not after_ok:
            index += 1
            continue
        cursor = _skip_ws_comments(source, after)
        if cursor >= len(source) or source[cursor] != ":":
            index = after
            continue
        cursor = _skip_ws_comments(source, cursor + 1)
        props: set[str] | None = None
        binding_name: str | None = None
        if cursor < len(source) and source[cursor] == "{":
            close = _matching_delimiter(source, cursor, "{", "}")
            if close != -1:
                props = _top_level_props(source[cursor + 1:close], object_bindings)
                index = close + 1
            else:
                index = cursor + 1
        else:
            binding_name, end = _read_identifier(source, cursor)
            if binding_name is not None:
                props = object_bindings.get(binding_name)
                index = end
            else:
                index = cursor + 1
        if _has_mixed_single_and_script_fonts(props) and binding_name not in reported_bindings:
            errors.append(_font_shape_error(path, source, index))

    return errors


def lint_source(path: Path, source: str) -> list[LintError]:
    errors: list[LintError] = []
    object_bindings = _collect_object_literal_bindings(source)
    function_return_bindings = _collect_function_return_bindings(source, object_bindings)
    constructor_aliases = _collect_paragraph_aliases(source)
    new_pattern = re.compile(r"\bnew\b")
    errors.extend(_lint_shading_options(path, source, object_bindings))
    errors.extend(_lint_font_options(path, source, object_bindings))

    index = 0
    while index < len(source):
        ch = source[index]
        if ch in ("'", '"'):
            index = _skip_string(source, index)
            continue
        if ch == "`":
            ranges, template_end = _template_expression_ranges(source, index)
            for start, end in ranges:
                line_offset = source.count("\n", 0, start)
                for error in lint_source(path, source[start:end]):
                    error.line += line_offset
                    errors.append(error)
            index = template_end
            continue
        if source.startswith("//", index) or source.startswith("/*", index):
            index = _skip_comment(source, index)
            continue

        match = new_pattern.match(source, index)
        line_index = index
        if match is not None:
            constructor_expr, cursor = _parse_constructor_expr(source, match.end())
            if constructor_expr is None or not _constructor_is_paragraph(constructor_expr, constructor_aliases):
                index = match.end()
                continue
            line_index = match.start()
        else:
            if not re.match(r"[A-Za-z_$]", ch):
                index += 1
                continue
            if index > 0 and re.match(r"[\w$]", source[index - 1]):
                index += 1
                continue
            if _previous_word(source, index) == "new":
                index += 1
                continue
            constructor_expr, cursor = _parse_constructor_expr(source, index)
            if constructor_expr is None or not _constructor_is_paragraph(constructor_expr, constructor_aliases):
                index += 1
                continue

        props, scan_resume = _props_from_call_args(
            source,
            cursor,
            object_bindings,
            function_return_bindings,
        )
        if props is None:
            index = match.end() if match is not None else index + 1
            continue

        if "text" in props and "children" in props:
            line = source.count("\n", 0, line_index) + 1
            errors.append(
                LintError(
                    path,
                    line,
                    "docx-js Paragraph must not combine top-level text and children; "
                    "use text for plain paragraphs or children with TextRun for styled content.",
                )
            )
        # Continue inside the call so nested Paragraph(...) mistakes are still reported.
        index = cursor + 1

    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: lint_docx_js.py <script.js> [more.js ...]", file=sys.stderr)
        return 2

    errors: list[LintError] = []
    for raw_path in argv:
        path = Path(raw_path)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(LintError(path, 1, f"cannot read file: {exc}"))
            continue
        errors.extend(lint_source(path, source))

    for error in errors:
        print(error)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
