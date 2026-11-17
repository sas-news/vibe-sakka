"""release_gate.py の self-test。

fixtures: export_work/ (v2 合格) / gate_ng/ (v2 不合格) /
gate_legacy_ok/ (v1 互換で合格)。ネットワーク・git に依存しない。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import release_gate  # noqa: E402
from testlib import copy_fixture, read, run_tool  # noqa: E402

TODAY = "2026-11-17"


class GateTestBase(unittest.TestCase):
    fixture_name = "export_work"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workdir = Path(self._tmp.name) / "work"
        copy_fixture(self.fixture_name, self.workdir)

    def tearDown(self):
        self._tmp.cleanup()

    def run_gate(self, *extra):
        return run_tool("release_gate.py", "--workdir", self.workdir,
                        "--today", TODAY, *extra)


class GateV2OkTest(GateTestBase):
    fixture_name = "export_work"

    def test_passes(self):
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("release gate: 合格", proc.stdout)

    def test_report_written(self):
        self.run_gate()
        report = self.workdir / "reviews" / "release-20261117.md"
        self.assertTrue(report.is_file())
        text = read(report)
        self.assertIn("release gate レポート", text)
        self.assertIn("合格", text)
        self.assertIn("| out | OK |", text)

    def test_json(self):
        proc = self.run_gate("--json")
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["errors"], [])
        self.assertTrue(data["report"].endswith("release-20261117.md"))

    def test_module_check_does_not_require_cli(self):
        result = release_gate.check(self.workdir, today=date(2026, 11, 17),
                                    write_report_file=False)
        self.assertTrue(result.ok, result.errors)
        self.assertIsNone(result.report_path)


class GateV2NgTest(GateTestBase):
    fixture_name = "gate_ng"

    def test_fails_with_all_reasons(self):
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        output = proc.stdout
        self.assertIn("status が active ではありません", output)
        self.assertIn("「面白さの設計」が空", output)
        self.assertIn("craft/engine.md がありません", output)
        self.assertIn("contracts/1-2.md がありません", output)
        self.assertIn("polished: true ではありません", output)
        self.assertIn("回収期限を過ぎた", output)
        self.assertIn("reviews/polish-*.md がありません", output)
        self.assertIn("企画書.md", output)
        self.assertIn("mk_epub.py", output)

    def test_report_is_written_even_when_failing(self):
        self.run_gate()
        report = self.workdir / "reviews" / "release-20261117.md"
        self.assertTrue(report.is_file())
        self.assertIn("不合格", read(report))

    def test_title_aware_out_check(self):
        """md でも作品タイトル以外の名前は out/ 汚染として落とす。"""
        result = release_gate.check(self.workdir, today=date(2026, 11, 17),
                                    write_report_file=False)
        self.assertTrue(any("企画書.md" in message for message in result.errors))


class GateLegacyTest(GateTestBase):
    fixture_name = "gate_legacy_ok"

    def test_legacy_passes_with_warnings(self):
        proc = self.run_gate("--legacy")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("release gate: 合格", proc.stdout)
        self.assertIn("GATE W", proc.stdout)
        self.assertIn("--legacy", proc.stdout)

    def test_v2_mode_is_stricter(self):
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("craft/engine.md がありません", proc.stdout)
        self.assertIn("polished: true ではありません", proc.stdout)


class GateCliTest(unittest.TestCase):
    def test_missing_workdir_exit_2(self):
        proc = run_tool("release_gate.py", "--workdir",
                        Path(tempfile.gettempdir()) / "no-such-workdir")
        self.assertEqual(proc.returncode, 2)

    def test_bad_today_exit_2(self):
        proc = run_tool("release_gate.py", "--workdir", Path(tempfile.gettempdir()),
                        "--today", "2026/11/17")
        self.assertEqual(proc.returncode, 2)

    def test_empty_dir_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_tool("release_gate.py", "--workdir", tmp,
                            "--today", TODAY)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("work.md がありません", proc.stdout)


if __name__ == "__main__":
    unittest.main()
