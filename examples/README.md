# examples/ — 実例で学ぶ

> 現行の規範を「読んで分かる」形にした実例集。文章で説明するより、
> 旧手順 と 現行 を並べ、最小作品を動かすほうが速い。
> ここにある作品は規範の見本であり、実在の出版物ではない。

## examples/before-after.md — 旧手順 要約体 → 現行 場面化

旧手順で書かれた失敗作 (本キット開発時に観測した実運用データ。リポジトリ外・非公開) の第1話を、
現行の規範で場面として書き直した実例。冒頭の引用、9症状の診断表、
1,537字のオリジナルリライト、9項目の注釈、数値比較を収録する。

- 何が分かるか: 「あらすじを書く」と「場面を書く」の差。要約体の見分け方。
  フック・転・代償・引きの作り方。
- 使い方: 自分の原稿の冒頭400字を、診断表 (§2) に当てはめる。
- 注意: このファイルは規範の説明用であり公開原稿ではない。旧手順の引用部は
  `tools/manuscript_lint.py` が **E L003 (ビート見出し) / E L009 (`(了)`)**
  を検出することを意図している (現行のリライト本文そのものは E を出さない。
  文書全体は原稿ではないため、見出し類を lint にかけると E L003 が出る)。

## examples/sample-work/ — 最小作品 (1話2シーン)

現行 で作った小さな作品『忘れ物預かり所』の全ファイル。`work.md` の
「面白さの設計」、`craft/engine.md`、`craft/voice.md`、craft 欄つき契約、
`polished: true` の本文、推敲記録、興味スコアカード、公開チェックリストまで
一通り揃っている。**エージェントが真似する雛形**として使う。

```text
examples/sample-work/
├── work.md                         作品情報 + 面白さの設計
├── craft/engine.md                 物語エンジン
├── craft/voice.md                  文体の声
├── canon/facts.md                  正典メモ (f001–f003)
├── entities.md                     登場要素 (ent-c01 等)
├── knowledge.md                    知識イベント
├── events.md                       出来事 (時系列)
├── foreshadowing.md                伏線台帳 (fs01 回収済み / fs02 意図的未回収)
├── plan/tree.md                    第1話 → 2シーン + hook/promise/detonator/payoff
├── contracts/1-1.md, 1-2.md        craft 欄つき契約 (status: approved)
├── scenes/1-1.md, 1-2.md           本文 (polished: true)
├── reviews/polish-20261117.md    推敲記録 (削除率13.9%)
├── reviews/beta-第1話-2026-11-17.md       興味監査 (スコアカード合格)
├── reviews/release-checklist-20261117.md 公開チェックリスト (記入例)
├── reviews/release-20261117.md     release_gate.py の生成レポート
├── build/export-report.md          export の生成レポート (公開しない)
└── out/忘れ物預かり所.md / .txt    公開原稿 (export 形式)
```

### 動かし方

```bash
# 1) 本文の衛生検査 (E 0 件が目標)
python3 tools/manuscript_lint.py examples/sample-work/out/*.md

# 2) 状態検査 (契約・推敲記録・out/ 清浄・craft の有無)
python3 tools/release_gate.py --workdir examples/sample-work

# 3) 公開用 export (lint + gate を通してから書き出す)
python3 tools/export.py --workdir examples/sample-work --release --md --txt
```

### 読む順番 (エージェント向け)

1. `work.md` の「面白さの設計」 — 何を面白いと決めたか。
2. `craft/engine.md` — 欲求・対立・代償・時計。
3. `contracts/1-1.md` の craft 欄 — 場面をどう設計したか。
4. `scenes/1-1.md` — 設計が本文でどう演じられたか。
5. `reviews/polish-20261117.md` — 何を削り、何を具体化したか。
6. `reviews/beta-第1話-2026-11-17.md` — 外部読者の採点 (スコアカード)。

### 注意

- `reviews/` のスコアカードとチェックリストは**記入例**である。実際の
  外部読者テストは、`canon/` `plan/` を知らない新規コンテキストで行う
  (`.agents/skills/beta-read/SKILL.md`)。
- `out/` は `tools/export.py --workdir examples/sample-work --release --md --txt`
  の生成物である。`build/` は作業物で、公開しない。
- 日付はすべて 2026-11-17。

## 関連

- `docs/CRAFT.md` — 技芸の正本 (10原則・フック5・引き5・場面設計・具体化)
- `.agents/skills/spark/SKILL.md` — 企画の作り方
- `.agents/skills/scene-craft/SKILL.md` — 場面設計
- `.agents/skills/polish/SKILL.md` — 推敲
- `.agents/skills/release-gate/SKILL.md` — 公開ゲート
- `templates/interest-scorecard.md` / `templates/polish-report.md` /
  `templates/release-checklist.md` — 記録用紙
