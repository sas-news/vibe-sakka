# reviews/release-checklist-20261117.md — 公開前チェックリスト (手動記録)

```yaml
date: 2026-11-17
work: "忘れ物預かり所"
version: v1.0.0
releaser: ai
auto_report: reviews/release-20261117.md
```

## 0. 前提

- [x] `polish` 済み (`reviews/polish-20261117.md`)
- [x] `beta-read` を外部コンテキストで実施 (`reviews/beta-第1話-2026-11-17.md`、`context: external`)
- [x] interest gate: pass (high 0 / medium 0。fail でも作者判断で公開可)
- [x] 全シーンの契約が `status: approved`
- [x] `scenes/*.md` の `polished: true`

## 1. 決定的検査 (コマンド)

```bash
python3 tools/manuscript_lint.py --workdir . scenes/*.md
python3 tools/manuscript_lint.py --workdir . out/*.md
python3 tools/manuscript_lint.py out/*.txt
python3 tools/release_gate.py --workdir .
python3 tools/export.py --workdir . --release --md --txt
```

- [x] lint (scenes): E 0件 / W 3件
- [x] lint (out md): E 0件 / W 4件、lint (out txt): E 0件 / W 5件、lint (scenes): E 0件 / W 3件
- [x] release_gate: exit 0 (beta 記録 external・スコア記載を検査済み。合否は警告)
- [x] export --release: exit 0、`out/` は `.md` `.txt` のみ
- [x] 3コマンドを同じ原稿に対して実行した。

## 2. 公開物 (out/) の清浄

- [x] 企画書・調査・スクリプト・下書き・画像なし
- [x] URL・出典・`research/` 参照なし
- [x] 台帳ID・ファイル名・制作メモなし
- [x] ビート見出しなし
- [x] `(了)` 重複・区切り混在なし

## 3. 全話の意味判断

| 話 | 冒頭フック (引用) | 章末の引き (引用) | interest gate |
| --- | --- | --- | --- |
| 第1話 | 忘れ物預かり所は、駅の西口に、昨日からあった。 | 明日は、何を忘れよう。彼女は、そう思った。 | pass |

## 4. 引用ファイアウォール

- [x] 外部資料なし (創作のみ)

## 5. 最終

- [x] タイトル・版表記が正しい
- [x] `work.md` status: active
- [x] 自動レポート `reviews/release-20261117.md` を確認した
- [x] 作者に公開可と生成物パスを報告
