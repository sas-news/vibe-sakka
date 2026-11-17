#!/usr/bin/env python3
"""init_work.py — templates/ から作品ディレクトリの骨格を生成する.

仕様の正本は docs/DESIGN.md §5.4、使い方の正本は tools/README.md。

    python3 tools/init_work.py <target-dir> --title "..." \
        [--mode short|serial] [--force] [--json]

既存ディレクトリは --force がない限り拒否する。
--force は「既存ディレクトリでも続行し、存在しないファイルだけ作る」
(既存ファイルは上書きしない)。終了コード: 0 = 生成 / 2 = 使い方・IO エラー。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATES = TOOL_DIR.parent / "templates"

#: 作品ディレクトリに必ず作るディレクトリ。
DIRECTORIES = (
    "canon",
    "plan",
    "contracts",
    "scenes",
    "scenes/history",
    "proposals",
    "changesets",
    "reviews",
    "research",
    "scratch",
    "out",
    "build",
    "craft",
)

#: templates/ のファイル → 作品ディレクトリ内の配置先。
TEMPLATE_MAP = {
    "work.md": "work.md",
    "canon-facts.md": "canon/facts.md",
    "canon-history.md": "canon/history.md",
    "entities.md": "entities.md",
    "knowledge.md": "knowledge.md",
    "events.md": "events.md",
    "foreshadowing.md": "foreshadowing.md",
    "plan-tree.md": "plan/tree.md",
    "dialogue.md": "dialogue.md",
}

#: craft テンプレート (未作成でも落ちないようにフォールバックを持つ)。
CRAFT_TEMPLATES = {
    "craft-engine.md": ("craft/engine.md", "物語エンジン"),
    "craft-voice.md": ("craft/voice.md", "文体の声"),
}

YAML_TITLE_RE = re.compile(r"(?m)^title:.*$")
YAML_MODE_RE = re.compile(r"(?m)^mode:.*$")
YAML_STATUS_RE = re.compile(r"(?m)^status:.*$")


class InitError(Exception):
    """生成を続けられない (使い方・IO エラー)。"""


def _yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def fill_work_md(template: str, title: str, mode: str) -> str:
    """work.md の雛形に title / mode / status: setup を埋める。"""
    text = template
    if YAML_TITLE_RE.search(text):
        text = YAML_TITLE_RE.sub(f"title: {_yaml_quote(title)}", text, count=1)
        if YAML_MODE_RE.search(text):
            text = YAML_MODE_RE.sub(f"mode: {mode}", text, count=1)
        else:
            # title 行の直後に mode を差し込む
            text = YAML_TITLE_RE.sub(
                lambda match: f"{match.group(0)}\nmode: {mode}", text, count=1)
    else:
        text = f"title: {_yaml_quote(title)}\nmode: {mode}\n" + text
    if YAML_STATUS_RE.search(text):
        text = YAML_STATUS_RE.sub("status: setup", text, count=1)
    else:
        text = YAML_MODE_RE.sub(lambda match: f"{match.group(0)}\nstatus: setup",
                                text, count=1)
    return text


def fallback_craft(title: str, heading: str) -> str:
    """craft テンプレートが未作成のときの最小骨格。"""
    return (
        f"# {title}\n\n"
        f"> テンプレート (templates/) が見つからなかったため、init_work.py が"
        f"最小骨格を作成した。\n"
        f"> `.agents/skills/init-work` の手順で「{heading}」を記入してから執筆を始める。\n"
        "\n"
        "## 記入欄\n"
        "\n"
        "- (未記入)\n"
    )


def _write_new_file(path: Path, content: str) -> bool:
    """存在しないファイルだけ書く。書いたら True。"""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def init_work(target: Path, title: str, mode: str, force: bool,
              templates: Path) -> list[str]:
    """作品骨格を生成し、作成したファイル (相対パス) の一覧を返す。"""
    if target.exists():
        if not target.is_dir():
            raise InitError(f"指定先がファイルです: {target}")
        if not force:
            raise InitError(
                f"既存ディレクトリのため拒否しました: {target}\n"
                f"続行するには --force を付けてください (存在しないファイルだけ作ります)")
    if not templates.is_dir():
        raise InitError(f"templates/ が見つかりません: {templates}")

    created: list[str] = []
    target.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (target / directory).mkdir(parents=True, exist_ok=True)

    for template_name, relative in TEMPLATE_MAP.items():
        source = templates / template_name
        if not source.is_file():
            if template_name == "work.md":
                raise InitError(f"必須テンプレートがありません: {source}")
            continue
        content = source.read_text(encoding="utf-8")
        if relative == "work.md":
            content = fill_work_md(content, title, mode)
        if _write_new_file(target / relative, content):
            created.append(relative)

    for template_name, (relative, heading) in CRAFT_TEMPLATES.items():
        source = templates / template_name
        content = source.read_text(encoding="utf-8") if source.is_file() else ""
        if not content.strip():
            content = fallback_craft(heading, heading)
        if _write_new_file(target / relative, content):
            created.append(relative)

    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="init_work.py",
        description="templates/ から作品ディレクトリの骨格を生成する。",
    )
    parser.add_argument("target", metavar="TARGET-DIR", help="生成先ディレクトリ")
    parser.add_argument("--title", required=True, help="作品タイトル")
    parser.add_argument("--mode", choices=("short", "serial"), default="short",
                        help="執筆モード (既定: short)")
    parser.add_argument("--force", action="store_true",
                        help="既存ディレクトリでも続行する (既存ファイルは上書きしない)")
    parser.add_argument("--templates", metavar="DIR", default=None,
                        help="templates/ の場所 (既定: キットの templates/)")
    parser.add_argument("--json", action="store_true", help="結果を JSON で出す")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target)
    templates = Path(args.templates) if args.templates else DEFAULT_TEMPLATES
    try:
        created = init_work(target, args.title, args.mode, args.force, templates)
    except InitError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"エラー: 生成に失敗しました: {exc}", file=sys.stderr)
        return 2
    if args.json:
        data = {
            "ok": True,
            "workdir": str(target),
            "title": args.title,
            "mode": args.mode,
            "created": created,
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"生成しました: {target}")
        print(f"  作品: {args.title} / モード: {args.mode}")
        for relative in created:
            print(f"  作成: {relative}")
        if not created:
            print("  作成: なし (既存ファイルのみ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
