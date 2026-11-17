"""init_work.py の self-test。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import init_work  # noqa: E402
from testlib import read, run_tool  # noqa: E402

EXPECTED_DIRS = (
    "canon", "plan", "contracts", "scenes", "scenes/history", "proposals",
    "changesets", "reviews", "research", "scratch", "out", "build", "craft",
)
EXPECTED_FILES = (
    "work.md", "canon/facts.md", "canon/history.md", "entities.md",
    "knowledge.md", "events.md", "foreshadowing.md", "plan/tree.md",
    "dialogue.md", "craft/engine.md", "craft/voice.md",
)


class InitWorkTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name) / "新しい作品"

    def tearDown(self):
        self._tmp.cleanup()

    def test_generates_skeleton(self):
        proc = run_tool("init_work.py", self.target, "--title", "星の名前",
                        "--mode", "serial")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for relative in EXPECTED_DIRS:
            self.assertTrue((self.target / relative).is_dir(), relative)
        for relative in EXPECTED_FILES:
            self.assertTrue((self.target / relative).is_file(), relative)

    def test_work_md_fields(self):
        proc = run_tool("init_work.py", self.target, "--title", "星の名前")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        text = read(self.target / "work.md")
        self.assertIn('title: "星の名前"', text)
        self.assertIn("status: setup", text)
        self.assertIn("mode: short", text)

    def test_existing_dir_refused(self):
        self.target.mkdir()
        proc = run_tool("init_work.py", self.target, "--title", "断られる")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--force", proc.stderr)

    def test_force_does_not_overwrite(self):
        self.assertEqual(run_tool("init_work.py", self.target, "--title", "最初")
                         .returncode, 0)
        work_md = self.target / "work.md"
        original = read(work_md)
        proc = run_tool("init_work.py", self.target, "--title", "二度目", "--force")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(read(work_md), original)
        self.assertIn("作成: なし", proc.stdout)

    def test_json_output(self):
        proc = run_tool("init_work.py", self.target, "--title", "星の名前", "--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertIn("work.md", data["created"])
        self.assertEqual(data["workdir"], str(self.target))

    def test_mode_validation(self):
        proc = run_tool("init_work.py", self.target, "--title", "x", "--mode", "long")
        self.assertEqual(proc.returncode, 2)

    def test_module_api(self):
        created = init_work.init_work(self.target, "題", "short", False,
                                      init_work.DEFAULT_TEMPLATES)
        self.assertIn("work.md", created)
        self.assertTrue((self.target / "craft" / "engine.md").is_file())


if __name__ == "__main__":
    unittest.main()
