# VERIFICATION — v2 の検証手順と結果

このファイルは v2.0.0 時点の受入検証を再現可能な形で記録する。
上から順に実行すれば、キットが壊れていないことを確認できる。

対象環境: Python 3.12+、外部ライブラリなし。ネットワーク・git 不要。

## 1. ツールの自己テスト

```sh
python3 tools/selftest.py
```

期待: `Ran 78 tests ... OK` / exit 0。

内訳:

| テスト | 件数 | 内容 |
| --- | --- | --- |
| test_lint | 26 | E L001–L012 / W の検出、`--fix`、stale、`--json`、L004 章スコープ、L006 文脈 |
| test_export | 23 | plan 解析、`--order`、YAML 除去、見出し、md/txt/epub、`--separator`、staging、lint で書かない |
| test_release_gate | 22 | v2 合格/不合格、v1 (`--legacy`) の互換、beta/polish 内容、設計7項目、伏線期限、out/ 汚染 |
| test_init_work | 7 | 骨格生成、`--force`、上書きしない、mode |

## 2. 見本作品 (v2 で作った最小作品)

```sh
python3 tools/manuscript_lint.py --workdir examples/sample-work examples/sample-work/out/*.md
# 期待: E 0 / W 4 / exit 0 (W は出荷可の推敲対象)

python3 tools/release_gate.py --workdir examples/sample-work
# 期待: 合格 (gate E 0 / W 0, lint E 0 / W 12) / exit 0

python3 tools/export.py --workdir examples/sample-work --release --md --txt --no-report
# 期待: exit 0。staging 経由で out/ に md/txt のみ
```

ゲートは `out/*.md` / `out/*.txt` / `scenes/*.md` のすべてを lint し、
`reviews/beta-*.md` (external + interest_gate: pass) と
`reviews/polish-*.md` (before/after または cut_rate) の**中身**も検査する。

## 3. v1 作品の検査 (legacy)

`--legacy` は **v1 形式の互換** (面白さの設計7項目・`craft/`・`polished` フラグ・
表形式 plan を warn に落とす) であり、**公開判定は緩めない**。
polish/beta 記録・out/ 清浄・lint E 0 は legacy でも error。

```sh
# v1 の原稿: 推敲漏れ (重複 (了)) と stale export を検出
python3 tools/manuscript_lint.py --workdir <v1作品> <v1作品>/out/<title>.md
# 期待: 問題があれば E L009 / E L007 で exit 1

# v1 の要約体: ビート見出しを検出
python3 tools/manuscript_lint.py <v1作品>/scenes/1.md
# 期待: E L003 を検出し exit 1

# v1 の公開状態: beta/polish 欠落・out/ 汚染・lint E を error
python3 tools/release_gate.py --workdir <v1作品> --legacy
# 期待: 不合格 (exit 1)。何を直すべきかが列挙される
```

## 4. v1 原稿の再 export (衛生修復)

```sh
# 1. 本文のアーティファクトは scenes/ (正本) に対して直す。
#    --fix は安全な自動修正のみ (本文の語句は書き換えない)。
python3 tools/manuscript_lint.py --fix scenes/*.md
python3 tools/manuscript_lint.py scenes/*.md        # E 0 を確認

# 2. export (lint E が残っていれば out/ に書かずに失敗する)
python3 tools/export.py --workdir <v1作品> --title "<title>" \
  --md --txt --epub --separator "◆"
```

`(了)` の重複・md/txt の区切り不統一・stale export が解消され、
lint E 0 で出力される。旧 `out/` は事前に `build/legacy-out/` 等へ退避する。

## 5. 新規作品の雛形

```sh
python3 tools/init_work.py /tmp/verify-work --title "検証" --mode short
# 期待: work.md / canon/ / craft/engine.md / craft/voice.md /
#       plan/tree.md / contracts/ / scenes/ / reviews/ / build/ / out/ を生成
```

直後の骨格は未記入のため、`release_gate.py` は**不合格**になる (正しい)。
面白さの設計・craft・契約・本文・beta・polish を埋めてからゲートを通す。

## 6. before/after の規範例

`examples/before-after.md` は説明用のため、v1 引用部に意図的に
lint E (ビート見出し・制作メモ) を含む。**CI の lint 対象外**。
lint 0 の実例は `examples/sample-work/` を参照。

## 7. CI

`.github/workflows/kit-ci.yml` が push / PR ごとに次を実行する:

- `python3 tools/selftest.py`
- `python3 tools/manuscript_lint.py --workdir examples/sample-work examples/sample-work/out/*.md`
- `python3 tools/release_gate.py --workdir examples/sample-work`
- `python3 tools/export.py --workdir examples/sample-work --release --md --txt --no-report`

## 8. v2.0.0 時点の実測値

| 検証 | 結果 |
| --- | --- |
| `tools/selftest.py` | 78 tests / OK |
| sample-work lint (md) | E 0 / W 4 / exit 0 |
| sample-work gate | 合格 (gate E 0 / W 0, lint E 0 / W 12) |
| sample-work export --release | exit 0 (staging → out) |
| v1 原稿 (ato-de-yomu) lint | E 0 / W 20 / exit 0 (修復済み) |
| v1 原稿 (ato-de-yomu) gate --legacy | 不合格 E 2 (beta/polish なし。正しい判定) |
| v1 要約体 (browser-wars 全12話) | E 60 (L003 ビート見出し等) / exit 1 |
| 監査の再現ケース | txt URL・scenes の L009・beta なし・空 polish・空の設計・期限誤読・未定誤爆・章またぎ重複 をすべて適切に判定 |
