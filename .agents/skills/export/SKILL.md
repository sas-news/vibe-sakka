---
name: export
description: 生成済みシーンを計画順に連結して読める原稿を書き出す。python3 tools/export.py 経由を必須とし、手作業連結を禁止する。out/ は公開物のみ、build/ は作業物。--release は release_gate を通す。「原稿を出して」「連結して」「投稿用に出力して」で使う。
---

# export — 原稿の書き出し

`scenes/` に散った本文を読める形にまとめる。**結合のみ — 本文は一字一句
変えない** (直したい箇所は `.agents/skills/change-set` か `polish` 経由)。
**手作業での連結 (cat・コピペ) は禁止。** 順序・話見出し・YAML 除去・lint を
`python3 tools/export.py` に一元化する。

## いつ使うか

- 作者が「読みたい」「投稿用に」「EPUB がほしい」と言ったとき。
- beta-read / polish / release-gate の入力原稿を出すとき。
- 公開物を確定するとき (`--release`)。

## 入力

- `plan/tree.md` — 公開順 (`## 第N話 <タイトル> [状態]` と
  `- シーン \`E-S\` …`)。パース不能なら export はエラーにし `--order` を
  促す (推測で並べない)。
- `scenes/*.md` — 本文とヘッダ (`polished` を含む)。
- `work.md` — タイトル・モード。

## 手順

1. **前提確認**: 計画上の公開対象シーンが generated で、契約が approved、
   本文があること。欠けがあれば一覧にして作者に報告し、勝手に
   プレースホルダを公開物へ入れない。
2. **原稿を書き出す**:
   `python3 tools/export.py --workdir . --md --txt --title "<作品タイトル>"`
   (必要なら `--epub`)。標準で `out/<title>.md`、`--txt` で
   `out/<title>.txt`、`--epub` で `out/<title>.epub`。
   - export は実行前に lint を走らせ、E があれば**書かずに失敗する**。
     `--no-lint` は使わない (使った場合は理由を記録する)。
   - 話見出し `## 第N話 タイトル` の挿入・YAML ヘッダ除去・`---` 区切りの
     処理はツールが行う。手で整えない。
   - シーン間に区切り (`◆` 等) を入れたい場合は `--separator "◆"` を付ける。
     md/txt で同じ区切りに揃う。
3. **公開版を確定する**:
   `python3 tools/export.py --workdir . --release`
   - `--release` は `tools/release_gate.py` の検査を通し、`out/` に公開物
     以外があれば失敗する。レポートは `build/export-report.md`。
   - 失敗 (exit 1) したら**公開しない**。どの検査が落ちたか (E コード・
     ゲート項目) を作者に報告し、修正後に再実行する。
4. **出力を確認する**:
   - `out/` にあるのは `<title>.md` / `.txt` / `.epub` のみ。
   - URL・出典・台帳ID・制作メモが1つでもあれば公開ゲートで落ちる
     (`manuscript_lint.py` の E L001 / L002 / L003)。out/ は公開物だけ。
   - 作業物 (lint/export レポート・epub 中間・版違いの下書き) は `build/`。
     企画書・調査ノート・スクリプトは元の場所 (`plan/` `research/`) に置く。
5. **報告**: 話数・シーン数・文字数・欠けているシーン・exit code・
   出力ファイルパス。字数は下限確認の材料であり、水増しの理由にしない。

## 出力・記録先

- 公開物: `out/<title>.md` / `.txt` / `.epub`
- 作業物: `build/export-report.md` ほか `build/` 以下
- 失敗時は作者への報告 (何が落ちたか・次の一手)

## auto 運転中の扱い

export は無害な生成物なので承認不要。品質停車点で beta-read に渡す原稿を
出す、作者の「読みたい」に応える、の用途で自律的に走らせてよい。
ただし `--release` は release-gate と polish 記録が揃ってから。

## 注意

- `out/` は生成物置き場。正典・計画・契約の状態には触れない。
- 同じファイル名への上書きでよい。重要な版を残す場合は `build/` に
  版違いを置く (`out/` には公開物だけ)。
- stale export に注意: scenes を変更したら export を再実行する。古い
  `out/` を残したまま「公開した」と報告しない。

## アンチパターン

- `cat scenes/*.md > out/manuscript.md` のような手作業連結。
- `out/` に企画書・調査ノート・スクリプト・リンク集を置く。
- lint E を無視するために `--no-lint` を使う。
- release-gate の失敗を握りつぶして「公開した」と報告する。
- scenes を直したのに再 export しない (stale export)。
- 文字数が足りないからと export 時点で本文を足す (場面化は write-scene /
  polish の仕事)。
