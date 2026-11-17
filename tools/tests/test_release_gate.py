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
from testlib import FIXTURES_DIR, copy_fixture, read, run_tool  # noqa: E402

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


class GateContractContentTest(GateTestBase):
    """ゲート検査の穴 (監査 Must fix) の回帰テスト。"""

    fixture_name = "export_work"

    def test_txt_is_linted(self):
        """out/*.txt の URL / (了) 重複も検出する (fast M1)。"""
        bad = self.workdir / "out" / "星の名前.txt"
        bad.write_text("# 星の名前\n\n出典: https://example.com/x\n\n(了)\n\n(了)\n",
                       encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("L001", proc.stdout)
        self.assertIn("L009", proc.stdout)

    def test_scenes_are_linted(self):
        """scenes/ の E (L009) は out がクリーンでも不合格 (deep M3)。"""
        scene = self.workdir / "scenes" / "1-2.md"
        scene.write_text(read(scene) + "\n(了)\n\n(了)\n", encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("L009", proc.stdout)
        self.assertIn("scenes", proc.stdout)
        exported = run_tool("export.py", "--workdir", self.workdir, "--md",
                            "--no-report")
        self.assertEqual(exported.returncode, 1)

    def test_beta_required(self):
        """非 legacy では beta 記録が必須 (fast M2)。"""
        (self.workdir / "reviews" / "beta-第1話-20261117.md").unlink()
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("beta", proc.stdout)
        self.assertIn("beta-*.md", proc.stdout)

    def test_beta_external_required(self):
        """external でない記録は error (未実施・自己採点を止める)。"""
        beta = self.workdir / "reviews" / "beta-第1話-20261117.md"
        beta.write_text("# beta\n\n```yaml\ncontext: self\ninterest_gate: pass\n```\n"
                        "\n| 1 | 冒頭フック | 3 | 「灯台」 |\n", encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("external", proc.stdout)

    def test_beta_score_required(self):
        """スコアカードの採点行がない記録は error。"""
        beta = self.workdir / "reviews" / "beta-第1話-20261117.md"
        beta.write_text("# beta\n\n```yaml\ncontext: external\ninterest_gate: pass\n```\n",
                        encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("スコアの記載", proc.stdout)

    def test_interest_fail_is_warning_not_error(self):
        """interest_gate: fail は警告で合格 (公開可否は作者判断)。"""
        beta = self.workdir / "reviews" / "beta-第1話-20261117.md"
        beta.write_text(
            "# beta\n\n```yaml\ncontext: external\ninterest_gate: fail\n```\n"
            "\n| 1 | 冒頭フック | 3 | 「灯台」 |\n"
            "| 3 | 意外性 | 1 | 弱い |\n"
            "- high (0–1): 1件 / medium (2): 2件\n", encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("作者判断で公開可", proc.stdout)
        self.assertIn("interest: fail", proc.stdout)

    def test_polish_content_is_checked(self):
        """空の polish 記録・数値なしは不合格 (fast M2 / deep M4)。"""
        polish = self.workdir / "reviews" / "polish-20261101.md"
        polish.write_text("", encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("空です", proc.stdout)
        polish.write_text("# polish\n\n- 対象: 全シーン\n", encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("before/after", proc.stdout)

    def test_empty_template_work_is_ng(self):
        """templates/work.md を空のままコピーした作品は不合格 (deep M1)。"""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            copy_fixture("gate_template_empty", work)
            proc = run_tool("release_gate.py", "--workdir", work,
                            "--today", TODAY, "--no-report")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("「約束」が空です", proc.stdout)
            self.assertIn("テンプレート未記入", proc.stdout)
            self.assertIn("面白さの設計", proc.stdout)

    def test_foreshadowing_deadline_cases(self):
        """期限: YYYY-MM-DD だけで判定し、張設の日付を誤認しない (deep M5)。"""
        target = self.workdir / "foreshadowing.md"
        # 未来の期限 → 合格
        target.write_text((FIXTURES_DIR / "foreshadowing" / "future.md").read_text(
            encoding="utf-8"), encoding="utf-8")
        self.assertEqual(self.run_gate().returncode, 0)
        # 過去の期限 → 不合格
        target.write_text((FIXTURES_DIR / "foreshadowing" / "past.md").read_text(
            encoding="utf-8"), encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2020-06-01", proc.stdout)
        self.assertNotIn("2020-01-01 (", proc.stdout)  # 張設の日付を期限にしない
        # 期限なし → 合格 (警告のみ)
        target.write_text((FIXTURES_DIR / "foreshadowing" / "no_deadline.md").read_text(
            encoding="utf-8"), encoding="utf-8")
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("未記入の planted", proc.stdout)

    def test_no_report_option(self):
        proc = self.run_gate("--no-report")
        self.assertEqual(proc.returncode, 0)
        self.assertFalse((self.workdir / "reviews" / "release-20261117.md").exists())

    def test_report_mentions_manual_checklist(self):
        self.run_gate()
        report = read(self.workdir / "reviews" / "release-20261117.md")
        self.assertIn("自動生成", report)
        self.assertIn("release-checklist-", report)


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

    def test_legacy_without_polish_beta_fails(self):
        """polish/beta の欠落は legacy でも error (公開判定は緩めない)。"""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            copy_fixture("gate_legacy_ng", work)
            proc = run_tool("release_gate.py", "--workdir", work, "--legacy",
                            "--today", TODAY, "--no-report")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("reviews/polish-*.md がありません", proc.stdout)
            self.assertIn("reviews/beta-*.md がありません", proc.stdout)
            self.assertNotIn("( --legacy のため警告)", proc.stdout)

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
