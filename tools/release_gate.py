#!/usr/bin/env python3
"""release_gate.py — 公開ゲート (決定論的). Python 3 標準ライブラリのみ.

仕様の正本は docs/DESIGN.md §5.3、使い方の正本は tools/README.md。

    python3 tools/release_gate.py [--workdir .] [--legacy] [--json]
                                  [--no-report] [--today YYYY-MM-DD]

検査項目: work.md の status と面白さの設計 (7項目) / craft/ / 契約 approved /
scenes の polished: true / beta 記録 (external・interest_gate: pass) /
推敲記録の中身 / 伏線の回収期限 / out/ 清浄 / out+scenes の lint E 0。

--legacy は **v1 形式の互換のみ** を緩和する (設計7項目・craft・polished・
plan 表形式の欠落を warn)。polish/beta 記録・out/ 清浄・lint E は legacy でも
error (推敲なし・外部読者テストなしの公開を許さない)。

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
YAML_FENCE_RE = re.compile(r"^```ya?ml\s*$", re.IGNORECASE)
FENCE_END_RE = re.compile(r"^```\s*$")
ALLOWED_OUT_SUFFIXES = (".md", ".txt", ".epub")

#: 憲章「面白さの設計」の必須7項目。
CHARTER_ITEMS = ("約束", "冒頭のフック", "ジャンルの快楽", "感情の弧",
                 "禁じ手", "声", "面白さの基準")
#: craft/engine.md の必須要素。
ENGINE_ITEMS = ("約束", "欲求", "対立", "代償", "時計", "快楽", "禁じ手")
#: beta 記録 (外部読者テスト) の必須マーカー。
EXTERNAL_RE = re.compile(r"(?mi)^\s*(?:reader|context)\s*:\s*external\b")
GATE_PASS_RE = re.compile(r"(?mi)^\s*interest_gate\s*:\s*pass\b")
BETA_TARGET_RE = re.compile(r'(?mi)^\s*target\s*:\s*"?([^"#\n]+?)"?\s*(?:#.*)?$')
BETA_DATE_RE = re.compile(r"(?mi)^\s*date\s*:\s*(\d{4}-\d{2}-\d{2})\b")
BETA_NAME_DATE_RE = re.compile(r"-\d{4}-?\d{2}-?\d{2}(?:-r\d+)?$")
#: 推敲記録の数値 (補助線追加等で微増した負の cut_rate も許容)。
BEFORE_RE = re.compile(r"(?mi)^\s*before_chars\s*:\s*(\d+)")
AFTER_RE = re.compile(r"(?mi)^\s*after_chars\s*:\s*(\d+)")
CUT_RE = re.compile(r"(?mi)^\s*cut_rate\s*:\s*(-?[0-9]*\.?[0-9]+)")
#: 伏線の回収期限は `期限: YYYY-MM-DD` の直後だけを読む。
DEADLINE_RE = re.compile(r"期限\s*[:：]\s*(\d{4})-(\d{2})-(\d{2})")
FS_CHUNK_RE = re.compile(r"^[-*]\s*\(fs\d+\)|^\|.*\bfs\d+\b")
FS_ID_RE = re.compile(r"\(fs\d+\)")
PLANTED_RE = re.compile(r"\[planted\]|\bplanted\b")
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

#: テンプレートの説明文 (値を検査するときに「記入済み」と数えない)。
INSTRUCTION_MARKERS = ("記入例", "書く", "不可", "例:", "例：", "参照", "選び",
                       "1文で", "動詞で", "抽象語")


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
        self.scene_ids: list[str] = []

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

    def fail_or_warn(self, check: str, message: str) -> None:
        """非 legacy は error、legacy は「警告」に落とす。"""
        if self.legacy:
            self.warn(check, message + " (--legacy のため警告)")
        else:
            self.error(check, message)

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
            "lint": {"errors": self.lint_errors, "warnings": self.lint_warnings},
            "report": None if self.report_path is None else str(self.report_path),
        }


# ---------------------------------------------------------------------------
# テキストの小道具
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _yaml_block(text: str) -> str:
    """最初の ```yaml ... ``` ブロックの中身 (なければ全文)。"""
    in_yaml, block = False, []
    for line in text.splitlines():
        if YAML_FENCE_RE.match(line):
            in_yaml = True
            continue
        if in_yaml and FENCE_END_RE.match(line):
            return "\n".join(block)
        if in_yaml:
            block.append(line)
    return text if not block else "\n".join(block)


def _value_after_colon(line: str) -> str:
    """`- **約束** (読者に渡す快楽): 値` から値だけを取り出す。"""
    if ":" not in line and "：" not in line:
        return ""
    value = re.split(r"[:：]", line, maxsplit=1)[-1]
    value = re.sub(r"<!--.*?-->", "", value).replace("*", "").replace("`", "")
    return value.strip()


def _is_placeholder(value: str, instruction: bool = True) -> bool:
    """値が空・プレースホルダ・テンプレートの説明文なら True。"""
    value = value.strip()
    if not value:
        return True
    if value.startswith(">") or value.startswith("<!--"):
        return True
    if value.startswith("<") and value.endswith(">"):
        return True
    if value in {"未定", "未記入", "TBD", "TODO"}:
        return True
    if len(re.sub(r"[\s、。・（）()【】\-*「」]", "", value)) < 3:
        return True
    if instruction and any(marker in value for marker in INSTRUCTION_MARKERS):
        return True
    return False


def _section_lines(lines: list[str], heading_keyword: str) -> list[tuple[int, int]] | None:
    """`## ...heading_keyword...` 見出しから次の `## ` までの行 index 範囲。"""
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## ") and heading_keyword in line:
            start = index + 1
            continue
        if start is not None and line.startswith("## "):
            return start, index
    if start is not None:
        return start, len(lines)
    return None


def _is_label_line(line: str, keyword: str) -> bool:
    """keyword が見出し・箇条書きの「ラベル位置」にあるか (本文中の言及は除く)。"""
    stripped = line.strip()
    if stripped.startswith("#"):
        return keyword in stripped
    pattern = rf"^[-*]\s*\*{{0,2}}{re.escape(keyword)}"
    return bool(re.match(pattern, stripped))


def _section_value(text: str, keyword: str,
                   instruction: bool = True,
                   section_heading: str | None = None) -> str:
    """keyword をラベルに持つ行・節から最初の実値を返す (なければ空文字)。

    section_heading を渡すと、その見出しの節の中だけを探す
    (work.md の「面白さの設計」など)。
    """
    lines = text.splitlines()
    start, end = 0, len(lines)
    if section_heading is not None:
        bounds = _section_lines(lines, section_heading)
        if bounds is None:
            return ""
        start, end = bounds
    for index in range(start, end):
        line = lines[index]
        if not _is_label_line(line, keyword):
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            for follow in lines[index + 1:end]:
                if follow.startswith("## "):
                    break
                candidate = _value_after_colon(follow) if (
                    ":" in follow or "：" in follow) else follow.strip()
                if _is_placeholder(candidate, instruction):
                    continue
                if follow.strip().startswith(("-", "*")):
                    continue
                return candidate
            continue
        candidate = _value_after_colon(stripped)
        if candidate and not _is_placeholder(candidate, instruction):
            return candidate
    return ""


def _looks_like_template(text: str, template_name: str) -> bool:
    """作品ファイルが templates/<name> の未記入コピーに近いか。"""
    template = TEMPLATES_DIR / template_name
    if not template.is_file():
        return False
    candidates = []
    for line in _read(template).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ">", "<!--", "```",
                                                 "|", "---", "<!--")):
            continue
        if re.match(r"^[A-Za-z_][\w-]*\s*:", stripped):
            continue
        candidates.append(stripped)
    if len(candidates) < 3:
        return False
    work_lines = {line.strip() for line in text.splitlines()}
    matched = sum(1 for line in candidates if line in work_lines)
    return matched / len(candidates) >= 0.6


# ---------------------------------------------------------------------------
# 個別検査
# ---------------------------------------------------------------------------


def check_work_md(result: GateResult) -> None:
    """work.md: status active / 面白さの設計の必須7項目。"""
    path = result.workdir / "work.md"
    if not path.is_file():
        result.error("work.md", "work.md がありません")
        return
    text = _read(path)
    status_match = STATUS_YAML_RE.search(_yaml_block(text))
    status = status_match.group(1).lower() if status_match else ""
    if status != "active":
        result.error("work.md", f"status が active ではありません "
                                f"(status: {status or '不明'})")
    else:
        result.allow("work.md", "status: active")

    filled = 0
    for keyword in CHARTER_ITEMS:
        if _section_value(text, keyword, section_heading="面白さの設計"):
            filled += 1
            continue
        result.fail_or_warn("work.md", f"憲章の「{keyword}」が空です")
    if filled == 0:
        result.fail_or_warn("work.md", "憲章の「面白さの設計」が空です "
                                       "(7項目のいずれも記入されていません)")
    elif filled < len(CHARTER_ITEMS):
        result.allow("work.md", f"面白さの設計 {filled}/{len(CHARTER_ITEMS)} 項目")
    else:
        result.allow("work.md", "面白さの設計 7/7 項目")


def check_craft(result: GateResult) -> None:
    """craft/engine.md・voice.md の存在と中身 (legacy は警告)。"""
    engine = result.workdir / "craft" / "engine.md"
    voice = result.workdir / "craft" / "voice.md"
    for path, label in ((engine, "craft/engine.md"), (voice, "craft/voice.md")):
        if not path.is_file() or not _read(path).strip():
            result.fail_or_warn("craft", f"{label} がありません (物語エンジン・声の設計)")
            continue
        text = _read(path)
        template_name = "craft-engine.md" if path is engine else "craft-voice.md"
        if _looks_like_template(text, template_name):
            result.fail_or_warn("craft", f"{label} がテンプレート未記入のコピーです")
            continue
        result.allow("craft", f"{label} あり")
    if not engine.is_file():
        return
    engine_text = _read(engine)
    for keyword in ENGINE_ITEMS:
        if _section_value(engine_text, keyword, instruction=True):
            continue
        result.fail_or_warn("craft", f"craft/engine.md の「{keyword}」が空です")


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


def _scene_sort_key(name: str) -> tuple[int, int]:
    match = re.match(r"^(\d+)-(\d+)$", name)
    return (int(match.group(1)), int(match.group(2))) if match else (10 ** 6, 10 ** 6)


def check_plan(result: GateResult) -> None:
    """計画・契約・本文・polished の検査。検査したシーンIDを残す。"""
    tree_path = result.workdir / "plan" / "tree.md"
    if not tree_path.is_file():
        result.error("plan", "plan/tree.md がありません")
        return
    scene_ids = parse_plan_scene_ids(tree_path)
    result.scene_ids = scene_ids
    if not scene_ids:
        if result.legacy:
            scene_dir = result.workdir / "scenes"
            scene_ids = sorted((path.stem for path in scene_dir.glob("*.md")),
                               key=_scene_sort_key)
            result.scene_ids = scene_ids
            if scene_ids:
                result.warn("plan", "plan/tree.md を解析できないため scenes/*.md で"
                                    "代用しました (--legacy)")
            else:
                result.error("plan", "plan/tree.md を解析できず、scenes/*.md もありません")
        else:
            result.error("plan", "plan/tree.md から公開順を解析できません")
        return

    for scene_id in scene_ids:
        contract = result.workdir / "contracts" / f"{scene_id}.md"
        if not contract.is_file():
            result.error("contract", f"contracts/{scene_id}.md がありません")
        else:
            match = STATUS_YAML_RE.search(_yaml_block(_read(contract)))
            if not match or match.group(1).lower() != "approved":
                got = match.group(1) if match else "なし"
                result.error("contract", f"contracts/{scene_id}.md の status が "
                                         f"approved ではありません (status: {got})")
        scene = result.workdir / "scenes" / f"{scene_id}.md"
        if not scene.is_file():
            result.error("scenes", f"scenes/{scene_id}.md がありません")
            continue
        match = POLISHED_RE.search(_yaml_block(_read(scene)))
        if not (match and match.group(1).lower() == "true"):
            result.fail_or_warn("polish", f"scenes/{scene_id}.md が polished: true では"
                                          f"ありません (推敲未実施)")
    result.allow("plan", f"{len(scene_ids)} シーンを計画から確認")


def _beta_group_key(path: Path, text: str) -> tuple[str, tuple[str, str]]:
    """beta-*.md の対象キーと新しさソートキー (date, filename) を返す。"""
    yaml_block = _yaml_block(text)
    target_match = BETA_TARGET_RE.search(yaml_block)
    if target_match and not _is_placeholder(target_match.group(1), instruction=False):
        target = target_match.group(1).strip()
    else:
        stem = path.stem[len("beta-"):] if path.stem.startswith("beta-") else path.stem
        target = BETA_NAME_DATE_RE.sub("", stem) or path.stem
    date_match = BETA_DATE_RE.search(yaml_block)
    date_key = date_match.group(1) if date_match else ""
    return target, (date_key, path.name)


def check_beta(result: GateResult) -> None:
    """外部読者テスト (reviews/beta-*.md) の中身検査。

    同一対象に複数回の記録がある場合は最新記録で合否を判定する
    (revise 前の fail 履歴を残したまま、改稿後の pass で合格できるようにする)。
    """
    reviews = result.workdir / "reviews"
    records = sorted(reviews.glob("beta-*.md")) if reviews.is_dir() else []
    errors_before = len(result.errors)
    if not records:
        # 外部読者テストの欠落は v1 でも公開不可 (v1 の失敗の再発防止)
        result.error("beta", "reviews/beta-*.md がありません "
                             "(外部読者テストの記録が必須。v1 でも error)")
        return
    latest_by_target: dict[str, tuple[tuple[str, str], Path, str]] = {}
    for path in records:
        text = _read(path)
        if not text.strip():
            result.error("beta", f"{path.name} が空です")
            continue
        target, sort_key = _beta_group_key(path, text)
        prev = latest_by_target.get(target)
        if prev is None or sort_key >= prev[0]:
            latest_by_target[target] = (sort_key, path, text)
    for _, path, text in latest_by_target.values():
        if not EXTERNAL_RE.search(text):
            result.error("beta", f"{path.name} に external の記録がありません "
                                 "(`reader: external` / `context: external`)")
        if not GATE_PASS_RE.search(text):
            result.error("beta", f"{path.name} が interest_gate: pass ではありません "
                                 "(high 1 or medium 3 で不合格)")
    if len(result.errors) == errors_before:
        result.allow("beta", f"beta 記録 {len(records)} 件 (対象 {len(latest_by_target)} 件すべて合格)")


def check_foreshadowing(result: GateResult, today: date) -> None:
    """foreshadowing.md: planted の回収期限 (`期限: YYYY-MM-DD`) 超過。

    期限の日付だけを読み、`張設:` などの日付は期限と誤認しない。
    期限が未記入の planted は警告 (仕様: 回収予定日を書くことを推奨)。
    """
    path = result.workdir / "foreshadowing.md"
    if not path.is_file():
        result.fail_or_warn("foreshadowing", "foreshadowing.md がありません (伏線台帳)")
        return
    lines = _read(path).splitlines()
    chunks: list[list[str]] = []
    for line in lines:
        if FS_CHUNK_RE.match(line.strip()):
            chunks.append([line])
        elif chunks and line.strip() and not line.lstrip().startswith(("#", "<!--")):
            if line.startswith((" ", "\t")) or "—" in line or "期限" in line:
                chunks[-1].append(line)
    overdue: list[str] = []
    undated: list[str] = []
    for chunk in chunks:
        text = "\n".join(chunk)
        if not PLANTED_RE.search(text):
            continue
        label_match = FS_ID_RE.search(text)
        label = label_match.group(0) if label_match else "伏線"
        deadline_match = DEADLINE_RE.search(text)
        if not deadline_match:
            undated.append(label)
            continue
        try:
            deadline = date(int(deadline_match.group(1)), int(deadline_match.group(2)),
                            int(deadline_match.group(3)))
        except ValueError:
            undated.append(label)
            continue
        if deadline < today:
            overdue.append(f"{label} (期限 {deadline.isoformat()})")
    if overdue:
        result.error("foreshadowing",
                     "回収期限を過ぎた planted の伏線があります: " + ", ".join(overdue))
    if undated:
        result.warn("foreshadowing",
                    "回収期限 (`期限: YYYY-MM-DD`) が未記入の planted 伏線: "
                    + ", ".join(undated))
    if not overdue and not undated:
        result.allow("foreshadowing", "回収期限超過なし")


def check_polish_records(result: GateResult) -> None:
    """推敲記録 (reviews/polish-*.md) の存在と中身。"""
    reviews = result.workdir / "reviews"
    records = sorted(reviews.glob("polish-*.md")) if reviews.is_dir() else []
    errors_before = len(result.errors)
    if not records:
        # 推敲記録の欠落は v1 でも公開不可 (v1 の失敗の再発防止)
        result.error("polish", "reviews/polish-*.md がありません "
                               "(推敲記録が必須。v1 でも error)")
        return
    for path in records:
        text = _read(path)
        if not text.strip():
            result.error("polish", f"{path.name} が空です (推敲記録)")
            continue
        if _looks_like_template(text, "polish-report.md"):
            result.error("polish", f"{path.name} がテンプレート未記入のコピーです")
            continue
        before = BEFORE_RE.search(text)
        after = AFTER_RE.search(text)
        cut = CUT_RE.search(text)
        numbers_ok = bool(before and int(before.group(1)) > 0
                          and after and int(after.group(1)) > 0)
        cut_ok = bool(cut) and -1.0 <= float(cut.group(1)) <= 1.0
        if not numbers_ok and not cut_ok:
            result.error(
                "polish", f"{path.name} に before/after 字数または cut_rate がありません "
                          "(数値で記録する)")
    if len(result.errors) == errors_before:
        result.allow("polish", f"推敲記録 {len(records)} 件")


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


def _record_lint(result: GateResult, report, label: str) -> None:
    result.lint_errors += len(report.errors)
    result.lint_warnings += len(report.warnings)
    if report.errors:
        for finding in report.errors[:20]:
            result.errors.append(f"lint({label}): {finding.format()}")
            result._record("lint", "error", finding.format())
    else:
        result.allow("lint", f"{label}: E 0 / W {len(report.warnings)}")


def check_lint(result: GateResult, extra_manuscripts: list[Path] | None = None) -> None:
    """out/*.md・out/*.txt・scenes/*.md・staging 原稿を lint して E 0 を要求する。"""
    out_dir = result.workdir / "out"
    staged_names = {path.name for path in (extra_manuscripts or [])}
    manuscripts: list[Path] = []
    if out_dir.is_dir():
        # --release の staging で差し替え予定の旧 out/<name> は除外し、staging 側を検査する
        manuscripts = [path for path in sorted(out_dir.iterdir())
                       if path.suffix.lower() in (".md", ".txt")
                       and path.name not in staged_names]
    if not manuscripts and not extra_manuscripts:
        result.error("lint", "out/ に原稿 (.md/.txt) がありません")
        return
    for path in manuscripts:
        if path.suffix.lower() == ".md":
            report = manuscript_lint.lint_files(
                [path], workdir=result.workdir, legacy=result.legacy)
        else:
            report = manuscript_lint.lint_files([path], legacy=result.legacy)
        result.checked_manuscripts.append(str(path))
        _record_lint(result, report, str(path))

    scene_paths = [result.workdir / "scenes" / f"{scene_id}.md"
                   for scene_id in result.scene_ids]
    scene_paths = [path for path in scene_paths if path.is_file()]
    if scene_paths:
        # シーン単位では 200 字下限 (話単位の L012) は適用しない
        report = manuscript_lint.lint_files(scene_paths, legacy=result.legacy,
                                            min_chars=0)
        result.checked_manuscripts.extend(str(path) for path in scene_paths)
        _record_lint(result, report, "scenes/")

    for path in extra_manuscripts or []:
        report = manuscript_lint.lint_files(
            [path], legacy=result.legacy,
            min_chars=0 if path.suffix.lower() == ".txt" else 200)
        result.checked_manuscripts.append(str(path))
        _record_lint(result, report, f"staging/{path.name}")
        if path.suffix.lower() == ".md":
            fresh, detail = manuscript_lint.is_fresh_export(path, result.workdir)
            if not fresh:
                result.errors.append(f"lint(staging/{path.name}): {detail}")
                result._record("lint", "error", detail)


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
        f"> 自動生成 (release_gate.py が上書きする)。手動の公開チェックリストは",
        f"> `reviews/release-checklist-{today.strftime('%Y%m%d')}.md` に書く"
        " (このファイルに追記しても次回実行で消える)。",
        "",
        f"- 作品ディレクトリ: {result.workdir}",
        f"- モード: {'legacy (v1 互換)' if result.legacy else 'v2'}",
        f"- 判定: {'合格' if result.ok else '不合格'}",
        f"- lint: E {result.lint_errors} / W {result.lint_warnings}",
        f"- 検査した原稿: {len(result.checked_manuscripts)} 件",
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
        "- 外部読者テスト・目視確認の手動記録は release-checklist 側に書く。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 本体
# ---------------------------------------------------------------------------


def check(workdir: Path, legacy: bool = False, today: date | None = None,
          write_report_file: bool = True,
          extra_out_names: set[str] | None = None,
          extra_manuscripts: list[Path] | None = None) -> GateResult:
    """公開ゲートを実行する。レポートも書く。

    extra_out_names: out/ で追加許可するファイル名 (export.py --release 用)。
    extra_manuscripts: 移動前の staging 原稿 (lint と stale 比較の対象)。
    """
    result = GateResult(workdir, legacy)
    if not workdir.is_dir():
        result.error("workdir", f"作品ディレクトリがありません: {workdir}")
        return result
    check_work_md(result)
    check_craft(result)
    check_beta(result)
    check_plan(result)
    check_foreshadowing(result, today or date.today())
    check_polish_records(result)
    check_out_dir(result, extra_out_names)
    check_lint(result, extra_manuscripts)
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
    parser.add_argument("--no-report", action="store_true",
                        help="reviews/release-*.md を書かない (CI 用)")
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
    result = check(workdir, legacy=args.legacy, today=today,
                   write_report_file=not args.no_report)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        for message in result.errors:
            print(f"GATE E: {message}")
        for message in result.warnings:
            print(f"GATE W: {message}")
        print(f"release gate: {'合格' if result.ok else '不合格'} "
              f"(gate E {len(result.errors)} / W {len(result.warnings)}, "
              f"lint E {result.lint_errors} / W {result.lint_warnings})")
        if result.report_path is not None:
            print(f"レポート: {result.report_path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
