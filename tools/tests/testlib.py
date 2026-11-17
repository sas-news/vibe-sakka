"""tools/tests 共通のテスト補助 (外部依存なし)。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def run_tool(name: str, *args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """tools/<name> を CLI として実行する (ネットワーク・git 非依存)。"""
    command = [sys.executable, str(TOOLS_DIR / name), *[str(arg) for arg in args]]
    return subprocess.run(command, capture_output=True, text=True,
                          cwd=str(cwd) if cwd else None)


def fixture(name: str) -> Path:
    return FIXTURES_DIR / name


def copy_fixture(name: str, destination: Path) -> Path:
    """fixture を一時ディレクトリにコピーして返す (fixture を書き換えない)。"""
    source = fixture(name)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)
    return destination


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def codes(output: str) -> set[str]:
    """lint のテキスト出力から検査コード (L001 等) を集める。"""
    found: set[str] = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("E", "W") and parts[1][:1] in ("L", "W"):
            found.add(parts[1])
    return found


def boot():
    """sys.path に tools/ と tests/ を足す (テストファイルの先頭で呼ぶ)。"""
    for path in (str(TOOLS_DIR), str(Path(__file__).resolve().parent)):
        if path not in sys.path:
            sys.path.insert(0, path)
