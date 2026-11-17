#!/usr/bin/env python3
"""selftest.py — tools/tests/ の unittest を実行する self-test ランナー.

    python3 tools/selftest.py            # 全テスト
    python3 tools/selftest.py -v         # unittest の詳細表示
    python3 tools/selftest.py test_lint  # テストモジュールを絞る

外部依存なし (unittest のみ)。ネットワーク・git に依存しない。
終了コード: 0 = 全テスト成功 / 1 = 失敗。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TESTS_DIR = TOOLS_DIR / "tests"


def build_suite(pattern: str | None = None) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    if pattern:
        return loader.loadTestsFromNames([pattern])
    return loader.discover(str(TESTS_DIR), pattern="test_*.py",
                           top_level_dir=str(TESTS_DIR))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    verbosity = 2 if "-v" in argv else 1
    names = [arg for arg in argv if not arg.startswith("-")]
    for path in (str(TOOLS_DIR), str(TESTS_DIR)):
        if path not in sys.path:
            sys.path.insert(0, path)
    pattern = names[0] if names else None
    if pattern and not pattern.startswith("test_"):
        pattern = f"test_{pattern}"
    try:
        suite = build_suite(pattern)
    except Exception as exc:  # テストモジュールの import 失敗
        print(f"self-test を開始できません: {exc}", file=sys.stderr)
        return 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    if result.wasSuccessful():
        print(f"OK: {result.testsRun} tests, "
              f"{len(result.skipped)} skipped")
        return 0
    print(f"FAILED: {len(result.failures)} failures, "
          f"{len(result.errors)} errors (of {result.testsRun} tests)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
