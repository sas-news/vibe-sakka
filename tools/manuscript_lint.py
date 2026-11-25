#!/usr/bin/env python3
"""manuscript_lint.py — 原稿の決定論的 lint (Python 3 標準ライブラリのみ).

仕様の正本は docs/DESIGN.md §5.1、使い方の正本は tools/README.md。

    python3 tools/manuscript_lint.py [--json] [--fix] [--workdir DIR]
                                     [--legacy] [--glossary FILE] FILE...

終了コード: 0 = E 0 件 / 1 = E あり / 2 = 使い方・IO エラー。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEV_ERROR, SEV_WARN, SEV_INFO = "E", "W", "I"

#: 章見出し。export.py が挿入する `## 第N話 タイトル` と表記揺れ。
DIGITS = "0-9０-９一二三四五六七八九十百"
CHAPTER_RE = re.compile(rf"^##\s+第([{DIGITS}]+)話(?:\s+(.*))?$")
CHAPTER_ALLOW_RE = re.compile(rf"^##\s+第[{DIGITS}]+話(?:\s|$)")
TITLE_LINE_RE = re.compile(r"^#\s+\S")

#: 区切り線として扱う文字。
SEP_CHARS = set("◆◇※*＊-—―ー=・─━")
SEP_LINE_RE = re.compile(r"^[\s◆◇※*＊\-—―ー=・─━]+$")

#: `(了)` `（了）`。
TERMINATOR_RE = re.compile(r"^[（(]\s*了\s*[)）]$")
TERMINATOR_INLINE_RE = re.compile(r"[（(]\s*了\s*[)）]")

#: YAML ヘッダ・シーン名。
YAML_FENCE_RE = re.compile(r"^```ya?ml\s*$", re.IGNORECASE)
FENCE_END_RE = re.compile(r"^```\s*$")
SCENE_NAME_RE = re.compile(r"^(\d+)-(\d+)$")
SCENE_LIKE_RE = re.compile(r"^\d+(-\d+)?$")

#: L001: 参照リンク・出典の残留。
L001_PATTERNS = (
    (re.compile(r"https?://"), "URL"),
    (re.compile(r"(?<![A-Za-z])www\.[A-Za-z0-9]"), "URL (www.)"),
    (re.compile(r"\[[^\]\n]*\]\([^)\n]*\)"), "Markdown リンク"),
    (re.compile(r"(?:出典|参照|資料|引用|ソース)\s*[:：]"), "出典ラベル"),
    (re.compile(r"research/"), "research/ への参照"),
)

#: L002: 台帳メタの混入。
L002_PATTERNS = (
    (re.compile(r"(?<![A-Za-z0-9])(?:canon|contracts|scenes|plan|proposals|changesets)/"),
     "台帳パス"),
    (re.compile(r"(?<![A-Za-z0-9])work\.md(?![A-Za-z0-9])"), "台帳パス"),
    (re.compile(r"(?<![A-Za-z0-9])p-\d{4}(?!\d)"), "提案ID"),
    (re.compile(r"(?<![A-Za-z0-9])cs-\d{4}(?!\d)"), "変更セットID"),
    (re.compile(r"(?<![A-Za-z0-9])f\d{3}(?!\d)"), "正典ID"),
    (re.compile(r"(?<![A-Za-z0-9])ent-[a-z]\d{2}(?!\d)"), "要素ID"),
    (re.compile(r"(?<![A-Za-z0-9])ev\d{2}(?!\d)"), "出来事ID"),
    (re.compile(r"(?<![A-Za-z0-9])fs\d{2}(?!\d)"), "伏線ID"),
    (re.compile(r"(?<![A-Za-z0-9])ke\d{2}(?!\d)"), "知識ID"),
    (re.compile(r"(?<![A-Za-z0-9])rev\s*\d+(?!\d)"), "リビジョン表記"),
)

#: L003: ビート見出し・番号行・制作メモ。
L003_SINGLE_KANJI_RE = re.compile(r"^[一二三四五六七八九十百]+$")
L003_BRACKET_RE = re.compile(r"^【[^】]*】$")
L003_MEMO_RE = re.compile(rf"^[（(]\s*第[{DIGITS}]+話[・\s]*了\s*[)）]$")
L003_ATX_RE = re.compile(r"^#{1,6}\s")

#: L006: プレースホルダ。
L006_PATTERNS = (
    (re.compile(r"\[\s*※\s*未執筆\s*\]"), "[※未執筆]"),
    (re.compile(r"(?<![A-Za-z0-9])(?:TODO|FIXME|XXX)(?![A-Za-z0-9])"),
     "TODO/FIXME/XXX"),
    (re.compile(r"要確認"), "要確認"),
    (re.compile(r"<<"), "<<"),
    (re.compile(r"\{\{"), "{{"),
    (re.compile(r"[（(]\s*※"), "（※"),
)

#: L006: 未定はプレースホルダ文脈 (単独行・括弧書き・値が未定) のみ E。
L006_UNDECIDED_RE = re.compile(r"[（(\[【]\s*未定\s*[)）\]】]")
L006_UNDECIDED_LINE_RE = re.compile(r"^(?:[-*]\s*)?(?:\*\*)?未定(?:\*\*)?\s*$")
L006_UNDECIDED_VALUE_RE = re.compile(r"[:：]\s*(?:[（(\[【]\s*)?未定(?:\s*[)）\]】])?\s*$")

L011_SCENE_ID_RE = re.compile(r"シーン\s*\d+-\d+")
L011_BARE_ID_RE = re.compile(r"^\d+-\d+$")

#: 警告の語彙・閾値。
EMOTION_WORDS = ("悲し", "哀し", "嬉し", "うれし", "怖", "恐ろし", "恐れ", "寂し",
                 "さびし", "つらい", "つらか", "つらく", "辛い", "辛か", "辛く",
                 "美し", "すご", "とても", "楽しか", "悔し", "怒った", "怒り",
                 "怒って", "不安", "安心", "好き", "嫌い")
ABSTRACT_WORDS = ("気持ち", "感じ", "こと", "もの")
VERB_WORDS = ("言った", "思った", "見た")
SUMMARY_PATTERNS = (re.compile(r"ことにな(?:る|った|り)"), re.compile(r"のである"),
                    re.compile(r"のだろう"), re.compile(r"だろう"))
DIALOGUE_RE = re.compile(r"[「『][^」』\n]*[」』]")
SENTENCE_SPLIT_RE = re.compile(r"[。．！？!?]+")
JP_CHAR_RE = re.compile(r"[^\u3040-\u30ff\u4e00-\u9fffA-Za-z0-9]")
JP_RANGE = r"\u3040-\u30ff\u4e00-\u9fff"

THRESHOLDS = {
    "W001": (3.0, "感情の名指し"),
    "W002": (8.0, "抽象語(こと/もの/気持ち/感じ)"),
    "W008": (4.0, "「言った/思った/見た」"),
    "W009": (3.0, "要約体の言い回し"),
}
W005_MIN_COUNT = 5      # 同一 4-gram の最小反復回数
W010_MIN_COUNT = 5      # 同一 2〜3字始まりの最小行数

_KANJI_DIGITS = {c: i for i, c in enumerate("零一二三四五六七八九")}
_FULLWIDTH_DIGITS = {chr(0xFF10 + i): str(i) for i in range(10)}


def episode_int(text: str) -> int:
    """`1` `１` `十一` などの話数を int にする。解釈できなければ -1。"""
    text = text.strip()
    if not text:
        return -1
    if text.isdigit():
        return int(text)
    if all(char in _FULLWIDTH_DIGITS for char in text):
        return int("".join(_FULLWIDTH_DIGITS[char] for char in text))
    total = unit = 0
    for char in text:
        if char in _KANJI_DIGITS:
            unit = _KANJI_DIGITS[char]
        elif char == "十":
            total, unit = total + (unit or 1) * 10, 0
        elif char == "百":
            total, unit = total + (unit or 1) * 100, 0
        else:
            return -1
    return total + unit


def content_chars(text: str) -> int:
    """空白・改行を除いた本文文字数。"""
    return len(re.sub(r"\s", "", text))


def _ratio(num: int, den: int) -> float:
    return round(num / den, 3) if den else 0.0


def _density(count: int, chars: int) -> float:
    """1,200 字あたりの出現数 (丸め 1 桁)。"""
    return round(count * 1200 / chars, 1) if chars else 0.0


def dialogue_chars(text: str) -> int:
    """「」『』内の文字数 (台詞比率の分子)。"""
    return sum(content_chars(match.group(1))
               for match in re.finditer(r"[「『](.*?)[」』]", text))


def _strip_dialogue(text: str) -> str:
    """「」『』内の台詞を除いた地の文を返す (W001/W009 の台詞誤爆防止)。"""
    return DIALOGUE_RE.sub("", text)



class Finding:
    """1件の指摘。"""

    __slots__ = ("code", "severity", "category", "file", "line", "message")

    def __init__(self, code: str, severity: str, category: str, file: str,
                 line: int, message: str) -> None:
        self.code, self.severity = code, severity
        self.category, self.file, self.line = category, file, line
        self.message = message

    def to_dict(self) -> dict:
        return {"code": self.code, "severity": self.severity, "file": self.file,
                "line": self.line, "message": self.message}

    def format(self) -> str:
        return (f"{self.severity} {self.code} {self.category:<10} "
                f"{self.file}:{self.line}  {self.message}")


class Report:
    """lint 結果の集約。"""

    def __init__(self) -> None:
        self.errors: list[Finding] = []
        self.warnings: list[Finding] = []
        self.infos: list[Finding] = []
        self.files: list[str] = []
        self.stats = {"chars": 0, "scenes": 0, "chapters": 0,
                      "dialogue_ratio": 0.0, "sentences": 0}

    def add(self, severity: str, code: str, category: str, file: str,
            line: int, message: str) -> None:
        finding = Finding(code, severity, category, file, line, message)
        {SEV_ERROR: self.errors, SEV_WARN: self.warnings,
         SEV_INFO: self.infos}[severity].append(finding)

    def error(self, code, category, file, line, message):
        self.add(SEV_ERROR, code, category, file, line, message)

    def warn(self, code, category, file, line, message):
        self.add(SEV_WARN, code, category, file, line, message)

    def info(self, code, category, file, line, message):
        self.add(SEV_INFO, code, category, file, line, message)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {"errors": [f.to_dict() for f in self.errors],
                "warnings": [f.to_dict() for f in self.warnings],
                "infos": [f.to_dict() for f in self.infos],
                "stats": dict(self.stats)}



class Source:
    """1ファイル分の読み込み結果。"""

    def __init__(self, path: Path, raw: bytes) -> None:
        self.path = path
        self.display = str(path)
        self.raw = raw
        self.text = ""
        self.encoding_errors: list[str] = []

    def decode(self) -> None:
        if self.raw.startswith(b"\xef\xbb\xbf"):
            self.encoding_errors.append("UTF-8 BOM が付いています")
            self.raw = self.raw[3:]
        crlf, lf = self.raw.count(b"\r\n"), self.raw.count(b"\n")
        if crlf and lf > crlf:
            self.encoding_errors.append("改行コードが CRLF と LF で混在しています")
        elif crlf:
            self.encoding_errors.append("改行コードが CRLF です (LF に統一してください)")
        elif b"\r" in self.raw:
            self.encoding_errors.append("CR 単独の改行があります")
        try:
            self.text = self.raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.encoding_errors.append(f"UTF-8 としてデコードできません (byte {exc.start})")
            self.text = self.raw.decode("utf-8", errors="replace")


def _strip_metadata(raw_lines: list[str]) -> list[tuple[int, str]]:
    """先頭のシーンタイトル行・YAML ヘッダ・`---` 区切りを除去する。

    返り値は (元の行番号, 行テキスト)。原稿ファイルにはヘッダがないので
    そのまま全行が返る。
    """
    n = len(raw_lines)

    def skip_blank(index: int) -> int:
        while index < n and not raw_lines[index].strip():
            index += 1
        return index

    index = skip_blank(0)
    while index < n and raw_lines[index].startswith("# ") and (
            "シーン本文" in raw_lines[index]
            or raw_lines[index].lstrip("# ").startswith("scenes/")):
        index = skip_blank(index + 1)
    if index < n and YAML_FENCE_RE.match(raw_lines[index]):
        index += 1
        while index < n and not FENCE_END_RE.match(raw_lines[index]):
            index += 1
        index = skip_blank(index + 1)
    elif index < n and raw_lines[index].strip() == "---":
        end = index + 1
        block: list[str] = []
        while end < n and raw_lines[end].strip() != "---":
            block.append(raw_lines[end])
            end += 1
        if end < n and block and all(not line.strip()
                                     or re.match(r"^[A-Za-z_][\w-]*\s*:", line)
                                     for line in block):
            index = skip_blank(end + 1)
    if index < n and raw_lines[index].strip() == "---":
        index = skip_blank(index + 1)
    end = n
    while end > index and not raw_lines[end - 1].strip():
        end -= 1
    if end > index and raw_lines[end - 1].strip() == "---":
        end -= 1
        while end > index and not raw_lines[end - 1].strip():
            end -= 1
    return [(i + 1, raw_lines[i]) for i in range(index, end)]


def strip_metadata(text: str) -> str:
    """シーン/原稿ファイル先頭のメタ情報 (タイトル行・YAML・---) を除いた本文。"""
    return "\n".join(line for _, line in _strip_metadata(text.splitlines()))


class Chapter:
    __slots__ = ("number", "title", "start", "end", "line")

    def __init__(self, number: int, title: str, start: int, line: int) -> None:
        self.number, self.title = number, title
        self.start = self.end = start
        self.line = line


def split_chapters(body: list[tuple[int, str]]) -> list[Chapter]:
    chapters: list[Chapter] = []
    for index, (lineno, text) in enumerate(body):
        match = CHAPTER_RE.match(text.strip())
        if not match:
            continue
        if chapters:
            chapters[-1].end = index
        chapters.append(Chapter(episode_int(match.group(1)),
                                (match.group(2) or "").strip(), index, lineno))
    if chapters:
        chapters[-1].end = len(body)
    return chapters


def _chapter_ranges(body: list[tuple[int, str]],
                    chapters: list[Chapter]) -> list[tuple[int, int, int]]:
    """(開始 index, 終了 index, 見出し行番号) のリスト。章がなければ全体。"""
    if chapters:
        return [(chapter.start, chapter.end, chapter.line) for chapter in chapters]
    return [(0, len(body), body[0][0] if body else 1)]



def _undecided_placeholder(stripped: str) -> bool:
    """「未定」がプレースホルダ文脈 (単独行・括弧書き・値が未定) か。"""
    if not stripped:
        return False
    bare = stripped.lstrip("-* ").strip().strip("*")
    if L006_UNDECIDED_LINE_RE.match(bare):
        return True
    if L006_UNDECIDED_RE.search(stripped):
        return True
    return bool(L006_UNDECIDED_VALUE_RE.search(stripped))


PLAIN_CHAPTER_RE = re.compile(rf"^第[{DIGITS}]+話(?:\s|$)")


def _is_heading(text: str) -> bool:
    stripped = text.strip()
    return bool(CHAPTER_RE.match(stripped) or CHAPTER_ALLOW_RE.match(stripped)
                or PLAIN_CHAPTER_RE.match(stripped)
                or (TITLE_LINE_RE.match(stripped) and stripped.startswith("# ")))


def _scan_lines(report: Report, body: list[tuple[int, str]], name: str) -> None:
    for lineno, text in body:
        stripped = text.strip()
        if not stripped:
            continue
        for pattern, label in L001_PATTERNS:
            match = pattern.search(text)
            if match:
                report.error("L001", "reference", name, lineno,
                             f"{label}「{match.group(0)[:60]}」が本文に残っています")
                break
        for pattern, label in L002_PATTERNS:
            match = pattern.search(text)
            if match:
                report.error("L002", "ledger", name, lineno,
                             f"台帳メタ({label})「{match.group(0)}」が本文に混入しています")
                break
        if L003_SINGLE_KANJI_RE.match(stripped):
            report.error("L003", "outline", name, lineno,
                         f"ビート見出し「{stripped}」が単独行で入っています")
        elif L003_BRACKET_RE.match(stripped):
            report.error("L003", "outline", name, lineno,
                         f"【…】単独行「{stripped[:40]}」が本文に混入しています")
        elif L003_MEMO_RE.match(stripped):
            report.error("L003", "outline", name, lineno,
                         f"制作メモ「{stripped}」が本文に残っています")
        elif L003_ATX_RE.match(stripped) and not CHAPTER_ALLOW_RE.match(stripped) \
                and not (lineno <= 2 and TITLE_LINE_RE.match(stripped)):
            report.error("L003", "outline", name, lineno,
                         f"本文中の見出し「{stripped[:40]}」は本文に不要です")
        for pattern, label in L006_PATTERNS:
            match = pattern.search(text)
            if match:
                report.error("L006", "placeholder", name, lineno,
                             f"プレースホルダ({label})「{match.group(0)}」が残っています")
                break
        if _undecided_placeholder(stripped):
            report.error("L006", "placeholder", name, lineno,
                         "未定 がプレースホルダのまま残っています")
        match = L011_SCENE_ID_RE.search(text) or L011_BARE_ID_RE.match(stripped)
        if match:
            report.error("L011", "sceneid", name, lineno,
                         f"scene ID「{match.group(0)}」が本文に混入しています")



def _check_duplicates(report: Report, body: list[tuple[int, str]],
                      chapters: list[Chapter], name: str) -> None:
    """L004: 同一行 (15字以上) / 同一文の重複。

    近接 (3行以内) の完全一致はコピペ痕跡として E にし、
    離れた反復や章をまたぐ反復は意図的なモチーフ・リフレインを止めないため W にする。
    """
    def chapter_of(index: int) -> int:
        for number, chapter in enumerate(chapters):
            if chapter.start <= index < chapter.end:
                return number
        return 0

    proximity = 3
    seen_line: dict[str, tuple[int, int]] = {}
    seen_sentence: dict[str, tuple[int, int]] = {}

    def report_duplicate(kind: str, lineno: int, first_line: int,
                         first_chapter: int, chapter_no: int) -> None:
        near = first_chapter == chapter_no and lineno - first_line <= proximity
        if near:
            report.error("L004", "duplicate", name, lineno,
                         f"{kind}が近接して重複しています (初出 {first_line} 行目)")
        else:
            report.warn("L004", "duplicate", name, lineno,
                        f"{kind}が離れて反復しています (初出 {first_line} 行目) "
                        "— 意図的なモチーフなら可")

    for index, (lineno, text) in enumerate(body):
        chapter_no = chapter_of(index)
        key = text.strip()
        if len(key) >= 15 and not SEP_LINE_RE.match(key):
            if key in seen_line:
                first_line, first_chapter = seen_line[key]
                report_duplicate("同一行", lineno, first_line,
                                 first_chapter, chapter_no)
            else:
                seen_line[key] = (lineno, chapter_no)
        for sentence in SENTENCE_SPLIT_RE.split(text):
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            if sentence in seen_sentence:
                first_line, first_chapter = seen_sentence[sentence]
                report_duplicate(f"同一文「{sentence[:24]}…」", lineno,
                                 first_line, first_chapter, chapter_no)
            else:
                seen_sentence[sentence] = (lineno, chapter_no)


def _check_order(report: Report, chapters: list[Chapter], name: str) -> None:
    """L005: 話見出しの欠番・重複・逆行。"""
    previous = None
    seen: set[int] = set()
    for chapter in chapters:
        number, lineno = chapter.number, chapter.line
        if number < 0:
            report.error("L005", "order", name, lineno,
                         f"話数を解釈できません: {chapter.title!r}")
            continue
        if number in seen:
            report.error("L005", "order", name, lineno,
                         f"話見出し「第{number}話」が重複しています")
        elif previous is not None and number < previous:
            report.error("L005", "order", name, lineno,
                         f"話見出しが逆行しています (第{previous}話 → 第{number}話)")
        elif previous is not None and number > previous + 1:
            report.error("L005", "order", name, lineno,
                         f"話見出しが欠番です (第{previous}話 → 第{number}話)")
        seen.add(number)
        previous = number


def _check_terminators(report: Report, body: list[tuple[int, str]], name: str) -> None:
    """L009: 末尾・章末の重複 `(了)`。"""
    hits = [lineno for lineno, text in body if TERMINATOR_RE.match(text.strip())]
    if len(hits) >= 2:
        for lineno in hits[:-1]:
            report.error("L009", "terminator", name, lineno,
                         "(了) が重複しています (末尾以外の完結記号)")
    inline = sum(len(TERMINATOR_INLINE_RE.findall(text)) for _, text in body) - len(hits)
    if inline > 0:
        first = next((lineno for lineno, text in body
                      if TERMINATOR_INLINE_RE.search(text)
                      and not TERMINATOR_RE.match(text.strip())), 1)
        report.error("L009", "terminator", name, first,
                     f"本文中に (了) が {inline} 箇所あります")


def _separator_kind(stripped: str) -> str:
    if stripped == "---":
        return "dash"
    if set(stripped) <= {"◆"}:
        return "filled"
    if set(stripped) <= {"◇"}:
        return "hollow"
    if set(stripped) <= set("*＊"):
        return "asterisk"
    if set(stripped) <= set("-—―ー─━="):
        return "dash"
    return "other"


def _check_separators(report: Report, body: list[tuple[int, str]], name: str) -> None:
    """L010: 区切り記号の混在と区切りの連続。"""
    seps = [(index, lineno, _separator_kind(text.strip()))
            for index, (lineno, text) in enumerate(body)
            if 1 <= len(text.strip()) <= 10 and SEP_LINE_RE.match(text.strip())]
    visual = [entry for entry in seps if entry[2] != "dash"]
    if len({entry[2] for entry in visual}) > 1:
        for _, lineno, kind in visual:
            if kind != "filled":
                report.error("L010", "separator", name, lineno,
                             "区切り記号が混在しています (◆ / ◇ / *** の混用)")
                break
    for (prev_idx, _, _), (curr_idx, lineno, _) in zip(seps, seps[1:]):
        if curr_idx - prev_idx > 1 and all(
                not body[i][1].strip() for i in range(prev_idx + 1, curr_idx)):
            report.error("L010", "separator", name, lineno,
                         "区切り記号が連続しています")


def _check_short_chapters(report: Report, body: list[tuple[int, str]],
                          chapters: list[Chapter], name: str,
                          min_chars: int = 200) -> None:
    """L012: 空シーン/極端な短さ (本文 min_chars 字未満の話)。"""
    if min_chars <= 0:
        return
    if not chapters:
        chars = content_chars("\n".join(text for _, text in body))
        if chars < min_chars:
            report.error("L012", "length", name, body[0][0] if body else 1,
                         f"本文が短すぎます ({chars} 字 < {min_chars} 字)")
        return
    for chapter in chapters:
        chars = content_chars("\n".join(text for _, text in body[chapter.start:chapter.end]))
        if chars < min_chars:
            report.error("L012", "length", name, chapter.line,
                         f"第{chapter.number}話の本文が短すぎます ({chars} 字 < {min_chars} 字)")



def _check_density(report: Report, body: list[tuple[int, str]], name: str,
                   code: str, category: str, words, threshold: float,
                   narration_only: bool = False) -> None:
    """語彙密度の警告 (W001 / W002 / W009)。"""
    lines = [(lineno, _strip_dialogue(text) if narration_only else text)
             for lineno, text in body]
    full_text = "\n".join(text for _, text in lines)
    chars = content_chars(full_text)
    if callable(words):
        count = words(full_text)
        hit_line = next((lineno for lineno, text in lines if words(text)),
                        body[0][0] if body else 1)
    else:
        count = sum(full_text.count(word) for word in words)
        hit_line = next((lineno for lineno, text in lines
                         if any(word in text for word in words)),
                        body[0][0] if body else 1)
    density = _density(count, chars)
    if density >= threshold:
        label = THRESHOLDS[code][1]
        report.warn(code, category, name, hit_line,
                    f"{label}が多い (1,200字あたり {density}, {count} 箇所)")


def _check_dialogue(report: Report, body: list[tuple[int, str]], name: str) -> int:
    """W003: 台詞比率 (<5% or >90% で警告。2000字未満は info のみ)。

    独白・地の文中心の場面を止めないため閾値は緩め。短い場面は
    比率が暴れやすいので info に落とす。
    """
    full_text = "\n".join(text for _, text in body)
    chars = content_chars(full_text)
    dialogue = dialogue_chars(full_text)
    ratio = _ratio(dialogue, chars)
    if chars >= 200 and (ratio < 0.05 or ratio > 0.90):
        side = "5% 未満" if ratio < 0.05 else "90% 超"
        message = f"台詞比率 {ratio:.1%} ({side})"
        if chars >= 2000:
            report.warn("W003", "dialogue", name, body[0][0] if body else 1, message)
        else:
            report.info("W003", "dialogue", name, body[0][0] if body else 1,
                        message + " — 2000字未満のため info")
    return dialogue


def _check_long(report: Report, body: list[tuple[int, str]], name: str) -> None:
    """W004: 長段落 (600字超) / 長文 (120字超)。"""
    paragraph: list[tuple[int, str]] = []
    reported = False
    for lineno, text in body + [(0, "")]:
        if text.strip():
            paragraph.append((lineno, text))
            if not reported and content_chars(
                    "\n".join(line for _, line in paragraph)) > 600:
                report.warn("W004", "length", name, paragraph[0][0],
                            "段落が長すぎます (600 字超)")
                reported = True
            for sentence in SENTENCE_SPLIT_RE.split(text):
                if content_chars(sentence) > 120:
                    report.warn("W004", "length", name, lineno,
                                f"一文が長すぎます ({content_chars(sentence)} 字 > 120 字)")
        else:
            paragraph, reported = [], False


def _check_repetition(report: Report, body: list[tuple[int, str]],
                      chapters: list[Chapter], name: str) -> None:
    """W005: 章内の同一 4-gram 反復 (回数付き)。"""
    for start, end, line in _chapter_ranges(body, chapters):
        text = "".join(line_text for _, line_text in body[start:end])
        # 英字・数字は W006 の担当なので 4-gram 反復から除く
        text = re.sub(r"[A-Za-z0-9]", "", JP_CHAR_RE.sub("", text))
        counts: dict[str, int] = {}
        for i in range(len(text) - 3):
            gram = text[i:i + 4]
            counts[gram] = counts.get(gram, 0) + 1
        repeated = sorted(((gram, count) for gram, count in counts.items()
                           if count >= W005_MIN_COUNT),
                          key=lambda item: item[1], reverse=True)[:2]
        for gram, count in repeated:
            report.warn("W005", "repetition", name, line,
                        f"同一 4-gram「{gram}」が章内で {count} 回反復しています")


def _check_latin(report: Report, body: list[tuple[int, str]], name: str,
                 glossary: set[str]) -> None:
    """W006: 英字の残留 (glossary 未登録の3文字以上)。"""
    reported: set[str] = set()
    for lineno, text in body:
        if L001_PATTERNS[0][0].search(text) or _is_heading(text):
            continue
        for word in re.findall(r"[A-Za-z]{3,}", text):
            if word.lower() in glossary or word in reported:
                continue
            reported.add(word)
            report.warn("W006", "latin", name, lineno,
                        f"未登録の英字語「{word}」(glossary に登録するか和訳してください)")
            if len(reported) >= 8:
                return


def _check_spacing(report: Report, body: list[tuple[int, str]], name: str) -> None:
    """W007: 和文直後の半角 !? や不自然な空白。"""
    half_punct = re.compile(rf"[{JP_RANGE}][!?]")
    inner_space = re.compile(rf"[{JP_RANGE}] +[{JP_RANGE}]")
    count = 0
    for lineno, text in body:
        if _is_heading(text):
            continue
        for pattern, label in ((half_punct, "和文直後の半角記号"),
                               (inner_space, "和文間の不自然な半角空白")):
            match = pattern.search(text)
            if match:
                report.warn("W007", "spacing", name, lineno,
                            f"{label}「{match.group(0)}」")
                count += 1
        if count >= 4:
            return


def _check_per_chapter_style(report: Report, body: list[tuple[int, str]],
                             chapters: list[Chapter], name: str) -> None:
    """W008 (動詞の連続) と W010 (同一起始)。"""
    for start, end, line in _chapter_ranges(body, chapters):
        text = "".join(chunk for _, chunk in body[start:end])
        chars = content_chars(text)
        verb_count = sum(text.count(word) for word in VERB_WORDS)
        density = _density(verb_count, chars)
        if verb_count >= 4 and density >= THRESHOLDS["W008"][0]:
            report.warn("W008", "verb", name, line,
                        f"「言った/思った/見た」が多い "
                        f"(1,200字あたり {density}, {verb_count} 箇所)")
        lines = [(lineno, stripped) for lineno, line_text in body[start:end]
                 if len((stripped := line_text.strip())) >= 10
                 and not SEP_LINE_RE.match(stripped) and not _is_heading(line_text)
                 and stripped[0] not in "「『"]
        for size in (3, 2):
            groups: dict[str, int] = {}
            for _, stripped in lines:
                groups[stripped[:size]] = groups.get(stripped[:size], 0) + 1
            hits = [(prefix, count) for prefix, count in groups.items()
                    if count >= W010_MIN_COUNT]
            if hits:
                prefix, count = max(hits, key=lambda item: item[1])
                report.warn("W010", "anaphora", name, line,
                            f"同じ{size}字始まりの行が多い「{prefix}…」({count} 行)")
                break



def _normalize_for_compare(body: list[tuple[int, str]]) -> str:
    """stale export 比較用の正規化。見出し・区切り・(了)・空白の差は無視する。"""
    chunks = []
    for index, (_, text) in enumerate(body):
        stripped = text.strip()
        if not stripped:
            continue
        if CHAPTER_RE.match(stripped) or CHAPTER_ALLOW_RE.match(stripped):
            continue
        if len(stripped) <= 10 and SEP_LINE_RE.match(stripped):
            continue
        if stripped == "---":
            continue
        if index == 0 and TITLE_LINE_RE.match(stripped):
            continue
        chunks.append(re.sub(r"\s", "", stripped))
    return "".join(chunks)


def _scene_sort_key(path: Path) -> tuple[int, int]:
    match = SCENE_NAME_RE.match(path.stem)
    if not match:
        return (10 ** 6, 10 ** 6)
    return (int(match.group(1)), int(match.group(2)))


def _scene_like(path: Path) -> bool:
    """シーンファイルらしい名前か (1-2.md、scenes/ 配下の 1.md)。"""
    return bool(SCENE_NAME_RE.match(path.stem)) or (
        bool(re.match(r"^\d+$", path.stem)) and path.parent.name == "scenes")


def _read_body(path: Path) -> tuple[list[tuple[int, str]], list[str]]:
    source = Source(path, path.read_bytes())
    source.decode()
    return _strip_metadata(source.text.splitlines()), source.encoding_errors


PLAN_CHAPTER_RE = re.compile(r"^##\s+第(\d+)話(?:\s+(.*))?$")
PLAN_SCENE_RE = re.compile(r"^[-*]\s+シーン\s+`?(\d+)-(\d+)`?")


def _plan_scene_files(workdir: Path, scenes_dir: Path) -> list[Path] | None:
    """plan/tree.md が読めれば、その公開順に該当する scenes/*.md を返す。"""
    tree_path = workdir / "plan" / "tree.md"
    if not tree_path.is_file():
        return None
    scene_ids: list[str] = []
    current_episode: int | None = None
    for line in tree_path.read_text(encoding="utf-8").splitlines():
        if PLAN_CHAPTER_RE.match(line):
            current_episode = 1
            continue
        match = PLAN_SCENE_RE.match(line)
        if match and current_episode is not None:
            scene_ids.append(f"{int(match.group(1))}-{int(match.group(2))}")
    if not scene_ids:
        return None
    paths = [scenes_dir / f"{scene_id}.md" for scene_id in scene_ids]
    if all(path.is_file() for path in paths):
        return paths
    return None


def _scenes_combined(workdir: Path) -> str:
    """scenes/*.md の本文を正規化して連結した文字列 (stale 比較用)。"""
    scenes_dir = workdir / "scenes"
    if not scenes_dir.is_dir():
        return ""
    scene_files = _plan_scene_files(workdir, scenes_dir)
    if scene_files is None:
        scene_files = sorted(scenes_dir.glob("*.md"), key=_scene_sort_key)
    return "".join(_normalize_for_compare(_read_body(path)[0])
                   for path in scene_files)


def is_fresh_export(manuscript: Path | str, workdir: Path) -> tuple[bool, str]:
    """原稿が scenes/ の最新連結と一致するか (stale export でないか)。

    返り値: (一致したか, 説明)。out/ 以外 (build/staging 等) の原稿にも使える。
    """
    scene_text = _scenes_combined(workdir)
    if not scene_text:
        return True, "scenes/ が空のため stale 検査を省略しました"
    path = Path(manuscript)
    out_text = _normalize_for_compare(_read_body(path)[0])
    if out_text == scene_text:
        return True, "export は最新です"
    return False, (f"scenes と一致しません (stale export): "
                   f"原稿 {len(out_text)}字 / scenes {len(scene_text)}字")


def _check_stale(report: Report, workdir: Path, files: list[Path]) -> None:
    """L007: out/ の原稿と scenes/ の本文を正規化比較する。"""
    scenes_dir, out_dir = workdir / "scenes", workdir / "out"
    if not scenes_dir.is_dir():
        report.info("L007", "stale", str(workdir), 0, "scenes/ がないため stale 検査を省略")
        return
    scene_text = _scenes_combined(workdir)
    if not scene_text:
        report.info("L007", "stale", str(scenes_dir), 0, "scenes の本文が空のため省略")
        return
    # stale 比較は Markdown 原稿だけ (txt は md の派生物なので比較しない)
    targets = [path for path in files
               if path.parent.resolve() == out_dir.resolve()
               and path.suffix.lower() == ".md"]
    if not targets:
        targets = sorted(out_dir.glob("*.md")) if out_dir.is_dir() else []
    if not targets:
        report.info("L007", "stale", str(out_dir), 0, "out/*.md がないため省略")
        return
    for target in targets:
        out_text = _normalize_for_compare(_read_body(target)[0])
        if out_text == scene_text:
            report.info("L007", "stale", str(target), 0, "export は最新です")
            continue
        pos = next((i for i, (a, b) in enumerate(zip(out_text, scene_text)) if a != b),
                   min(len(out_text), len(scene_text)))
        detail = ""
        if pos < len(out_text) and pos < len(scene_text):
            detail = (f" 最初の差分: 「{out_text[pos:pos + 12]}」 ≠ "
                      f"「{scene_text[pos:pos + 12]}」")
        report.error("L007", "stale", str(target), 0,
                     "out 原稿が scenes と一致しません (stale export)。"
                     "export.py を再実行してください"
                     f" (out {len(out_text)}字 / scenes {len(scene_text)}字){detail}")



def _compute_stats(body: list[tuple[int, str]], chapters: list[Chapter],
                   dialogue: int) -> dict:
    full_text = "\n".join(text for _, text in body)
    chars = content_chars(full_text)
    return {"chars": chars, "chapters": len(chapters),
            "dialogue_ratio": _ratio(dialogue, chars),
            "sentences": len([s for s in SENTENCE_SPLIT_RE.split(full_text) if s.strip()]),
            "_dialogue": dialogue}


def lint_source(source: Source, legacy: bool = False,
                glossary: set[str] | None = None,
                min_chars: int = 200) -> Report:
    """1ファイル分の Report を作る。"""
    report = Report()
    for message in source.encoding_errors:
        report.error("L008", "encoding", source.display, 1, message)
    body = _strip_metadata(source.text.splitlines())
    if not body:
        report.error("L012", "length", source.display, 1, "本文が空です")
        return report
    chapters = split_chapters(body)
    _scan_lines(report, body, source.display)
    _check_duplicates(report, body, chapters, source.display)
    _check_order(report, chapters, source.display)
    _check_terminators(report, body, source.display)
    _check_separators(report, body, source.display)
    _check_short_chapters(report, body, chapters, source.display, min_chars)
    _check_density(report, body, source.display, "W001", "emotion",
                   EMOTION_WORDS, THRESHOLDS["W001"][0], narration_only=True)
    _check_density(report, body, source.display, "W002", "abstract",
                   ABSTRACT_WORDS, THRESHOLDS["W002"][0])
    dialogue = _check_dialogue(report, body, source.display)
    _check_long(report, body, source.display)
    _check_repetition(report, body, chapters, source.display)
    _check_latin(report, body, source.display, glossary or set())
    _check_spacing(report, body, source.display)
    _check_per_chapter_style(report, body, chapters, source.display)
    _check_density(report, body, source.display, "W009", "summary",
                   lambda text: sum(len(p.findall(text)) for p in SUMMARY_PATTERNS),
                   THRESHOLDS["W009"][0], narration_only=True)
    report.stats.update(_compute_stats(body, chapters, dialogue))
    report.stats["scenes"] = 1 if _scene_like(source.path) else 0
    report.files.append(source.display)
    return report


def lint_files(files: list[Path], workdir: Path | None = None, legacy: bool = False,
               glossary: set[str] | None = None, min_chars: int = 200) -> Report:
    """複数ファイルを lint して1つの Report にまとめる。"""
    total = Report()
    dialogue_total = 0
    for path in files:
        source = Source(path, path.read_bytes())
        source.decode()
        report = lint_source(source, legacy=legacy, glossary=glossary,
                             min_chars=min_chars)
        total.errors.extend(report.errors)
        total.warnings.extend(report.warnings)
        total.infos.extend(report.infos)
        total.files.extend(report.files)
        for key in ("chars", "scenes", "chapters", "sentences"):
            total.stats[key] += report.stats[key]
        dialogue_total += report.stats.get("_dialogue", 0)
    total.stats["dialogue_ratio"] = _ratio(dialogue_total, total.stats["chars"])
    if workdir is not None:
        _check_stale(total, workdir, files)
        scenes_dir, out_dir = workdir / "scenes", (workdir / "out").resolve()
        if scenes_dir.is_dir() and files and all(
                path.resolve().parent == out_dir for path in files):
            total.stats["scenes"] = len(list(scenes_dir.glob("*.md")))
    return total


def lint_text(text: str, name: str = "<text>", legacy: bool = False,
              glossary: set[str] | None = None,
              min_chars: int = 200) -> Report:
    """メモリ上の原稿テキストを lint する (export.py / release_gate.py から使う)。"""
    source = Source(Path(name), text.encode("utf-8"))
    source.decode()
    return lint_source(source, legacy=legacy, glossary=glossary,
                       min_chars=min_chars)


BLANK_RE = re.compile(r"^\s*$")
_VISUAL_SEP = set("◆◇※*＊—―ー=・─━")


def _merge_consecutive_separators(lines: list[str]) -> tuple[list[str], int]:
    """空白行のみを挟んで連続する区切り記号を1本に整理する。"""
    merged = 0
    changed = True
    while changed:
        changed, result, index = False, [], 0
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped and set(stripped) <= _VISUAL_SEP:
                look = index + 1
                while look < len(lines) and not lines[look].strip():
                    look += 1
                if look < len(lines) and lines[look].strip() and \
                        set(lines[look].strip()) <= _VISUAL_SEP:
                    result.append(lines[index])
                    index = look + 1
                    merged += 1
                    changed = True
                    continue
            result.append(lines[index])
            index += 1
        lines = result
    return lines, merged


def fix_text(text: str) -> tuple[str, list[str]]:
    """安全な自動修正のみを行う。本文の語句は書き換えない。"""
    fixes: list[str] = []
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
        fixes.append("BOM を除去")
    if "\r\n" in text or "\r" in text:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        fixes.append("改行コードを LF に統一")

    lines = text.split("\n")
    trailing = [i for i, line in enumerate(lines) if line != line.rstrip()]
    if trailing:
        lines = [line.rstrip() for line in lines]
        fixes.append(f"行末空白を除去 ({len(trailing)} 行)")

    converted = 0
    for i, line in enumerate(lines):
        if line.strip() in ("◇", "***", "**", "＊", "※"):
            lines[i] = "◆"
            converted += 1
    if converted:
        fixes.append(f"区切り記号を ◆ に統一 ({converted} 箇所)")

    terminators = [i for i, line in enumerate(lines) if TERMINATOR_RE.match(line.strip())]
    if len(terminators) >= 2:
        keep = terminators[-1]
        lines = [line for i, line in enumerate(lines)
                 if i not in terminators or i == keep]
        fixes.append(f"重複した (了) を除去 ({len(terminators) - 1} 箇所)")

    lines, merged = _merge_consecutive_separators(lines)
    if merged:
        fixes.append(f"連続した区切りを整理 ({merged} 箇所)")

    collapsed, result, blanks = 0, [], 0
    for line in lines:
        if BLANK_RE.match(line):
            blanks += 1
            if blanks <= 1:
                result.append("")
            else:
                collapsed += 1
        else:
            blanks = 0
            result.append(line)
    if collapsed:
        fixes.append(f"過剰な空行を整理 ({collapsed} 行)")
        lines = result

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    if not text.endswith("\n"):
        text += "\n"
    return text, fixes



def load_glossary(path: Path | None) -> set[str]:
    """英字語の許可リスト (1行1語、# でコメント)。"""
    if path is None:
        return set()
    return {line.split("#", 1)[0].strip().lower()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip()}


def print_report(report: Report, as_json: bool, files: list[str]) -> None:
    if as_json:
        data = report.to_dict()
        data["files"] = report.files or files
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    for finding in report.errors + report.warnings + report.infos:
        print(finding.format())
    stats = report.stats
    print(f"統計: chars={stats['chars']} scenes={stats['scenes']} "
          f"chapters={stats['chapters']} sentences={stats['sentences']} "
          f"dialogue_ratio={stats['dialogue_ratio']}")
    print(f"E {len(report.errors)} / W {len(report.warnings)} / I {len(report.infos)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manuscript_lint.py",
        description="原稿 Markdown の決定論的 lint。E が1件でもあれば exit 1。")
    parser.add_argument("files", nargs="+", metavar="FILE", help="検査する原稿 Markdown")
    parser.add_argument("--json", action="store_true", help="結果を JSON で stdout に出す")
    parser.add_argument("--fix", action="store_true", help="安全な自動修正のみ行う")
    parser.add_argument("--workdir", metavar="DIR", help="作品ディレクトリ (stale export 検査)")
    parser.add_argument("--legacy", action="store_true", help="v1 作品の互換モード")
    parser.add_argument("--glossary", metavar="FILE",
                        help="英字語の許可リスト (1行1語、# でコメント)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths: list[Path] = []
    for name in args.files:
        path = Path(name)
        if not path.is_file():
            print(f"エラー: ファイルが見つかりません: {name}", file=sys.stderr)
            return 2
        paths.append(path)
    workdir = Path(args.workdir) if args.workdir else None
    if workdir is not None and not workdir.is_dir():
        print(f"エラー: --workdir が見つかりません: {workdir}", file=sys.stderr)
        return 2
    try:
        glossary = load_glossary(Path(args.glossary) if args.glossary else None)
    except OSError as exc:
        print(f"エラー: glossary を読めません: {exc}", file=sys.stderr)
        return 2

    if args.fix:
        # --json のときは stdout を JSON 専用に保つため、修正ログは stderr に出す
        log = sys.stderr if args.json else sys.stdout
        fixes_made = 0
        for path in paths:
            source = Source(path, path.read_bytes())
            source.decode()
            fixed, fixes = fix_text(source.text)
            for fix in fixes:
                print(f"fix: {path}: {fix}", file=log)
            if fixes:
                path.write_text(fixed, encoding="utf-8", newline="\n")
                fixes_made += 1
        if not fixes_made:
            print("fix: 修正対象はありませんでした", file=log)

    try:
        report = lint_files(paths, workdir=workdir, legacy=args.legacy,
                            glossary=glossary)
    except OSError as exc:
        print(f"エラー: 読み込みに失敗しました: {exc}", file=sys.stderr)
        return 2
    print_report(report, args.json, [str(path) for path in paths])
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
