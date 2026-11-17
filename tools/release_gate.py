#!/usr/bin/env python3
"""release_gate.py — 公開ゲート (決定論的). Python 3 標準ライブラリのみ.

仕様の正本は docs/DESIGN.md §5.3、使い方の正本は tools/README.md。

    python3 tools/release_gate.py [--workdir .] [--legacy] [--json]
                                  [--today YYYY-MM-DD]

検査項目: work.md の status と憲章 / craft/ / 契約 approved / scenes の
polished: true / 伏線の回収期限 / 推敲記録 / out/ 清浄 / lint E 0。

終了コード: 0 = 合格 / 1 = 不合格 / 2 = 使い方・IO エラー。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import manuscript_lint

CHAPTER_RE = re.compile(r"^##\s+第(\d+)話(?:\s+(.*))?$")
SCENE_LINE_RE = re.compile(r"^[-*]\s+シーン\s+`?(\d+)-(\d+)`?")
STATUS_YAML_RE = re.compile(r"(?mi)^\s*[-*]?\s*status\s*:\s*\**\s*([A-Za-z_-]+)")
POLISHED_RE = re.compile(r"(?mi)^\s*[-*]?\s*polished\s*:\s*\**\s*(true|false)\**\s*$")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
YAML_FENCE_RE = re.compile(r"^```ya?ml\s*$", re.IGNORECASE)
FENCE_END_RE = re.compile(r"^```\s*$")
ALLOWED_OUT_SUFFIXES = (".md", ".txt", ".epub")

#: 憲章で「空でないこと」を要求する節 (v2)。v1 では警告に落とす。
CHARTER_KEYWORDS = ("面白さの設計", "禁じ手", "声")


class GateResult:
    """公開ゲートの結果。"""

    def __init__(self, workdir: Path, legacy: bool) -> None:
        self.workdir = workdir
        self.legacy = legacy
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: list[dict] = []
        self.report_path: Path | None = None
        self.lint_errors = 0
        self.lint_warnings = 0
        self.checked_manuscripts: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, check: str, message: str) -> None:
        self.errors.append(f"{check}: {message}")
        self._record(check, "error", message)

    def warn(self, check: str, message: str) -> None:
        self.warnings.append(f"{check}: {message}")
        self._record(check, "warn", message)

    def allow(self, check: str, message: str) -> None:
        self._record(check, "ok", message)

    def _record(self, check: str, status: str, detail: str) -> None:
        self.checks.append({"check": check, "status": status, "detail": detail})

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "legacy": self.legacy,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
            "manuscripts": self.checked_manuscripts,
            "report": None if self.report_path is None else str(self.report_path),
        }


# ---------------------------------------------------------------------------
# 個別検査
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _yaml_block(text: str) -> str:
    """最初の ```yaml ... ``` ブロックの中身 (なければ全文)。"""
    lines = text.splitlines()
    in_yaml = False
    block: list[str] = []
    for line in lines:
        if YAML_FENCE_RE.match(line):
            in_yaml = True
            continue
        if in_yaml and FENCE_END_RE.match(line):
            return "\n".join(block)
        if in_yaml:
            block.append(line)
    return text if not block else "\n".join(block)


def _value_after_colon(line: str) -> str:
    """`- **声**: 静かで…` から値を取り出す (Markdown 装飾を落とす)。"""
    if ":" in line or "：" in line:
        value = re.split(r"[:：]", line, maxsplit=1)[-1]
    else:
        value = ""
    value = value.replace("*", "").replace("`", "").strip()
    return value


def section_filled(text: str, keyword: str) -> bool:
    """keyword を含む節・行に実質的な内容があるか。"""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if keyword not in line:
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            for follow in lines[index + 1:]:
                follow = follow.strip()
                if not follow:
                    continue
                if follow.startswith("#"):
                    break
                candidate = _value_after_colon(follow) or follow
                if len(re.sub(r"[\s、。・（）()【】\-*]", "", candidate)) >= 3:
                    return True
        else:
            candidate = _value_after_colon(stripped)
            if len(re.sub(r"[\s、。・（）()【】\-*]", "", candidate)) >= 3:
                return True
    return False


def check_work_md(result: GateResult) -> None:
    """work.md: status active / 憲章の「面白さの設計」「禁じ手」「声」。"""
    path = result.workdir / "work.md"
    if not path.is_file():
        result.error("work.md", "work.md がありません")
        return
    text = _read(path)
    yaml_text = _yaml_block(text)
    status_match = STATUS_YAML_RE.search(yaml_text)
    status = status_match.group(1).lower() if status_match else ""
    if status != "active":
        result.error("work.md", f"status が active ではありません (status: {status or '不明'})")
    else:
        result.allow("work.md", "status: active")
    for keyword in CHARTER_KEYWORDS:
        if section_filled(text, keyword):
            continue
        message = f"憲章の「{keyword}」が空です"
        if result.legacy:
            result.warn("work.md", message + " (--legacy のため警告)")
        else:
            result.error("work.md", message)


def check_craft(result: GateResult) -> None:
    """craft/engine.md と craft/voice.md の存在 (legacy は警告)。"""
    for name in ("craft/engine.md", "craft/voice.md"):
        path = result.workdir / name
        if path.is_file() and _read(path).strip():
            result.allow("craft", f"{name} あり")
            continue
        message = f"{name} がありません (物語エンジン・声の設計)"
        if result.legacy:
            result.warn("craft", message + " (--legacy のため警告)")
        else:
            result.error("craft", message)


def parse_plan_scene_ids(tree_path: Path) -> list[str]:
    """plan/tree.md から `E-S` の公開順を読む (export.py と同じ書式)。"""
    scene_ids: list[str] = []
    current_episode: int | None = None
    for line in _read(tree_path).splitlines():
        chapter = CHAPTER_RE.match(line)
        if chapter:
            current_episode = int(chapter.group(1))
            continue
        scene = SCENE_LINE_RE.match(line)
        if scene and current_episode is not None:
            scene_ids.append(f"{int(scene.group(1))}-{int(scene.group(2))}")
    return scene_ids


def check_plan(result: GateResult) -> list[str]:
    """計画・契約・本文・polished の検査。検査したシーンIDを返す。"""
    tree_path = result.workdir / "plan" / "tree.md"
    if not tree_path.is_file():
        result.error("plan", "plan/tree.md がありません")
        return []
    scene_ids = parse_plan_scene_ids(tree_path)
    if not scene_ids:
        if result.legacy:
            scene_ids = sorted(
                (path.stem for path in (result.workdir / "scenes").glob("*.md")),
                key=_scene_sort_key,
            )
            if scene_ids:
                result.warn("plan", "plan/tree.md を解析できないため scenes/*.md で代用しました "
                                    "(--legacy)")
            else:
                result.error("plan", "plan/tree.md を解析できず、scenes/*.md もありません")
        else:
            result.error("plan", "plan/tree.md から公開順を解析できません")
        return scene_ids

    for scene_id in scene_ids:
        contract = result.workdir / "contracts" / f"{scene_id}.md"
        if not contract.is_file():
            result.error("contract", f"contracts/{scene_id}.md がありません")
        else:
            match = STATUS_YAML_RE.search(_yaml_block(_read(contract)))
            if not match or match.group(1).lower() != "approved":
                got = match.group(1) if match else "なし"
                result.error("contract", f"contracts/{scene_id}.md の status が approved では"
                                         f"ありません (status: {got})")
        scene = result.workdir / "scenes" / f"{scene_id}.md"
        if not scene.is_file():
            result.error("scenes", f"scenes/{scene_id}.md がありません")
            continue
        match = POLISHED_RE.search(_yaml_block(_read(scene)))
        polished = bool(match) and match.group(1).lower() == "true"
        if not polished:
            message = f"scenes/{scene_id}.md が polished: true ではありません (推敲未実施)"
            if result.legacy:
                result.warn("polish", message + " (--legacy のため警告)")
            else:
                result.error("polish", message)
    if scene_ids:
        result.allow("plan", f"{len(scene_ids)} シーンを計画から確認")
    return scene_ids


def _scene_sort_key(name: str) -> tuple[int, int]:
    match = re.match(r"^(\d+)-(\d+)$", name)
    if not match:
        return (10 ** 6, 10 ** 6)
    return (int(match.group(1)), int(match.group(2)))


def check_foreshadowing(result: GateResult, today: date) -> None:
    """foreshadowing.md: planted のまま回収期限を過ぎたもの。"""
    path = result.workdir / "foreshadowing.md"
    if not path.is_file():
        message = "foreshadowing.md がありません (伏線台帳)"
        if result.legacy:
            result.warn("foreshadowing", message + " (--legacy のため警告)")
        else:
            result.error("foreshadowing", message)
        return
    text = _read(path)
    # `- (fs01) [planted] … 期限: 2026-12-01` の塊ごとに見る
    chunks = re.split(r"(?m)^(?=- \(fs)", text)
    overdue: list[str] = []
    for chunk in chunks:
        if not re.search(r"\[planted\]", chunk):
            continue
        for year, month, day in DATE_RE.findall(chunk):
            try:
                deadline = date(int(year), int(month), int(day))
            except ValueError:
                continue
            if deadline < today:
                label = re.search(r"\(fs\d+\)", chunk)
                overdue.append(f"{label.group(0) if label else '伏線'} (期限 {deadline})")
    if overdue:
        result.error("foreshadowing", "回収期限を過ぎた planted の伏線があります: "
                                      + ", ".join(overdue))
    else:
        result.allow("foreshadowing", "回収期限超過なし")


def check_polish_records(result: GateResult) -> None:
    """reviews/polish-*.md が1件以上あること。"""
    reviews = result.workdir / "reviews"
    records = sorted(reviews.glob("polish-*.md")) if reviews.is_dir() else []
    if records:
        result.allow("polish", f"推敲記録 {len(records)} 件")
    else:
        result.error("polish", "reviews/polish-*.md がありません (推敲記録が必須)")


def load_title(workdir: Path) -> str:
    """work.md の YAML から作品タイトルを読む (なければ空文字)。"""
    work_md = workdir / "work.md"
    if not work_md.is_file():
        return ""
    for line in _read(work_md).splitlines():
        match = re.match(r"^title:\s*\"?(.*?)\"?\s*(?:#.*)?$", line)
        if match:
            return match.group(1).strip()
    return ""


def check_out_dir(result: GateResult, extra_names: set[str] | None = None) -> None:
    """out/ が公開物のみか。作品タイトルの `<title>.md/.txt/.epub` 以外は不可。"""
    out_dir = result.workdir / "out"
    if not out_dir.is_dir():
        result.error("out", "out/ がありません")
        return
    title = load_title(result.workdir)
    allowed: set[str] = set(extra_names or ())
    if title:
        # export.py と同じ安全化 (タイトルに使えない文字を _ に置換)
        safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", title).strip().strip(".") or "manuscript"
        for base in {title, safe}:
            allowed |= {f"{base}{suffix}" for suffix in ALLOWED_OUT_SUFFIXES}
    else:
        result.warn("out", "work.md にタイトルがないため out/ の名前検査を省略しました")
    bad: list[str] = []
    for path in sorted(out_dir.iterdir()):
        if path.is_dir():
            bad.append(f"{path.name}/")
        elif path.suffix.lower() not in ALLOWED_OUT_SUFFIXES:
            bad.append(path.name)
        elif title and path.name not in allowed:
            bad.append(f"{path.name} (作品タイトル {title} 以外の .md/.txt/.epub)")
    if bad:
        result.error("out", "out/ に公開物以外があります "
                            f"(<title>.md/.txt/.epub のみ可): " + ", ".join(bad))
    else:
        result.allow("out", "out/ は公開物のみ")


def check_lint(result: GateResult) -> None:
    """out/ の原稿を lint して E 0 件か。"""
    out_dir = result.workdir / "out"
    manuscripts = sorted(out_dir.glob("*.md")) if out_dir.is_dir() else []
    if not manuscripts:
        result.error("lint", "out/ に原稿 (.md) がありません")
        return
    total_errors = 0
    total_warnings = 0
    for path in manuscripts:
        report = manuscript_lint.lint_files(
            [path], workdir=result.workdir, legacy=result.legacy)
        total_errors += len(report.errors)
        total_warnings += len(report.warnings)
        result.checked_manuscripts.append(str(path))
        for finding in report.errors[:20]:
            result.errors.append(f"lint: {finding.format()}")
            result._record("lint", "error", finding.format())
    result.lint_errors = total_errors
    result.lint_warnings = total_warnings
    if total_errors == 0:
        result.allow("lint", f"E 0 / W {total_warnings}")


# ---------------------------------------------------------------------------
# レポート
# ---------------------------------------------------------------------------


def write_report(result: GateResult, today: date) -> Path:
    reviews = result.workdir / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    path = reviews / f"release-{today.strftime('%Y%m%d')}.md"
    mark = {"ok": "OK", "warn": "WARN", "error": "NG"}
    lines = [
        f"# release gate レポート ({today.isoformat()})",
        "",
        f"- 作品ディレクトリ: {result.workdir}",
        f"- モード: {'legacy (v1 互換)' if result.legacy else 'v2'}",
        f"- 判定: {'合格' if result.ok else '不合格'}",
        f"- lint: E {result.lint_errors} / W {result.lint_warnings}",
        "",
        "## 検査結果",
        "",
        "| 検査 | 判定 | 内容 |",
        "| --- | --- | --- |",
    ]
    for check in result.checks:
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| {check['check']} | {mark.get(check['status'], check['status'])} "
                     f"| {detail} |")
    if result.errors:
        lines += ["", "## 不合格の理由", ""]
        lines += [f"- {message}" for message in result.errors]
    if result.warnings:
        lines += ["", "## 警告 (合格は妨げない)", ""]
        lines += [f"- {message}" for message in result.warnings]
    lines += [
        "",
        "## 次にやること",
        "",
        "- NG があれば作者に「何が落ちたか」を選択肢付きで報告する。",
        "- ゲートを通さず公開しない。修正後に再実行する。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 本体
# ---------------------------------------------------------------------------


def check(workdir: Path, legacy: bool = False, today: date | None = None,
          write_report_file: bool = True,
          extra_out_names: set[str] | None = None) -> GateResult:
    """公開ゲートを実行する。レポートも書く。

    extra_out_names: out/ で追加許可するファイル名 (export.py --release が
    自分の出力を許可するために使う)。
    """
    result = GateResult(workdir, legacy)
    if not workdir.is_dir():
        result.error("workdir", f"作品ディレクトリがありません: {workdir}")
        return result
    check_work_md(result)
    check_craft(result)
    check_plan(result)
    check_foreshadowing(result, today or date.today())
    check_polish_records(result)
    check_out_dir(result, extra_out_names)
    check_lint(result)
    if write_report_file:
        try:
            result.report_path = write_report(result, today or date.today())
        except OSError as exc:
            result.warn("report", f"レポートを書けません: {exc}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="release_gate.py",
        description="公開前ゲート。1つでも error があれば exit 1。",
    )
    parser.add_argument("--workdir", default=".", metavar="DIR",
                        help="作品ディレクトリ (既定: カレント)")
    parser.add_argument("--legacy", action="store_true", help="v1 作品の互換モード")
    parser.add_argument("--json", action="store_true", help="結果を JSON で出す")
    parser.add_argument("--today", metavar="YYYY-MM-DD",
                        help="基準日 (伏線期限の判定とレポート名。既定: 今日)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workdir = Path(args.workdir)
    if not workdir.is_dir():
        print(f"エラー: --workdir が見つかりません: {workdir}", file=sys.stderr)
        return 2
    today = date.today()
    if args.today:
        try:
            today = datetime.strptime(args.today, "%Y-%m-%d").date()
        except ValueError:
            print(f"エラー: --today は YYYY-MM-DD で指定してください: {args.today}",
                  file=sys.stderr)
            return 2
    result = check(workdir, legacy=args.legacy, today=today)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        for message in result.errors:
            print(f"GATE E: {message}")
        for message in result.warnings:
            print(f"GATE W: {message}")
        print(f"release gate: {'合格' if result.ok else '不合格'} "
              f"(E {len(result.errors)} / W {len(result.warnings)})")
        if result.report_path is not None:
            print(f"レポート: {result.report_path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
