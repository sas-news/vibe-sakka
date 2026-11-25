"""export.py の self-test。

fixture の export_work/ は v2 の作品骨格 (work.md / plan / contracts /
scenes / craft / reviews / out)。ネットワーク・git に依存しない。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import export  # noqa: E402
from testlib import copy_fixture, fixture, read, run_tool  # noqa: E402


class ExportTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workdir = Path(self._tmp.name) / "work"
        copy_fixture("export_work", self.workdir)

    def tearDown(self):
        self._tmp.cleanup()

    @property
    def out_md(self) -> Path:
        return self.workdir / "out" / "星の名前.md"


class ExportMarkdownTest(ExportTestBase):
    def test_markdown_removes_yaml_and_inserts_headings(self):
        proc = run_tool("export.py", "--workdir", self.workdir)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = read(self.out_md)
        self.assertNotIn("```", text)
        self.assertNotIn("scene:", text)
        self.assertNotIn("polished:", text)
        self.assertIn("## 第1話 灯", text)
        self.assertIn("## 第2話 名前", text)
        # 公開順: 1-1 → 1-2 → 2-1
        first = text.index("灯台の石段は")
        second = text.index("昼になると")
        third = text.index("夜、ミナは灯をともした")
        self.assertLess(first, second)
        self.assertLess(second, third)
        self.assertLess(text.index("## 第1話 灯"), first)
        self.assertLess(second, text.index("## 第2話 名前"))

    def test_separator_between_scenes_in_same_episode(self):
        proc = run_tool("export.py", "--workdir", self.workdir,
                        "--separator", "◆")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = read(self.out_md)
        # 1-1 → 1-2 の間だけに区切り。話の境 (1-2 → 2-1) には入れない。
        self.assertEqual(text.count("◆"), 1)
        self.assertLess(text.index("灯台の石段は"), text.index("◆"))
        self.assertLess(text.index("◆"), text.index("昼になると"))

    def test_order_override(self):
        proc = run_tool("export.py", "--workdir", self.workdir,
                        "--order", "1-2,1-1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = read(self.out_md)
        self.assertLess(text.index("昼になると"), text.index("灯台の石段は"))

    def test_order_must_be_contiguous(self):
        proc = run_tool("export.py", "--workdir", self.workdir,
                        "--order", "1-1,2-1,1-2")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("連続していません", proc.stderr)

    def test_order_format_error(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--order", "1-x")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--order の書式", proc.stderr)

    def test_unparsable_plan_asks_for_order(self):
        plan = self.workdir / "plan" / "tree.md"
        plan.write_text(
            "# 計画ツリー\n\n| E | 章 | タイトル | status |\n| --- | --- | --- | --- |\n"
            "| 1 | I | 灯 | reviewed |\n", encoding="utf-8")
        proc = run_tool("export.py", "--workdir", self.workdir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--order", proc.stderr)
        self.assertIn("解析できません", proc.stderr)

    def test_title_from_work_md_and_override(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--title", "別名")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((self.workdir / "out" / "別名.md").is_file())
        self.assertIn("# 別名", read(self.workdir / "out" / "別名.md"))

    def test_report_written(self):
        proc = run_tool("export.py", "--workdir", self.workdir)
        self.assertEqual(proc.returncode, 0)
        report = read(self.workdir / "build" / "export-report.md")
        self.assertIn("export レポート", report)
        self.assertIn("1-1, 1-2, 2-1", report)
        self.assertIn("シーン数: 3", report)

    def test_json_output(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["title"], "星の名前")
        self.assertEqual(data["order"], ["1-1", "1-2", "2-1"])
        self.assertEqual(data["lint"]["errors"], 0)


class ExportFormatsTest(ExportTestBase):
    def test_txt(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--txt")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = read(self.workdir / "out" / "星の名前.txt")
        self.assertIn("第1話 灯", text)
        self.assertNotIn("##", text)
        self.assertNotIn("# 星の名前", text)

    def test_epub(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--epub")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        path = self.workdir / "out" / "星の名前.epub"
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names[0], "mimetype")
            self.assertEqual(archive.read("mimetype"), b"application/epub+zip")
            for name in ("META-INF/container.xml", "OEBPS/package.opf",
                         "OEBPS/nav.xhtml", "OEBPS/content.xhtml"):
                self.assertIn(name, names)
            content = archive.read("OEBPS/content.xhtml").decode("utf-8")
            self.assertIn("第1話 灯", content)
            self.assertIn("灯台の石段", content)

    def test_plain_text_conversion(self):
        markdown = "# 題\n\n## 第1話 灯\n\n**強調**と*斜体*の行。\n"
        text = export.to_plain_text(markdown)
        self.assertNotIn("#", text)
        self.assertNotIn("**", text)
        self.assertIn("強調と斜体の行。", text)


class ExportGateTest(ExportTestBase):
    def test_lint_error_blocks_writing(self):
        scene = self.workdir / "scenes" / "1-2.md"
        scene.write_text(read(scene) + "\n出典: https://example.com/x を参照。\n",
                        encoding="utf-8")
        self.out_md.unlink()
        proc = run_tool("export.py", "--workdir", self.workdir)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("L001", proc.stdout + proc.stderr)
        self.assertFalse(self.out_md.exists())

    def test_no_lint_allows_writing(self):
        scene = self.workdir / "scenes" / "1-2.md"
        scene.write_text(read(scene) + "\n出典: https://example.com/x を参照。\n",
                        encoding="utf-8")
        proc = run_tool("export.py", "--workdir", self.workdir, "--no-lint")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(self.out_md.is_file())

    def test_missing_scene_fails(self):
        (self.workdir / "scenes" / "2-1.md").unlink()
        proc = run_tool("export.py", "--workdir", self.workdir)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("scenes/2-1.md", proc.stderr)

    def test_release_passes_on_export_fixture(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--release",
                        "--epub", "--txt")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("release gate: 合格", proc.stdout)
        reports = sorted((self.workdir / "reviews").glob("release-*.md"))
        self.assertEqual(len(reports), 1)
        report = read(self.workdir / "build" / "export-report.md")
        self.assertIn("release gate: 合格", report)

    def test_out_dir_keeps_only_publications(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--txt", "--epub")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        names = sorted(path.name for path in (self.workdir / "out").iterdir())
        self.assertEqual(names, ["星の名前.epub", "星の名前.md", "星の名前.txt"])

    def test_json_on_lint_failure(self):
        """--json は lint 失敗時も JSON を出し、out/ に書かない。"""
        scene = self.workdir / "scenes" / "1-2.md"
        scene.write_text(read(scene) + "\n出典: https://example.com/x を参照。\n",
                        encoding="utf-8")
        self.out_md.unlink()
        proc = run_tool("export.py", "--workdir", self.workdir, "--json")
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["reason"], "lint")
        self.assertTrue(data["errors"])
        self.assertFalse(self.out_md.exists())

    def test_json_on_missing_scene(self):
        (self.workdir / "scenes" / "2-1.md").unlink()
        proc = run_tool("export.py", "--workdir", self.workdir, "--json")
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertEqual(data["reason"], "missing_scenes")
        self.assertEqual(data["missing"], ["2-1"])

    def test_release_failure_keeps_out_untouched(self):
        """--release が不合格なら out/ を一切変更しない (staging 経由)。"""
        import hashlib

        def md5(path: Path) -> str:
            return hashlib.md5(path.read_bytes()).hexdigest()

        before = md5(self.out_md)
        (self.workdir / "reviews" / "beta-第1話-20261117.md").unlink()
        proc = run_tool("export.py", "--workdir", self.workdir, "--release",
                        "--txt", "--no-report")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(md5(self.out_md), before)
        self.assertFalse((self.workdir / "out" / "星の名前.txt").exists())
        self.assertFalse((self.workdir / "build" / "staging").exists())
        report = read(self.workdir / "build" / "export-report.md")
        self.assertIn("出力: なし", report)

    def test_release_success_moves_from_staging(self):
        proc = run_tool("export.py", "--workdir", self.workdir, "--release",
                        "--txt", "--no-report")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse((self.workdir / "build" / "staging").exists())
        self.assertTrue((self.workdir / "out" / "星の名前.md").is_file())
        self.assertTrue((self.workdir / "out" / "星の名前.txt").is_file())

    def test_release_updates_stale_out(self):
        """scenes/ 更新後に古い out/*.md が残っていても --release で安全に差し替えられる。"""
        scene = self.workdir / "scenes" / "1-1.md"
        scene.write_text(read(scene) + "\n波の音が、石段の奥まで響いた。\n", encoding="utf-8")
        proc = run_tool("export.py", "--workdir", self.workdir, "--release",
                        "--txt", "--no-report")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("波の音が、石段の奥まで響いた。", read(self.out_md))

    def test_plan_error_mentions_v1_rename(self):
        plan = self.workdir / "plan" / "tree.md"
        plan.write_text("| 1 | I | 灯 | reviewed |\n", encoding="utf-8")
        proc = run_tool("export.py", "--workdir", self.workdir)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("N-1.md", proc.stderr)
        self.assertIn("MIGRATION", proc.stderr)

    def test_workdir_missing_exit_2(self):
        proc = run_tool("export.py", "--workdir", fixture("does-not-exist"))
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
