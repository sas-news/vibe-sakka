# VERIFICATION — v2 の検証手順と結果

このファイルは v2.0.0 時点の受入検証を再現可能な形で記録する。
上から順に実行すれば、キットが壊れていないことを確認できる。

対象環境: Python 3.12+、外部ライブラリなし。ネットワーク・git 不要。

## 1. ツールの自己テスト

```sh
python3 tools/selftest.py
```

期待: `Ran 61 tests ... OK` / exit 0。

内訳:

| テスト | 件数 | 内容 |
| --- | --- | --- |
| test_lint | 22 | E L001–L012 / W の検出、`--fix`、stale、`--json` |
| test_export | 20 | plan 解析、`--order`、YAML 除去、見出し、md/txt/epub、lint で書かない、`--separator` |
| test_release_gate | 12 | v2 合格/不合格、v1 (`--legacy`) 合格、out/ 汚染、polished、レポート |
| test_init_work | 7 | 骨格生成、`--force`、上書きしない、mode |

## 2. 見本作品 (v2 で作った最小作品)

```sh
python3 tools/manuscript_lint.py examples/sample-work/out/*.md
# 期待: E 0 / W 4 / exit 0 (W は出荷可の推敲対象)

python3 tools/release_gate.py --workdir examples/sample-work
# 期待: 合格 (E 0 / W 0) / exit 0

python3 tools/export.py --workdir examples/sample-work --release --md --txt
# 期待: exit 0。out/ に md/txt のみ
```

## 3. v1 作品の検査 (legacy)

v1 作品を壊さず、問題を検出できることを確認する。

```sh
# v1 の原稿: 推敲漏れ (重複 (了)) と stale export を検出
python3 tools/manuscript_lint.py --workdir <v1作品> <v1作品>/out/<title>.md
# 期待: E L009 / E L007 を検出し exit 1

# v1 の要約体: ビート見出しを検出
python3 tools/manuscript_lint.py <v1作品>/scenes/1.md
# 期待: E L003 を検出し exit 1

# v1 の公開状態: craft/polished/推敲記録の欠落を警告、out/ 汚染を error
python3 tools/release_gate.py --workdir <v1作品> --legacy
# 期待: 不合格 (exit 1)。何を直すべきかが列挙される
```

## 4. v1 原稿の再 export (衛生修復)

```sh
python3 tools/export.py --workdir <v1作品> --title "<title>" \
  --md --txt --epub --separator "◆"
```

`(了)` の重複・md/txt の区切り不統一・stale export が解消され、
lint E 0 で出力される (本文の語句は変えない)。

## 5. 新規作品の雛形

```sh
python3 tools/init_work.py /tmp/verify-work --title "検証" --mode short
# 期待: work.md / canon/ / craft/engine.md / craft/voice.md /
#       plan/tree.md / contracts/ / scenes/ / reviews/ / build/ / out/ を生成
```

`examples/sample-work/` はこの雛形から作った実例 (契約 approved、polished: true、
polish 記録、beta スコアカード、release レポート付き)。

## 6. before/after の規範例

`examples/before-after.md` は説明用のため、v1 引用部に意図的に
lint E (ビート見出し・制作メモ) を含む。**CI の lint 対象外**。
lint 0 の実例は `examples/sample-work/` を参照。

## 7. CI

`.github/workflows/kit-ci.yml` が push / PR ごとに次を実行する:

- `python3 tools/selftest.py`
- `python3 tools/manuscript_lint.py examples/sample-work/out/*.md`
- `python3 tools/release_gate.py --workdir examples/sample-work`

## 8. v2.0.0 時点の実測値

| 検証 | 結果 |
| --- | --- |
| `tools/selftest.py` | 61 tests / OK |
| sample-work lint | E 0 / W 4 / exit 0 |
| sample-work gate | 合格 / exit 0 |
| sample-work export --release | exit 0 |
| v1 原稿 (ato-de-yomu) | 修復前 E 2 → 修復後 E 0 (export.py + `--fix`) |
| v1 要約体 (browser-wars) | E 61 (L003 ビート見出し等) を検出 / gate 不合格 |
| v1 ゲート (--legacy) | 推敲記録なしで不合格 (正しい判定) |
