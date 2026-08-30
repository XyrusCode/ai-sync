import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
W16CID_NS = "http://schemas.microsoft.com/office/word/2016/wordml/cid"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
ODR_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
R_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04"
    b"\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _run_validate(docx_path: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SCRIPT_DIR}:{env.get('PYTHONPATH', '')}"
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "validate_all.py"), str(docx_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def _write_minimal_docx(path: Path, *, duplicate_bookmark: bool = False) -> None:
    bookmark = ""
    if duplicate_bookmark:
        bookmark = """
        <w:p>
          <w:bookmarkStart w:id="1" w:name="a"/>
          <w:bookmarkStart w:id="1" w:name="b"/>
          <w:r><w:t>duplicate bookmark</w:t></w:r>
          <w:bookmarkEnd w:id="1"/>
        </w:p>
        """

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
    <w:p><w:r><w:t>Hello</w:t></w:r></w:p>
    {bookmark}
    <w:tbl>
      <w:tblPr><w:tblW w:w="8000" w:type="dxa"/></w:tblPr>
      <w:tblGrid><w:gridCol w:w="4000"/><w:gridCol w:w="4000"/></w:tblGrid>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="1000" w:type="dxa"/></w:tcPr><w:p/></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="7000" w:type="dxa"/></w:tcPr><w:p/></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""

    content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CT_NS}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

    root_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

    document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="/word/media/image1.png"/>
</Relationships>
"""

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/_rels/document.xml.rels", document_rels)
        zf.writestr("word/media/image1.png", PNG_1X1)


def _replace_docx_entries(path: Path, entries: dict[str, str | bytes]) -> None:
    temp_path = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path, "r") as src, zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as dst:
        replaced = set(entries)
        for info in src.infolist():
            if info.filename not in replaced:
                dst.writestr(info, src.read(info.filename))
        for name, payload in entries.items():
            dst.writestr(name, payload)
    temp_path.replace(path)


class DocxToolingTests(unittest.TestCase):
    def test_build_resolves_external_docx_package_for_commonjs_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_docx = root / "source.docx"
            _write_minimal_docx(source_docx)

            external_modules = root / "external" / "node_modules"
            fake_docx = external_modules / "docx"
            fake_docx.mkdir(parents=True)
            (fake_docx / "package.json").write_text(
                '{"name":"docx","version":"0.0.0","type":"module","main":"index.js"}',
                encoding="utf-8",
            )
            (fake_docx / "index.js").write_text(
                "export class Document {}\n",
                encoding="utf-8",
            )

            script_dir = root / "work"
            script_dir.mkdir()
            (script_dir / "package.json").write_text('{"type":"commonjs"}', encoding="utf-8")
            script = script_dir / "create.js"
            script.write_text(
                """
import fs from "node:fs";
import { Document } from "docx";

if (!Document) throw new Error("docx import failed");
fs.copyFileSync(process.env.SOURCE_DOCX, process.argv[2]);
""",
                encoding="utf-8",
            )
            output = script_dir / "out.docx"

            env = os.environ.copy()
            env["NODE_PATH"] = str(external_modules)
            env["SOURCE_DOCX"] = str(source_docx)
            result = subprocess.run(
                [str(SCRIPT_DIR / "docx"), "build", str(script), str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(output.exists())
            self.assertFalse((script_dir / "node_modules").exists(), result.stdout)
            self.assertFalse(list(script_dir.glob("*.docx-build.*.mjs")), result.stdout)

    def test_build_resolves_docx_from_parent_node_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_docx = root / "source.docx"
            _write_minimal_docx(source_docx)

            fake_docx = root / "work" / "node_modules" / "docx"
            fake_docx.mkdir(parents=True)
            (fake_docx / "package.json").write_text(
                '{"name":"docx","version":"0.0.0","type":"module","main":"index.js"}',
                encoding="utf-8",
            )
            (fake_docx / "index.js").write_text("export class Document {}\n", encoding="utf-8")

            script_dir = root / "work" / "nested"
            script_dir.mkdir()
            (script_dir / "package.json").write_text('{"type":"commonjs"}', encoding="utf-8")
            script = script_dir / "create.js"
            script.write_text(
                """
import fs from "node:fs";
import { Document } from "docx";

if (!Document) throw new Error("docx import failed");
fs.copyFileSync(process.env.SOURCE_DOCX, process.argv[2]);
""",
                encoding="utf-8",
            )
            output = script_dir / "out.docx"

            env = os.environ.copy()
            env["DOCX_BUILD_NO_GLOBAL"] = "1"
            env["HOME"] = str(root / "home")
            env["XDG_CACHE_HOME"] = str(root / "xdg")
            env["NODE_PATH"] = ""
            env["SOURCE_DOCX"] = str(source_docx)
            result = subprocess.run(
                [str(SCRIPT_DIR / "docx"), "build", str(script), str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(output.exists())
            self.assertFalse((script_dir / "node_modules").exists(), result.stdout)

    def test_build_reports_install_hint_when_docx_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_dir = root / "work"
            script_dir.mkdir()
            script = script_dir / "create.js"
            script.write_text('import { Document } from "docx";\nconsole.log(Document);\n', encoding="utf-8")
            output = script_dir / "out.docx"

            env = os.environ.copy()
            env["DOCX_BUILD_NO_GLOBAL"] = "1"
            env["DOCX_NPM_PREFIX"] = str(root / "empty-prefix")
            env["HOME"] = str(root / "home")
            env["XDG_CACHE_HOME"] = str(root / "xdg")
            env["NODE_PATH"] = ""
            result = subprocess.run(
                [str(SCRIPT_DIR / "docx"), "build", str(script), str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Cannot find npm package", result.stdout)
            self.assertIn("npm install docx", result.stdout)
            self.assertIn("check-docx", result.stdout)

    def test_setup_node_env_check_docx_reports_found_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_dir = root / "work" / "nested"
            script_dir.mkdir(parents=True)

            env = os.environ.copy()
            env["DOCX_BUILD_NO_GLOBAL"] = "1"
            env["DOCX_NPM_PREFIX"] = str(root / "empty-prefix")
            env["HOME"] = str(root / "home")
            env["XDG_CACHE_HOME"] = str(root / "xdg")
            env["NODE_PATH"] = ""

            missing = subprocess.run(
                [str(SCRIPT_DIR / "setup_node_env"), "check-docx", str(script_dir)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("MISSING docx", missing.stdout)
            self.assertIn("npm install docx", missing.stdout)
            self.assertIn(str(script_dir), missing.stdout)

            fake_docx = root / "work" / "node_modules" / "docx"
            fake_docx.mkdir(parents=True)
            (fake_docx / "package.json").write_text('{"name":"docx"}', encoding="utf-8")

            found = subprocess.run(
                [str(SCRIPT_DIR / "setup_node_env"), "check-docx", str(script_dir)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            self.assertEqual(found.returncode, 0, found.stdout)
            self.assertIn("FOUND docx", found.stdout)
            self.assertIn(str(fake_docx), found.stdout)

    def test_setup_node_env_can_install_docx_to_configured_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_npm_bin = root / "bin"
            fake_npm_bin.mkdir()
            fake_npm = fake_npm_bin / "npm"
            fake_npm.write_text(
                """#!/usr/bin/env bash
set -euo pipefail
if [ "${1:-}" = "root" ] && [ "${2:-}" = "-g" ]; then
  echo "/nowhere/global/node_modules"
  exit 0
fi
prefix=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --prefix)
      prefix="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
[ -n "$prefix" ] || exit 2
mkdir -p "$prefix/node_modules/docx"
cat > "$prefix/node_modules/docx/package.json" <<'JSON'
{"name":"docx","version":"0.0.0","type":"module","main":"index.js"}
JSON
cat > "$prefix/node_modules/docx/index.js" <<'JS'
export class Document {}
JS
""",
                encoding="utf-8",
            )
            fake_npm.chmod(0o755)

            prefix = root / "cache-prefix"

            env = os.environ.copy()
            env["PATH"] = f"{fake_npm_bin}{os.pathsep}{env.get('PATH', '')}"
            env["DOCX_NPM_PREFIX"] = str(prefix)
            env["DOCX_BUILD_NO_GLOBAL"] = "1"
            env["NODE_PATH"] = ""
            result = subprocess.run(
                [str(SCRIPT_DIR / "setup_node_env"), "ensure-docx"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((prefix / "node_modules" / "docx" / "package.json").exists())
            self.assertIn(str(prefix / "node_modules"), result.stdout)

    def test_lint_rejects_paragraph_text_children_mix(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_js = Path(tmp) / "bad.js"
            bad_js.write_text(
                """
const { Paragraph, TextRun } = require("docx");
new Paragraph({
  text: "Title",
  children: [new TextRun("Title")]
});
new docx.Paragraph({
  text: "Namespaced",
  children: [new TextRun("Namespaced")]
});
Paragraph({
  text: "No new",
  children: [new TextRun("No new")]
});
docx.Paragraph({
  text: "Namespaced no new",
  children: [new TextRun("Namespaced no new")]
});
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(bad_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Paragraph", result.stdout)
        self.assertIn("text", result.stdout)
        self.assertIn("children", result.stdout)
        self.assertEqual(result.stdout.count("Paragraph must not combine"), 4)

    def test_lint_allows_text_only_and_children_only_paragraphs(self):
        with tempfile.TemporaryDirectory() as tmp:
            good_js = Path(tmp) / "good.js"
            good_js.write_text(
                """
const { Paragraph, TextRun } = require("docx");
new Paragraph({ text: "Simple" });
new Paragraph({ children: [new TextRun({ text: "Styled", bold: true })] });
new Paragraph({ children: [{ text: "nested object is not a paragraph option" }] });
// new Paragraph({ text: "comment", children: [new TextRun("ignored")] });
const example = "new Paragraph({ text: 'string', children: [] })";
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(good_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_lint_ignores_comments_and_strings_but_flags_real_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            edge_js = Path(tmp) / "edge.js"
            edge_js.write_text(
                """
// new Paragraph({ text: "comment", children: [] })
const fake = "new Paragraph({ text: 'fake', children: [] })";
/*
new Paragraph({ text: "block comment", children: [] })
*/
new Paragraph({
  children: [new TextRun("x")],
  text: "bad"
});
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(edge_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("Paragraph must not combine"), 1)
        self.assertIn("edge.js:7", result.stdout)

    def test_lint_rejects_shorthand_computed_spread_and_bound_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_js = Path(tmp) / "bad-forms.js"
            bad_js.write_text(
                """
const { Paragraph, TextRun } = require("docx");
const text = "shorthand";
const children = [new TextRun("shorthand")];
const opts = { text: "bound", children: [new TextRun("bound")] };
const mixed = { text: "spread variable", children: [new TextRun("spread variable")] };
const P = Paragraph;
new Paragraph({ text, children });
new docx.Paragraph({ ["text"]: "computed", ["children"]: [new TextRun("computed")] });
new Paragraph({ ...{ text: "spread", children: [new TextRun("spread")] } });
new Paragraph({ ...mixed });
new Paragraph(opts);
new P({ text: "alias", children: [new TextRun("alias")] });
new (Paragraph)({ text: "paren", children: [new TextRun("paren")] });
new docx["Paragraph"]({ text: "bracket", children: [new TextRun("bracket")] });
new lib.docx.Paragraph({ text /* inline */: "comment", children: [new TextRun("comment")] });
const template = `${new Paragraph({ text: "template", children: [new TextRun("template")] })}`;
new Paragraph({
  children: [
    new Paragraph({ text: "nested", children: [new TextRun("nested")] })
  ]
});
import { Paragraph as Para } from "docx";
const P2 = Para;
const paragraphOptions = (value) => ({ text: value, children: [new TextRun(value)] });
function moreParagraphOptions(value) {
  return { text: value, children: [new TextRun(value)] };
}
new Para({ text: "esm alias", children: [new TextRun("esm alias")] });
new P2({ text: "esm alias chain", children: [new TextRun("esm alias chain")] });
new Paragraph(paragraphOptions("helper return"));
new Paragraph(moreParagraphOptions("function return"));
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(bad_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("Paragraph must not combine"), 15, result.stdout)

    def test_lint_rejects_oo_xml_shading_val(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_js = Path(tmp) / "bad-shading.js"
            bad_js.write_text(
                """
const shade = { val: "clear", fill: "EEF3F6" };
new TableCell({ shading: { val: "clear", fill: "EEF3F6" } });
new TableCell({ shading: shade });
new TableCell({ shading: { type: ShadingType.CLEAR, fill: "EEF3F6" } });
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(bad_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("shading options use type"), 2, result.stdout)

    def test_lint_rejects_single_font_shorthand_mixed_with_script_fonts(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_js = Path(tmp) / "bad-font.js"
            bad_js.write_text(
                """
const bodyFont = { name: "Times New Roman", eastAsia: "SimSun" };
new TextRun({ text: "中文", font: bodyFont });
new TextRun({ text: "中文", font: { name: "Arial", hAnsi: "Arial", eastAsia: "SimSun" } });
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(bad_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("single-font branch"), 2, result.stdout)

    def test_lint_allows_explicit_multi_script_font_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            good_js = Path(tmp) / "good-font.js"
            good_js.write_text(
                """
const bodyFont = {
  ascii: "Times New Roman",
  hAnsi: "Times New Roman",
  cs: "Times New Roman",
  eastAsia: "SimSun",
};
new TextRun({ text: "中文", font: bodyFont });
""",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "lint_docx_js.py"), str(good_js)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_validate_warns_when_cjk_run_explicitly_uses_latin_east_asia_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "bad-cjk-font.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/></w:rPr><w:t>中文字体</w:t></w:r></w:p>
    <w:sectPr><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("w:eastAsia='Times New Roman'", result.stdout)

    def test_validate_accepts_explicit_cjk_east_asia_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "good-cjk-font.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun"/></w:rPr><w:t>中文字体</w:t></w:r></w:p>
    <w:sectPr><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("DOCX_FONT", result.stdout)

    def test_render_reports_unavailable_configured_renderer(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "input.docx"
            _write_minimal_docx(docx_path)
            env = os.environ.copy()
            env["DOCX_RENDERER"] = str(Path(tmp) / "missing-soffice")

            result = subprocess.run(
                ["bash", str(SCRIPT_DIR / "docx"), "render", str(docx_path), str(Path(tmp) / "rendered")],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("not executable", result.stdout)

    def test_validate_auto_fixes_package_and_table_widths(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "sample.docx"
            _write_minimal_docx(docx_path)

            env = os.environ.copy()
            env["PYTHONPATH"] = f"{SCRIPT_DIR}:{env.get('PYTHONPATH', '')}"
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "validate_all.py"), str(docx_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Fixed: applied", result.stdout)

            with zipfile.ZipFile(docx_path) as zf:
                content_types = ET.fromstring(zf.read("[Content_Types].xml"))
                document = ET.fromstring(zf.read("word/document.xml"))
                rels = ET.fromstring(zf.read("word/_rels/document.xml.rels"))

            xml_defaults = [
                elem.get("ContentType")
                for elem in content_types.findall(f"{{{CT_NS}}}Default")
                if elem.get("Extension") == "xml"
            ]
            self.assertEqual(xml_defaults, ["application/xml"])

            overrides = {
                elem.get("PartName")
                for elem in content_types.findall(f"{{{CT_NS}}}Override")
            }
            self.assertIn("/word/document.xml", overrides)

            body_children = list(document.find(f"{{{W_NS}}}body"))
            self.assertEqual(body_children[-1].tag, f"{{{W_NS}}}sectPr")

            widths = [
                elem.get(f"{{{W_NS}}}w")
                for elem in document.findall(f".//{{{W_NS}}}tcW")
            ]
            self.assertEqual(widths, ["4000", "4000"])

            targets = [elem.get("Target") for elem in rels.findall(f"{{{R_NS}}}Relationship")]
            self.assertEqual(targets, ["media/image1.png"])

    def test_validate_detects_duplicate_bookmark_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "duplicate.docx"
            _write_minimal_docx(docx_path, duplicate_bookmark=True)

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate bookmarkStart", result.stdout)

    def test_validate_rejects_missing_document_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "missing-document.docx"
            with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "[Content_Types].xml",
                    f"""<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="{CT_NS}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
</Types>
""",
                )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required part: word/document.xml", result.stdout)

    def test_validate_rejects_bad_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "bad.docx"
            docx_path.write_text("not a zip", encoding="utf-8")
            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("File corrupted or not valid docx", result.stdout)

    def test_validate_detects_missing_ignorable_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "missing-namespace.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:mc="{MC_NS}" mc:Ignorable="w14">
  <w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p><w:sectPr/></w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mc:Ignorable lists 'w14'", result.stdout)

    def test_validate_preserves_original_ignorable_namespaces_after_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "preserve-namespace.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:mc="{MC_NS}" xmlns:w14="{W14_NS}" xmlns:w15="{W15_NS}" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" mc:Ignorable="w14 w15 wp14">
  <w:body>
    <w:sectPr/>
    <w:p><w:r><w:t>Hello</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

            self.assertEqual(result.returncode, 0, result.stdout)
            with zipfile.ZipFile(docx_path) as zf:
                repaired = zf.read("word/document.xml").decode("utf-8")
            self.assertIn("xmlns:w14", repaired)
            self.assertIn("xmlns:w15", repaired)
            self.assertIn("xmlns:wp14", repaired)

    def test_validate_repairs_threaded_comment_companion_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "comments.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}" xmlns:mc="{MC_NS}" mc:Ignorable="w14">
  <w:comment w:id="0" w:author="A" w:date="2026-04-27T00:00:00Z">
    <w:p w14:paraId="00112233"><w:r><w:t>Reply thread</w:t></w:r></w:p>
  </w:comment>
</w:comments>
"""
            with zipfile.ZipFile(docx_path, "a", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("word/comments.xml", comments_xml)

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Fixed:", result.stdout)
        self.assertIn("comments.xml has orphan comment id '0'", result.stdout)

    def test_validate_detects_duplicate_comment_ids_in_comments_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "duplicate-comment-ids.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}">
  <w:comment w:id="0" w:author="A"><w:p><w:r><w:t>One</w:t></w:r></w:p></w:comment>
  <w:comment w:id="0" w:author="B"><w:p><w:r><w:t>Two</w:t></w:r></w:p></w:comment>
</w:comments>
"""
            _replace_docx_entries(docx_path, {"word/comments.xml": comments_xml})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate comment w:id='0'", result.stdout)

    def test_validate_detects_threaded_comment_paraid_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "comment-paraid-mismatch.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}" xmlns:mc="{MC_NS}" mc:Ignorable="w14">
  <w:comment w:id="0" w:author="A">
    <w:p w14:paraId="00112233"><w:r><w:t>Thread</w:t></w:r></w:p>
  </w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="DEADBEEF" w15:done="0"/>
</w15:commentsEx>
"""
            comments_ids_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="{W16CID_NS}">
  <w16cid:commentId w16cid:paraId="00112233" w16cid:durableId="ABCDEF01"/>
</w16cid:commentsIds>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/commentsIds.xml": comments_ids_xml,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commentsExtended.xml has orphan paraId 'DEADBEEF'", result.stdout)

    def test_validate_rejects_malformed_content_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "bad-content-types.docx"
            _write_minimal_docx(docx_path)
            _replace_docx_entries(docx_path, {"[Content_Types].xml": "<Types><Default>"})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONTENT_TYPES: malformed", result.stdout)
        self.assertIn("XML: [Content_Types].xml", result.stdout)

    def test_validate_rejects_conflicting_content_type_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "conflicting-overrides.docx"
            _write_minimal_docx(docx_path)
            content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CT_NS}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/xml"/>
</Types>
"""
            _replace_docx_entries(docx_path, {"[Content_Types].xml": content_types})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicting Override for /word/document.xml", result.stdout)

    def test_validate_repairs_missing_rels_content_type_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "missing-rels-default.docx"
            _write_minimal_docx(docx_path)
            content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CT_NS}">
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
            _replace_docx_entries(docx_path, {"[Content_Types].xml": content_types})

            result = _run_validate(docx_path)

            with zipfile.ZipFile(docx_path) as zf:
                content_types_root = ET.fromstring(zf.read("[Content_Types].xml"))

        self.assertEqual(result.returncode, 0, result.stdout)
        defaults = {
            elem.get("Extension"): elem.get("ContentType")
            for elem in content_types_root.findall(f"{{{CT_NS}}}Default")
        }
        self.assertEqual(defaults["rels"], "application/vnd.openxmlformats-package.relationships+xml")

    def test_validate_rejects_malformed_document_xml_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "bad-document.docx"
            _write_minimal_docx(docx_path)
            _replace_docx_entries(docx_path, {"word/document.xml": "<w:document>"})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("XML: word/document.xml", result.stdout)
        self.assertNotIn("Traceback", result.stdout)

    def test_validate_rejects_missing_office_document_relationship(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "missing-office-document-rel.docx"
            _write_minimal_docx(docx_path)
            root_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId99" Type="http://example.invalid/other" Target="word/document.xml"/>
</Relationships>
"""
            _replace_docx_entries(docx_path, {"_rels/.rels": root_rels})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing officeDocument relationship", result.stdout)

    def test_validate_repairs_missing_comment_relationship_for_comments_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "missing-comment-rel.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}">
  <w:comment w:id="0" w:author="A"><w:p><w:r><w:t>note</w:t></w:r></w:p></w:comment>
</w:comments>
"""
            _replace_docx_entries(docx_path, {"word/comments.xml": comments_xml})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Fixed:", result.stdout)
        self.assertIn("comments.xml has orphan comment id '0'", result.stdout)

    def test_validate_repairs_missing_comment_extension_relationships(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "missing-comment-extension-rels.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}" xmlns:mc="{MC_NS}" mc:Ignorable="w14">
  <w:comment w:id="0" w:author="A">
    <w:p w14:paraId="00112233"><w:r><w:t>thread</w:t></w:r></w:p>
  </w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="00112233" w15:done="0"/>
</w15:commentsEx>
"""
            comments_ids_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="{W16CID_NS}">
  <w16cid:commentId w16cid:paraId="00112233" w16cid:durableId="ABCDEF01"/>
</w16cid:commentsIds>
"""
            comments_extensible_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cex:commentsExtensible xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex">
  <w16cex:commentExtensible w16cex:durableId="ABCDEF01"/>
</w16cex:commentsExtensible>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/commentsIds.xml": comments_ids_xml,
                    "word/commentsExtensible.xml": comments_extensible_xml,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Fixed:", result.stdout)
        self.assertIn("comments.xml has orphan comment id '0'", result.stdout)

    def test_validate_rejects_comments_extensible_durable_id_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "comments-durable-drift.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}">
  <w:comment w:id="0" w:author="A">
    <w:p w14:paraId="00112233"><w:r><w:t>thread</w:t></w:r></w:p>
  </w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="00112233" w15:done="0"/>
</w15:commentsEx>
"""
            comments_ids_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="{W16CID_NS}">
  <w16cid:commentId w16cid:paraId="00112233" w16cid:durableId="ABCDEF01"/>
  <w16cid:commentId w16cid:paraId="DEADBEEF" w16cid:durableId="ABCDEF01"/>
</w16cid:commentsIds>
"""
            comments_extensible_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cex:commentsExtensible xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex">
  <w16cex:commentExtensible w16cex:durableId="ABCDEF01"/>
  <w16cex:commentExtensible w16cex:durableId="FACEBEEF"/>
</w16cex:commentsExtensible>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId3" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended" Target="commentsExtended.xml"/>
  <Relationship Id="rId4" Type="http://schemas.microsoft.com/office/2016/09/relationships/commentsIds" Target="commentsIds.xml"/>
  <Relationship Id="rId5" Type="http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible" Target="commentsExtensible.xml"/>
</Relationships>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/commentsIds.xml": comments_ids_xml,
                    "word/commentsExtensible.xml": comments_extensible_xml,
                    "word/_rels/document.xml.rels": document_rels,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate durableId 'ABCDEF01'", result.stdout)
        self.assertIn("commentsExtensible.xml has orphan durableId 'FACEBEEF'", result.stdout)

    def test_validate_rejects_duplicate_comments_extended_paraids(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "duplicate-comments-extended.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}">
  <w:comment w:id="0" w:author="A">
    <w:p w14:paraId="00112233"><w:r><w:t>thread</w:t></w:r></w:p>
  </w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="00112233" w15:done="0"/>
  <w15:commentEx w15:paraId="00112233" w15:done="1"/>
</w15:commentsEx>
"""
            comments_ids_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="{W16CID_NS}">
  <w16cid:commentId w16cid:paraId="00112233" w16cid:durableId="ABCDEF01"/>
</w16cid:commentsIds>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId3" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended" Target="commentsExtended.xml"/>
  <Relationship Id="rId4" Type="http://schemas.microsoft.com/office/2016/09/relationships/commentsIds" Target="commentsIds.xml"/>
</Relationships>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/commentsIds.xml": comments_ids_xml,
                    "word/_rels/document.xml.rels": document_rels,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate commentsExtended paraId '00112233'", result.stdout)

    def test_validate_rejects_duplicate_comments_extensible_durableids(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "duplicate-comments-extensible.docx"
            _write_minimal_docx(docx_path)
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}">
  <w:comment w:id="0" w:author="A">
    <w:p w14:paraId="00112233"><w:r><w:t>thread</w:t></w:r></w:p>
  </w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="00112233" w15:done="0"/>
</w15:commentsEx>
"""
            comments_ids_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="{W16CID_NS}">
  <w16cid:commentId w16cid:paraId="00112233" w16cid:durableId="ABCDEF01"/>
</w16cid:commentsIds>
"""
            comments_extensible_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cex:commentsExtensible xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex">
  <w16cex:commentExtensible w16cex:durableId="ABCDEF01"/>
  <w16cex:commentExtensible w16cex:durableId="ABCDEF01"/>
</w16cex:commentsExtensible>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId3" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended" Target="commentsExtended.xml"/>
  <Relationship Id="rId4" Type="http://schemas.microsoft.com/office/2016/09/relationships/commentsIds" Target="commentsIds.xml"/>
  <Relationship Id="rId5" Type="http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible" Target="commentsExtensible.xml"/>
</Relationships>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/commentsIds.xml": comments_ids_xml,
                    "word/commentsExtensible.xml": comments_extensible_xml,
                    "word/_rels/document.xml.rels": document_rels,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate commentsExtensible durableId 'ABCDEF01'", result.stdout)

    def test_validate_allows_mc_ignorable_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "mc-ignorable.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:mc="{MC_NS}" xmlns:w14="{W14_NS}" mc:Ignorable="w14">
  <w:body>
    <w:p w14:paraId="00112233"><w:r><w:t>Hello</w:t></w:r></w:p>
    <w:sectPr>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_validate_rejects_relationship_graph_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "bad-rels.docx"
            _write_minimal_docx(docx_path)
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/missing.png"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" TargetMode="External" Target="https://example.test/image.png"/>
</Relationships>
"""
            _replace_docx_entries(docx_path, {"word/_rels/document.xml.rels": document_rels})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate Id 'rId2'", result.stdout)
        self.assertIn("missing target media/missing.png", result.stdout)
        self.assertIn("external image target", result.stdout)

    def test_validate_rejects_comment_markers_without_comments_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "comment-marker-no-comments.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p>
      <w:commentRangeStart w:id="7"/>
      <w:r><w:t>Marked</w:t></w:r>
      <w:commentRangeEnd w:id="7"/>
      <w:r><w:commentReference w:id="7"/></w:r>
    </w:p>
    <w:sectPr><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("document has comment markers but missing comments.xml", result.stdout)

    def test_validate_rejects_duplicate_comment_reference_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "duplicate-comment-reference.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p>
      <w:commentRangeStart w:id="7"/>
      <w:r><w:t>Marked</w:t></w:r>
      <w:commentRangeEnd w:id="7"/>
      <w:r><w:commentReference w:id="7"/></w:r>
      <w:r><w:commentReference w:id="7"/></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate commentReference", result.stdout)

    def test_validate_rejects_threaded_reply_without_document_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "reply-without-anchor.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p>
      <w:commentRangeStart w:id="0"/>
      <w:r><w:t>Marked</w:t></w:r>
      <w:commentRangeEnd w:id="0"/>
      <w:r><w:commentReference w:id="0"/></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}" xmlns:mc="{MC_NS}" mc:Ignorable="w14">
  <w:comment w:id="0" w:author="A"><w:p w14:paraId="AAAABBBB"><w:r><w:t>note</w:t></w:r></w:p></w:comment>
  <w:comment w:id="1" w:author="B"><w:p w14:paraId="CCCCDDDD"><w:r><w:t>reply</w:t></w:r></w:p></w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="AAAABBBB" w15:done="0"/>
  <w15:commentEx w15:paraId="CCCCDDDD" w15:paraIdParent="AAAABBBB" w15:done="0"/>
</w15:commentsEx>
"""
            comments_ids_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="{W16CID_NS}">
  <w16cid:commentId w16cid:paraId="AAAABBBB" w16cid:durableId="11112222"/>
  <w16cid:commentId w16cid:paraId="CCCCDDDD" w16cid:durableId="33334444"/>
</w16cid:commentsIds>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId3" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended" Target="commentsExtended.xml"/>
  <Relationship Id="rId4" Type="http://schemas.microsoft.com/office/2016/09/relationships/commentsIds" Target="commentsIds.xml"/>
</Relationships>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/document.xml": document_xml,
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/commentsIds.xml": comments_ids_xml,
                    "word/_rels/document.xml.rels": document_rels,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("threaded reply comment id '1' has no document anchor", result.stdout)

    def test_reply_comment_backfills_metadata_and_anchors_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_docx = root / "input.docx"
            output_docx = root / "output.docx"
            _write_minimal_docx(input_docx)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p>
      <w:commentRangeStart w:id="0"/>
      <w:r><w:t>Marked</w:t></w:r>
      <w:commentRangeEnd w:id="0"/>
      <w:r><w:commentReference w:id="0"/></w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}" xmlns:w14="{W14_NS}">
  <w:comment w:id="0" w:author="A"><w:p w14:paraId="AAAABBBB"><w:r><w:t>note</w:t></w:r></w:p></w:comment>
</w:comments>
"""
            comments_extended_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="{W15_NS}">
  <w15:commentEx w15:paraId="AAAABBBB" w15:done="0"/>
</w15:commentsEx>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended" Target="commentsExtended.xml"/>
</Relationships>
"""
            _replace_docx_entries(
                input_docx,
                {
                    "word/document.xml": document_xml,
                    "word/comments.xml": comments_xml,
                    "word/commentsExtended.xml": comments_extended_xml,
                    "word/_rels/document.xml.rels": document_rels,
                },
            )

            sys.path.insert(0, str(SCRIPT_DIR))
            from docx_lib.editing import DocxContext, reply_comment

            with DocxContext(str(input_docx), str(output_docx)) as ctx:
                reply_id = reply_comment(ctx, "0", "reply text", author="B", initials="B")

            result = _run_validate(output_docx)

            self.assertEqual(result.returncode, 0, result.stdout)
            with zipfile.ZipFile(output_docx) as zf:
                document_root = ET.fromstring(zf.read("word/document.xml"))
                starts = [
                    elem.get(f"{{{W_NS}}}id")
                    for elem in document_root.iter(f"{{{W_NS}}}commentRangeStart")
                ]
                refs = [
                    elem.get(f"{{{W_NS}}}id")
                    for elem in document_root.iter(f"{{{W_NS}}}commentReference")
                ]
                self.assertIn(reply_id, starts)
                self.assertIn(reply_id, refs)

                ext_root = ET.fromstring(zf.read("word/commentsExtended.xml"))
                reply_para_ids = [
                    elem.get(f"{{{W15_NS}}}paraId")
                    for elem in ext_root.iter(f"{{{W15_NS}}}commentEx")
                    if elem.get(f"{{{W15_NS}}}paraIdParent") == "AAAABBBB"
                ]
                self.assertEqual(len(reply_para_ids), 1)

                ids_root = ET.fromstring(zf.read("word/commentsIds.xml"))
                ids_para = {
                    elem.get(f"{{{W16CID_NS}}}paraId")
                    for elem in ids_root.iter(f"{{{W16CID_NS}}}commentId")
                }
                self.assertIn("AAAABBBB", ids_para)
                self.assertIn(reply_para_ids[0], ids_para)

    def test_validate_preserves_inline_bookmark_range_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "bookmark-range.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:sectPr/>
    <w:p>
      <w:bookmarkStart w:id="1" w:name="target"/>
      <w:r><w:t>Marked</w:t></w:r>
      <w:bookmarkEnd w:id="1"/>
    </w:p>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

            self.assertEqual(result.returncode, 0, result.stdout)
            with zipfile.ZipFile(docx_path) as zf:
                document = ET.fromstring(zf.read("word/document.xml"))

        paragraph = document.find(f".//{{{W_NS}}}p")
        child_names = [elem.tag.split("}", 1)[1] for elem in list(paragraph)]
        self.assertEqual(child_names, ["bookmarkStart", "r", "bookmarkEnd"])

    def test_validate_preserves_omml_visual_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "omml-order.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:m="{M_NS}">
  <w:body>
    <w:p>
      <m:oMath>
        <m:r><m:t>A = </m:t></m:r>
        <m:m><m:mr><m:e><m:r><m:t>x</m:t></m:r></m:e></m:mr></m:m>
        <m:r><m:t> + B</m:t></m:r>
      </m:oMath>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

            self.assertEqual(result.returncode, 0, result.stdout)
            with zipfile.ZipFile(docx_path) as zf:
                document = ET.fromstring(zf.read("word/document.xml"))

        omath = document.find(f".//{{{M_NS}}}oMath")
        child_names = [elem.tag.split("}", 1)[1] for elem in list(omath)]
        self.assertEqual(child_names, ["r", "m", "r"])

    def test_validate_preserves_field_code_run_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "field-order.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p>
      <w:r>
        <w:fldChar w:fldCharType="begin"/>
        <w:instrText> PAGE </w:instrText>
        <w:fldChar w:fldCharType="separate"/>
        <w:t>1</w:t>
        <w:fldChar w:fldCharType="end"/>
      </w:r>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

            self.assertEqual(result.returncode, 0, result.stdout)
            with zipfile.ZipFile(docx_path) as zf:
                document = ET.fromstring(zf.read("word/document.xml"))

        run = document.find(f".//{{{W_NS}}}r")
        child_names = [elem.tag.split("}", 1)[1] for elem in list(run)]
        self.assertEqual(child_names, ["fldChar", "instrText", "fldChar", "t", "fldChar"])

    def test_validate_preserves_hyperlink_comment_marker_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "hyperlink-comment-order.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p>
      <w:hyperlink w:anchor="target">
        <w:commentRangeStart w:id="7"/>
        <w:r><w:t>Marked</w:t></w:r>
        <w:commentRangeEnd w:id="7"/>
        <w:r><w:commentReference w:id="7"/></w:r>
      </w:hyperlink>
    </w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            comments_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W_NS}">
  <w:comment w:id="7" w:author="A"><w:p><w:r><w:t>note</w:t></w:r></w:p></w:comment>
</w:comments>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/document.xml": document_xml,
                    "word/comments.xml": comments_xml,
                    "word/_rels/document.xml.rels": document_rels,
                },
            )

            result = _run_validate(docx_path)

            self.assertEqual(result.returncode, 0, result.stdout)
            with zipfile.ZipFile(docx_path) as zf:
                document = ET.fromstring(zf.read("word/document.xml"))

        hyperlink = document.find(f".//{{{W_NS}}}hyperlink")
        child_names = [elem.tag.split("}", 1)[1] for elem in list(hyperlink)]
        self.assertEqual(child_names, ["commentRangeStart", "r", "commentRangeEnd", "r"])

    def test_validate_allows_pct_widths_and_handles_gridspan(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "table-pct-gridspan.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:tbl>
      <w:tblPr><w:tblW w:w="8000" w:type="dxa"/></w:tblPr>
      <w:tblGrid><w:gridCol w:w="3000"/><w:gridCol w:w="5000"/></w:tblGrid>
      <w:tr>
        <w:tc>
          <w:tcPr><w:gridSpan w:val="2"/><w:tcW w:w="8000" w:type="dxa"/></w:tcPr>
          <w:p/>
        </w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="pct"/></w:tcPr><w:p/></w:tc>
      </w:tr>
    </w:tbl>
    <w:sectPr><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>
  </w:body>
</w:document>
"""
            _replace_docx_entries(docx_path, {"word/document.xml": document_xml})

            result = _run_validate(docx_path)

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_validate_detects_image_aspect_ratio_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "image-aspect.docx"
            _write_minimal_docx(docx_path)
            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:r="{ODR_NS}">
  <w:body>
    <w:p><w:r><w:drawing>
      <wp:inline>
        <wp:extent cx="2000000" cy="1000000"/>
        <a:graphic><a:graphicData><a:blip r:embed="rId2"/></a:graphicData></a:graphic>
      </wp:inline>
    </w:drawing></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
            document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
</Relationships>
"""
            _replace_docx_entries(
                docx_path,
                {
                    "word/document.xml": document_xml,
                    "word/_rels/document.xml.rels": document_rels,
                    "word/media/image1.png": PNG_1X1,
                },
            )

            result = _run_validate(docx_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("display=2.00 != actual=1.00", result.stdout)

    def test_revision_helpers_do_not_emit_word16du_dateutc(self):
        sys.path.insert(0, str(SCRIPT_DIR))
        from docx_lib.editing import DocxContext, insert_text, propose_deletion

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            insert_input = tmp_path / "insert-input.docx"
            insert_output = tmp_path / "insert-output.docx"
            delete_input = tmp_path / "delete-input.docx"
            delete_output = tmp_path / "delete-output.docx"
            _write_minimal_docx(insert_input)
            _write_minimal_docx(delete_input)

            with DocxContext(str(insert_input), str(insert_output)) as ctx:
                insert_text(ctx, "Hello", after="Hel", new_text=' "quoted"')
            with DocxContext(str(delete_input), str(delete_output)) as ctx:
                propose_deletion(ctx, "Hello", target="Hello")

            with zipfile.ZipFile(insert_output) as zf:
                insert_xml = zf.read("word/document.xml").decode("utf-8")
            with zipfile.ZipFile(delete_output) as zf:
                delete_xml = zf.read("word/document.xml").decode("utf-8")

        self.assertIn("<w:ins", insert_xml)
        self.assertIn('"quoted"', insert_xml)
        self.assertNotIn("dateUtc", insert_xml)
        self.assertIn("<w:del", delete_xml)
        self.assertIn("<w:delText", delete_xml)
        self.assertNotIn("dateUtc", delete_xml)

    def test_docx_build_runs_js_then_auto_fix_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture = tmp_path / "fixture.docx"
            output = tmp_path / "out.docx"
            script = tmp_path / "copy_fixture.js"
            _write_minimal_docx(fixture)
            script.write_text(
                """
const fs = require("fs");
fs.copyFileSync(process.env.DOCX_FIXTURE, process.argv[2]);
""",
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["DOCX_FIXTURE"] = str(fixture)
            result = subprocess.run(
                [str(SCRIPT_DIR / "docx"), "build", str(script), str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(output.exists())

    def test_docx_build_fails_when_script_does_not_write_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "missing.docx"
            script = tmp_path / "no_output.js"
            script.write_text("console.log('no output');\n", encoding="utf-8")

            result = subprocess.run(
                [str(SCRIPT_DIR / "docx"), "build", str(script), str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output was not written", result.stdout)

    def test_docx_build_fails_on_javascript_syntax_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "out.docx"
            script = tmp_path / "syntax.js"
            script.write_text("const = ;\n", encoding="utf-8")

            result = subprocess.run(
                [str(SCRIPT_DIR / "docx"), "build", str(script), str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SyntaxError", result.stdout)


if __name__ == "__main__":
    unittest.main()
