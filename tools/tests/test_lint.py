"""manuscript_lint.py の self-test。

fixtures は tools/tests/fixtures/。ネットワーク・git に依存しない。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import manuscript_lint  # noqa: E402
from testlib import codes, copy_fixture, fixture, read, run_tool  # noqa: E402


class LintFixtureTest(unittest.TestCase):
    """fixture ごとの検査コード。"""

    def test_good_is_clean(self):
        """good.md は E 0 で exit 0。"""
        proc = run_tool("manuscript_lint.py", fixture("good.md"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("E 0", proc.stdout)

    def test_url_and_sources(self):
        """bad_url.md: URL・出典ラベルを L001 で検出する。"""
        proc = run_tool("manuscript_lint.py", fixture("bad_url.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("L001", codes(proc.stdout))
        self.assertIn("出典", proc.stdout)

    def test_outline_beats(self):
        """bad_outline.md: ビート見出し「一」・【…】・本文見出し・制作メモを L003。"""
        proc = run_tool("manuscript_lint.py", fixture("bad_outline.md"))
        self.assertEqual(proc.returncode, 1)
        found = codes(proc.stdout)
        self.assertIn("L003", found)
        self.assertIn("ビート見出し「一」", proc.stdout)
        self.assertIn("【重要】", proc.stdout)
        self.assertIn("制作メモ", proc.stdout)

    def test_duplicate_blocks(self):
        """bad_dup.md: 同一行と同一文の重複を L004。"""
        proc = run_tool("manuscript_lint.py", fixture("bad_dup.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("L004", codes(proc.stdout))
        self.assertIn("重複", proc.stdout)

    def test_ledger_and_scene_id(self):
        """bad_ledger.md: 台帳メタを L002、scene ID を L011。"""
        proc = run_tool("manuscript_lint.py", fixture("bad_ledger.md"))
        self.assertEqual(proc.returncode, 1)
        found = codes(proc.stdout)
        self.assertIn("L002", found)
        self.assertIn("L011", found)
        self.assertIn("台帳メタ", proc.stdout)
        self.assertIn("p-0001", proc.stdout)

    def test_terminator_and_separator(self):
        """bad_terminator_sep.md: (了) 重複を L009、区切りの混在/連続を L010。"""
        proc = run_tool("manuscript_lint.py", fixture("bad_terminator_sep.md"))
        self.assertEqual(proc.returncode, 1)
        found = codes(proc.stdout)
        self.assertIn("L009", found)
        self.assertIn("L010", found)

    def test_fix_then_clean(self):
        """fixable.md は --fix 後に exit 0 (安全修正のみ)。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "fixable.md"
            copy_fixture("fixable.md", target)
            before = run_tool("manuscript_lint.py", target)
            self.assertEqual(before.returncode, 1)
            fixed = run_tool("manuscript_lint.py", "--fix", target)
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            self.assertIn("fix:", fixed.stdout)
            text = read(target)
            self.assertNotIn("◇", text)
            self.assertEqual(text.count("(了)"), 1)
            self.assertNotIn(" \n", text)

    def test_encoding_bom_crlf(self):
        """BOM + CRLF は L008。--fix で LF/BOM なしに直る。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "encoded.md"
            body = read(fixture("good.md")).replace("\n", "\r\n")
            target.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
            proc = run_tool("manuscript_lint.py", target)
            self.assertEqual(proc.returncode, 1)
            found = codes(proc.stdout)
            self.assertIn("L008", found)
            self.assertIn("BOM", proc.stdout)
            fixed = run_tool("manuscript_lint.py", "--fix", target)
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            raw = target.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r\n", raw)


class StaleExportTest(unittest.TestCase):
    """--workdir による stale export 検査 (L007)。"""

    def test_stale_is_detected(self):
        workdir = fixture("bad_stale")
        manuscript = workdir / "out" / "灯の話.md"
        proc = run_tool("manuscript_lint.py", "--workdir", workdir, manuscript)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("L007", codes(proc.stdout))
        self.assertIn("stale export", proc.stdout)

    def test_fresh_is_not_stale(self):
        """scenes と一致する out 原稿は L007 を出さない。"""
        proc = run_tool("manuscript_lint.py", "--workdir", fixture("export_work"),
                        fixture("export_work") / "out" / "星の名前.md")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("L007", codes(proc.stdout))

    def test_stale_normalization_allows_headings_and_separators(self):
        """見出し・区切り・(了) の差は許容して比較する。"""
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp) / "work"
            shutil.copytree(fixture("export_work"), workdir)
            manuscript = workdir / "out" / "星の名前.md"
            text = read(manuscript)
            text = text.replace("\n\n## 第2話 名前\n\n", "\n\n◆\n\n## 第2話 名前\n\n")
            manuscript.write_text(text + "\n(了)\n", encoding="utf-8")
            proc = run_tool("manuscript_lint.py", "--workdir", workdir, manuscript)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class LintCliTest(unittest.TestCase):
    """CLI / JSON / 終了コード。"""

    def test_json_shape(self):
        proc = run_tool("manuscript_lint.py", "--json", fixture("bad_url.md"))
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        for key in ("errors", "warnings", "infos", "stats"):
            self.assertIn(key, data)
        self.assertTrue(data["errors"])
        first = data["errors"][0]
        for key in ("code", "severity", "file", "line", "message"):
            self.assertIn(key, first)
        for key in ("chars", "scenes", "chapters", "dialogue_ratio", "sentences"):
            self.assertIn(key, data["stats"])

    def test_json_good_has_no_errors(self):
        proc = run_tool("manuscript_lint.py", "--json", fixture("good.md"))
        data = json.loads(proc.stdout)
        self.assertEqual(data["errors"], [])
        self.assertGreaterEqual(data["stats"]["chapters"], 1)

    def test_missing_file_exit_2(self):
        proc = run_tool("manuscript_lint.py", fixture("no-such-file.md"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("見つかりません", proc.stderr)

    def test_legacy_flag_accepted(self):
        proc = run_tool("manuscript_lint.py", "--legacy", fixture("good.md"))
        self.assertEqual(proc.returncode, 0)

    def test_json_with_fix_keeps_stdout_parseable(self):
        """--json --fix でも stdout は JSON だけ (修正ログは stderr)。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "fixable.md"
            copy_fixture("fixable.md", target)
            proc = run_tool("manuscript_lint.py", "--json", "--fix", target)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            self.assertEqual(data["errors"], [])
            self.assertIn("fix:", proc.stderr)

    def test_fix_without_target_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "good.md"
            copy_fixture("good.md", target)
            proc = run_tool("manuscript_lint.py", "--fix", target)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("修正対象はありませんでした", proc.stdout)


class LintUnitTest(unittest.TestCase):
    """モジュール API (export/release_gate が使う)。"""

    def test_lint_text_matches_file(self):
        text = read(fixture("bad_outline.md"))
        report = manuscript_lint.lint_text(text, name="bad_outline.md")
        self.assertFalse(report.ok)
        self.assertIn("L003", {finding.code for finding in report.errors})

    def test_strip_metadata(self):
        text = read(fixture("export_work") / "scenes" / "1-1.md")
        body = manuscript_lint.strip_metadata(text)
        self.assertNotIn("```", body)
        self.assertNotIn("scene:", body)
        self.assertTrue(body.startswith("灯台の石段"))

    def test_l002_id_patterns(self):
        """台帳IDの各パターンを L002 で検出する。"""
        for token in ("f001", "ent-c01", "ev01", "fs01", "ke01",
                      "p-0001", "cs-0001", "work.md", "rev 3"):
            report = manuscript_lint.lint_text(f"本文に {token} が混ざった。", name="x.md")
            self.assertIn("L002", {finding.code for finding in report.errors}, token)

    def test_l001_label_patterns(self):
        """出典・参照・資料・引用・ソース の各ラベルを L001 で検出する。"""
        for label in ("出典", "参照", "資料", "引用", "ソース"):
            report = manuscript_lint.lint_text(f"{label}: 何かの資料", name="x.md")
            self.assertIn("L001", {finding.code for finding in report.errors}, label)

    def test_dialogue_ratio(self):
        text = "「おはよう」\n\nミナはうなずいた。"
        report = manuscript_lint.lint_text(text, name="dialogue.md")
        self.assertGreater(report.stats["dialogue_ratio"], 0)


if __name__ == "__main__":
    unittest.main()
