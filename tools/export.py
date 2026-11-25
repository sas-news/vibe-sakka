#!/usr/bin/env python3
"""export.py — scenes/ を計画順に連結して公開原稿を書き出す (決定論的).

仕様の正本は docs/DESIGN.md §5.2、使い方の正本は tools/README.md。

    python3 tools/export.py [--workdir .] [--order 1-1,1-2,...]
                            [--title TITLE] [--md] [--txt] [--epub]
                            [--release] [--no-lint] [--legacy] [--json]

終了コード: 0 = 成功 / 1 = ゲート不合格 (lint E・シーン欠落・release gate) /
2 = 使い方・IO エラー (計画を解析できない等)。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import uuid
import zipfile
from datetime import date
from pathlib import Path

import manuscript_lint
import release_gate

#: `## 第N話 タイトル [状態]`
CHAPTER_RE = re.compile(r"^##\s+第(\d+)話(?:\s+(.*))?$")
#: 話タイトル末尾の `[状態]` 表記
STATE_SUFFIX_RE = re.compile(r"\s*\[[^\]]*\]\s*$")
#: `- シーン \`1-2\` タイトル [状態] ...`
SCENE_LINE_RE = re.compile(r"^[-*]\s+シーン\s+`?(\d+)-(\d+)`?")
#: `--order` の1要素
ORDER_ITEM_RE = re.compile(r"^(\d+)-(\d+)$")
#: YAML の `title: "..."`
TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*(?:#.*)?$', re.MULTILINE)
YAML_FENCE_RE = re.compile(r"^```ya?ml\s*$", re.IGNORECASE)
FENCE_END_RE = re.compile(r"^```\s*$")



class PlanError(Exception):
    """plan/tree.md を解析できない。"""


class SceneRef:
    """計画上の1シーン。"""

    __slots__ = ("episode", "order", "scene_id")

    def __init__(self, episode: int, order: int) -> None:
        self.episode = episode
        self.order = order
        self.scene_id = f"{episode}-{order}"


class Plan:
    """plan/tree.md の解析結果 (公開順と話タイトル)。"""

    def __init__(self) -> None:
        self.chapters: dict[int, str] = {}
        self.scenes: list[SceneRef] = []


# ---------------------------------------------------------------------------
# 計画・作品情報の解析
# ---------------------------------------------------------------------------


def parse_plan(path: Path) -> Plan:
    """plan/tree.md から公開順と話タイトルを読む。読めなければ PlanError。"""
    text = path.read_text(encoding="utf-8")
    plan = Plan()
    current_episode: int | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        chapter = CHAPTER_RE.match(line)
        if chapter:
            current_episode = int(chapter.group(1))
            title = STATE_SUFFIX_RE.sub("", (chapter.group(2) or "").strip()).strip()
            plan.chapters[current_episode] = title
            continue
        scene = SCENE_LINE_RE.match(line)
        if scene and current_episode is not None:
            plan.scenes.append(SceneRef(int(scene.group(1)), int(scene.group(2))))
    if not plan.scenes:
        raise PlanError("`## 第N話` と `- シーン \\`E-S\\`` の行が見つかりません")
    return plan


def parse_order(order: str) -> list[SceneRef]:
    """`1-1,1-2,...` を SceneRef のリストにする。不正なら PlanError。"""
    refs: list[SceneRef] = []
    for item in order.split(","):
        item = item.strip()
        if not item:
            continue
        match = ORDER_ITEM_RE.match(item)
        if not match:
            raise PlanError(f"--order の書式が不正です: {item!r} (例: 1-1,1-2,2-1)")
        chapter, order_in_chapter = int(match.group(1)), int(match.group(2))
        refs.append(SceneRef(chapter, order_in_chapter))
    if not refs:
        raise PlanError("--order が空です (例: 1-1,1-2,2-1)")
    return refs


def check_contiguous(refs: list[SceneRef]) -> None:
    """公開順が話単位で連続しているか。飛び飛びなら推測せずエラー。"""
    seen_episodes: list[int] = []
    for ref in refs:
        if not seen_episodes or seen_episodes[-1] != ref.episode:
            seen_episodes.append(ref.episode)
    if len(set(seen_episodes)) != len(seen_episodes):
        raise PlanError(
            "公開順が話単位で連続していません (同じ話が飛び飛びです): "
            + ", ".join(ref.scene_id for ref in refs)
        )
    if seen_episodes != sorted(seen_episodes):
        raise PlanError("公開順の話数が逆行しています: " + ", ".join(map(str, seen_episodes)))


def load_work_title(workdir: Path) -> str:
    """work.md の YAML から作品タイトルを読む (なければ空文字)。"""
    work_md = workdir / "work.md"
    if not work_md.is_file():
        return ""
    text = work_md.read_text(encoding="utf-8")
    in_yaml = False
    for line in text.splitlines():
        if YAML_FENCE_RE.match(line):
            in_yaml = True
            continue
        if in_yaml and FENCE_END_RE.match(line):
            break
        if in_yaml:
            match = TITLE_RE.match(line)
            if match:
                return match.group(1).strip().strip('"').strip()
    return ""


# ---------------------------------------------------------------------------
# 本文の組み立て
# ---------------------------------------------------------------------------


def scene_body(path: Path) -> str:
    """シーンファイルから本文だけを取り出す (ヘッダ・YAML・`---` は落とす)。"""
    text = path.read_text(encoding="utf-8")
    body = manuscript_lint.strip_metadata(text)
    # 末尾の余分な空行だけ落とす (本文の語句は変えない)
    return body.rstrip("\n")


def build_markdown(title: str, refs: list[SceneRef], plan: Plan | None,
                   workdir: Path, separator: str = "") -> tuple[str, dict]:
    """公開原稿 Markdown を組み立てる。整形は話見出しと任意の区切りの挿入だけ。"""
    parts: list[str] = []
    if title:
        parts.append(f"# {title}")
        parts.append("")
    current_episode: int | None = None
    scenes_included: list[str] = []
    for idx, ref in enumerate(refs):
        if ref.episode != current_episode:
            chapter_title = ""
            if plan is not None:
                chapter_title = plan.chapters.get(ref.episode, "")
            heading = f"## 第{ref.episode}話"
            if chapter_title:
                heading += f" {chapter_title}"
            parts.append(heading)
            parts.append("")
            current_episode = ref.episode
        body = scene_body(workdir / "scenes" / f"{ref.scene_id}.md")
        parts.append(body)
        nxt = refs[idx + 1] if idx + 1 < len(refs) else None
        if separator and nxt is not None and nxt.episode == ref.episode:
            parts.append(separator)
        parts.append("")
        scenes_included.append(ref.scene_id)
    content = "\n".join(parts)
    content = re.sub(r"\n{3,}", "\n\n", content).rstrip("\n") + "\n"
    structure = {
        "scenes": scenes_included,
        "chapters": sorted({ref.episode for ref in refs}),
    }
    return content, structure


def to_plain_text(markdown: str) -> str:
    """Markdown 記号を落とした投稿用プレーンテキスト。"""
    lines: list[str] = []
    for line in markdown.splitlines():
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^>\s?", "", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", line)
        line = line.replace("`", "")
        lines.append(line.rstrip())
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n") + "\n"


# ---------------------------------------------------------------------------
# EPUB
# ---------------------------------------------------------------------------


def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _blocks(markdown: str) -> list[tuple[str, str]]:
    """Markdown を (種類, テキスト) の列にする。種類は h1/h2/p。"""
    blocks: list[tuple[str, str]] = []
    current: list[str] = []
    for line in markdown.splitlines():
        if not line.strip():
            if current:
                blocks.append(("p", "\n".join(current)))
                current = []
            continue
        if line.startswith("## "):
            if current:
                blocks.append(("p", "\n".join(current)))
                current = []
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("# "):
            if current:
                blocks.append(("p", "\n".join(current)))
                current = []
            blocks.append(("h1", line[2:].strip()))
        else:
            current.append(line)
    if current:
        blocks.append(("p", "\n".join(current)))
    return blocks


def build_epub(title: str, markdown: str) -> bytes:
    """標準ライブラリの zipfile だけで最小 EPUB3 を組み立てる。"""
    book_title = title or "manuscript"
    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'vibe-sakka:' + book_title)}"
    modified = date.today().strftime("%Y-%m-%dT00:00:00Z")
    blocks = _blocks(markdown)

    body_parts: list[str] = []
    nav_items: list[str] = []
    chapter_no = 0
    for kind, text in blocks:
        if kind == "h1":
            body_parts.append(f"<h1>{_xml_escape(text)}</h1>")
        elif kind == "h2":
            chapter_no += 1
            anchor = f"ch{chapter_no}"
            body_parts.append(f'<h2 id="{anchor}">{_xml_escape(text)}</h2>')
            nav_items.append(f'      <li><a href="content.xhtml#{anchor}">'
                             f"{_xml_escape(text)}</a></li>")
        else:
            body_parts.append(f"<p>{_xml_escape(text).replace(chr(10), '<br/>')}</p>")

    content_xhtml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ja" lang="ja">\n'
        "<head>\n"
        f"  <title>{_xml_escape(book_title)}</title>\n"
        '  <meta charset="UTF-8"/>\n'
        "</head>\n"
        "<body>\n"
        "<section epub:type=\"bodymatter\">\n"
        + "\n".join(body_parts)
        + "\n</section>\n</body>\n</html>\n"
    )
    if not nav_items:
        nav_items.append(f'      <li><a href="content.xhtml">'
                         f"{_xml_escape(book_title)}</a></li>")
    nav_xhtml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ja" lang="ja">\n'
        "<head>\n"
        f"  <title>{_xml_escape(book_title)}</title>\n"
        '  <meta charset="UTF-8"/>\n'
        "</head>\n"
        "<body>\n"
        '  <nav epub:type="toc" id="toc">\n'
        "    <h1>目次</h1>\n"
        "    <ol>\n"
        + "\n".join(nav_items)
        + "\n    </ol>\n  </nav>\n</body>\n</html>\n"
    )
    package_opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid" xml:lang="ja">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="bookid">{identifier}</dc:identifier>\n'
        f"    <dc:title>{_xml_escape(book_title)}</dc:title>\n"
        "    <dc:language>ja</dc:language>\n"
        "    <dc:creator>vibe-sakka</dc:creator>\n"
        f'    <meta property="dcterms:modified">{modified}</meta>\n'
        "  </metadata>\n"
        "  <manifest>\n"
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" '
        'properties="nav"/>\n'
        '    <item id="content" href="content.xhtml" '
        'media-type="application/xhtml+xml"/>\n'
        "  </manifest>\n"
        "  <spine>\n"
        '    <itemref idref="content"/>\n'
        "  </spine>\n"
        "</package>\n"
    )
    container_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "  <rootfiles>\n"
        '    <rootfile full-path="OEBPS/package.opf" '
        'media-type="application/oebps-package+xml"/>\n'
        "  </rootfiles>\n"
        "</container>\n"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("mimetype")
        info.compress_type = zipfile.ZIP_STORED
        archive.writestr(info, "application/epub+zip")
        archive.writestr("META-INF/container.xml", container_xml,
                         compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/package.opf", package_opf,
                         compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/nav.xhtml", nav_xhtml,
                         compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/content.xhtml", content_xhtml,
                         compress_type=zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# 出力・レポート
# ---------------------------------------------------------------------------


def safe_filename(title: str) -> str:
    """作品タイトルをファイル名に使える形にする。"""
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", title).strip().strip(".")
    return name or "manuscript"


def remove_tree(path: Path) -> None:
    """作業ディレクトリを丸ごと消す (staging の後始末)。"""
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def write_report(workdir: Path, report_text: str) -> Path:
    build = workdir / "build"
    build.mkdir(parents=True, exist_ok=True)
    path = build / "export-report.md"
    path.write_text(report_text, encoding="utf-8")
    return path


def _format_report(title: str, workdir: Path, refs: list[SceneRef],
                   structure: dict, chars: int, lint_report,
                   outputs: list[Path], gate_result, no_lint: bool) -> str:
    lines = [
        "# export レポート",
        "",
        f"- 実行日: {date.today().isoformat()}",
        f"- 作品: {title or '(無題)'}",
        f"- 作業ディレクトリ: {workdir}",
        f"- 公開順: {', '.join(ref.scene_id for ref in refs)}",
        f"- 話数: {len(structure.get('chapters', []))} / "
        f"シーン数: {len(structure.get('scenes', []))}",
        f"- 文字数: {chars}",
    ]
    if no_lint:
        lines.append("- lint: スキップ (--no-lint)")
    elif lint_report is not None:
        lines.append(f"- lint: E {len(lint_report.errors)} / "
                     f"W {len(lint_report.warnings)}")
    if gate_result is None:
        lines.append("- release gate: 未実行")
    else:
        lines.append(f"- release gate: {'合格' if gate_result.ok else '不合格'}")
    lines.append("- 出力: " + (", ".join(str(p) for p in outputs) if outputs else "なし"))
    if not no_lint and lint_report is not None:
        lines += ["", "## lint の指摘", ""]
        findings = lint_report.errors + lint_report.warnings
        if not findings:
            lines.append("- なし")
        for finding in findings[:40]:
            lines.append(f"- {finding.format()}")
    if gate_result is not None:
        lines += ["", "## release gate の指摘", ""]
        findings = gate_result.errors + gate_result.warnings
        if not findings:
            lines.append("- なし")
        for message in findings:
            lines.append(f"- {message}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------


def _resolve_refs(workdir: Path, order: str | None) -> tuple[list[SceneRef], Plan | None]:
    plan_path = workdir / "plan" / "tree.md"
    plan: Plan | None = None
    if plan_path.is_file():
        try:
            plan = parse_plan(plan_path)
        except PlanError:
            plan = None
    if order:
        refs = parse_order(order)
        check_contiguous(refs)
        return refs, plan
    if plan is None:
        raise PlanError(
            "plan/tree.md から公開順を解析できません。"
            "`--order 1-1,1-2,2-1` の形で公開順を指定してください "
            "(推測で並べません)。"
            "v1 の `scenes/N.md` (1話1シーン) は --order でも解決しません。"
            "docs/MIGRATION.md §8.4 に従い `scenes/N-1.md` にリネームしてください"
        )
    check_contiguous(plan.scenes)
    return plan.scenes, plan


def run(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir)
    if not workdir.is_dir():
        print(f"エラー: --workdir が見つかりません: {workdir}", file=sys.stderr)
        return 2
    try:
        refs, plan = _resolve_refs(workdir, args.order)
    except PlanError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2

    title = args.title or load_work_title(workdir)
    if not title:
        title = "manuscript"

    missing = [ref.scene_id for ref in refs
               if not (workdir / "scenes" / f"{ref.scene_id}.md").is_file()]
    if missing:
        for scene_id in missing:
            print(f"エラー: シーンがありません: scenes/{scene_id}.md "
                  f"(計画上の公開順: {', '.join(ref.scene_id for ref in refs)})",
                  file=sys.stderr)
        report = _format_report(title, workdir, refs, {}, 0, None, [], None, True)
        report_path = write_report(workdir, report)
        if args.json:
            print(json.dumps({"ok": False, "reason": "missing_scenes",
                              "missing": missing, "report": str(report_path)},
                             ensure_ascii=False, indent=2))
        return 1

    content, structure = build_markdown(title, refs, plan, workdir, args.separator)
    chars = len(re.sub(r"\s", "", content))

    lint_report = None
    if not args.no_lint:
        lint_report = manuscript_lint.lint_text(
            content, name=f"out/{safe_filename(title)}.md", legacy=args.legacy)
        if lint_report.errors:
            stream = sys.stderr if args.json else sys.stdout
            print("エラー: lint E があるため書き出しません。", file=stream)
            for finding in lint_report.errors:
                print(f"  {finding.format()}", file=stream)
            report = _format_report(title, workdir, refs, structure, chars,
                                    lint_report, [], None, False)
            report_path = write_report(workdir, report)
            if args.json:
                print(json.dumps({
                    "ok": False, "reason": "lint",
                    "errors": [finding.to_dict() for finding in lint_report.errors],
                    "report": str(report_path)}, ensure_ascii=False, indent=2))
            return 1

    out_dir = workdir / "out"
    base = safe_filename(title)
    staging = workdir / "build" / "staging"

    # --release は build/staging/ に生成し、ゲート合格後にだけ out/ へ移す。
    # 失敗時は out/ を一切変更しない (公開済みの原稿を壊さない)。
    target_dir = staging if args.release else out_dir
    if args.release:
        remove_tree(staging)
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    staged_paths = {
        "md": target_dir / f"{base}.md",
        "txt": target_dir / f"{base}.txt",
        "epub": target_dir / f"{base}.epub",
    }
    staged_paths["md"].write_text(content, encoding="utf-8")
    outputs.append(staged_paths["md"])
    if args.txt:
        staged_paths["txt"].write_text(to_plain_text(content), encoding="utf-8")
        outputs.append(staged_paths["txt"])
    if args.epub:
        staged_paths["epub"].write_bytes(build_epub(title, content))
        outputs.append(staged_paths["epub"])

    gate_result = None
    gate_ok = True
    if args.release:
        gate_result = release_gate.check(
            workdir, legacy=args.legacy,
            extra_out_names={path.name for path in outputs},
            extra_manuscripts=[path for path in outputs
                               if path.suffix.lower() in (".md", ".txt")],
            write_report_file=not args.no_report)
        gate_ok = gate_result.ok
        final_outputs: list[Path] = []
        if gate_ok:
            out_dir.mkdir(parents=True, exist_ok=True)
            for path in outputs:
                destination = out_dir / path.name
                os.replace(path, destination)
                final_outputs.append(destination)
            remove_tree(staging)
        else:
            remove_tree(staging)
        outputs = final_outputs

    report = _format_report(title, workdir, refs, structure, chars, lint_report,
                            outputs, gate_result, args.no_lint)
    report_path = write_report(workdir, report)

    ok = gate_ok
    if args.json:
        data = {
            "ok": ok,
            "title": title,
            "files": [str(path) for path in outputs],
            "order": [ref.scene_id for ref in refs],
            "chars": chars,
            "lint": None if lint_report is None else {
                "errors": len(lint_report.errors),
                "warnings": len(lint_report.warnings),
            },
            "gate": None if gate_result is None else {
                "ok": gate_result.ok,
                "errors": gate_result.errors,
                "warnings": gate_result.warnings,
            },
            "report": str(report_path),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for path in outputs:
            print(f"出力: {path}")
        if lint_report is not None:
            print(f"lint: E {len(lint_report.errors)} / W {len(lint_report.warnings)}")
        else:
            print("lint: スキップ (--no-lint)")
        if gate_result is not None:
            print(f"release gate: {'合格' if gate_result.ok else '不合格'}")
            for message in gate_result.errors:
                print(f"  GATE E: {message}")
            for message in gate_result.warnings:
                print(f"  GATE W: {message}")
        print(f"レポート: {report_path}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="export.py",
        description="plan/tree.md の公開順に scenes/*.md を連結し、"
                    "out/ に公開原稿 (md/txt/epub) を書き出す。",
    )
    parser.add_argument("--workdir", default=".", metavar="DIR",
                        help="作品ディレクトリ (既定: カレント)")
    parser.add_argument("--order", metavar="LIST",
                        help="公開順を明示する (例: 1-1,1-2,2-1)。"
                             "plan/tree.md を解析できない時に使う")
    parser.add_argument("--title", metavar="TITLE", help="作品タイトル (既定: work.md)")
    parser.add_argument("--separator", metavar="SEP",
                        help="同一話内のシーン間に入れる区切り (例: ◆)。"
                             "md/txt で同じ区切りになる。既定はなし")
    parser.add_argument("--md", action="store_true", help="Markdown を出力 (既定で出力)")
    parser.add_argument("--txt", action="store_true", help="プレーンテキストも出力")
    parser.add_argument("--epub", action="store_true", help="EPUB も出力")
    parser.add_argument("--release", action="store_true",
                        help="release_gate.py の検査も通す")
    parser.add_argument("--no-lint", action="store_true", help="lint をスキップする")
    parser.add_argument("--no-report", action="store_true",
                        help="--release 時に release_gate のレポートを書かない "
                             "(CI 用)")
    parser.add_argument("--legacy", action="store_true", help="v1 作品の互換モード")
    parser.add_argument("--json", action="store_true", help="結果を JSON で出す")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
