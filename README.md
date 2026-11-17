# Vibe作家 — 面白さを工程にする AI 執筆ワークスペース

AI エージェントを**物語のオーケストレーター兼作家**として動かすための規範キット。
人間はノリと方向性を語り、面白さの設計・整合性・改稿・公開の作業はエージェントが
請け負う。ファイルと Python だけで完結し、特定のエージェントハーネスに依存しない。

**中核原則: 面白さが目的。整合性はその下支え。**

## これは何か

- 作品ディレクトリに展開して使う、**ファイルだけの創作環境**
- エージェントが「企画 → 設計 → 執筆 → 外部読者テスト → 推敲 → 公開」を回す
- 人間は創作上の決定と方向性に集中する。正典・時系列・伏線・公開物の同期は
  エージェントとツールが担う
- 面白さを設計・検査・改稿するための語彙と手順を提供する
- 公開物の衛生 (URL・出典・制作メモ・重複・stale export・`out/` の汚染) は
  決定論的ツールで機械的に守る

### 向いている用途

- 短編から連載まで、AI と一緒に最後まで書き切りたい
- 設定・時系列・伏線・公開物の管理を会話とファイルに任せたい
- 「読者が次を読みたくなるか」を工程として回したい

### 向かない用途

- 一発生成のテキストが欲しいだけ (このキットは工程が重い)
- 人間が全ファイルを手で管理したい (会話を入口にする設計)

## 使い方

```sh
# 1. 作品ディレクトリを作る (規範・スキル・ツール・craft/・build/・out/ を生成)
python3 tools/init_work.py my-work --title "作品名" --mode short
cd my-work

# 2. エージェントハーネスを起動して話す
#    「面白い短編を書きたい。まず企画から」   → spark
#    「計画を立てて」                         → plan-work
#    「書いて」                               → scene-craft → write-scene
#    「読者目線で読んで」                     → beta-read
#    「推敲して」                             → polish
#    「公開して」                             → release-gate → export
```

既存のディレクトリに後から導入する場合:

```sh
cp -r /path/to/vibe-sakka/.agents ./
cp /path/to/vibe-sakka/AGENTS.md ./
cp -r /path/to/vibe-sakka/tools ./
cp -r /path/to/vibe-sakka/templates ./
mkdir -p craft build
```

## 工程

### 短編モード (short, 既定)

```
init_work.py → spark → engine → plan(簡易) → contract(1枚) →
write-scene → beta-read → revise → polish → release-gate → export
```

- 帳簿 (正典・変更セット・提案) は必要になった時だけ
- 契約は1シーン1枚。推敲と公開ゲートは省略しない

### 連載モード (serial)

帳簿 (正典・知識・伏線・変更セット) を維持し、各話に
`hook / promise / detonator / payoff` を記入。話ごとに外部読者テストを行い、
全話完走後に推敲 → 公開ゲート → export。

### 品質停車点

auto 運転では、話ごとに外部読者テストとスコアカードを挟む。
退屈や混乱の指摘が閾値を超えたら改稿し、直らなければ止めて作者に報告する。
「文字数を満たすための水増し」ではなく「場面化」と「削減」で直す。

## ツール

すべて Python 3 標準ライブラリ。**キットの `tools/` は作品ディレクトリには自動で
コピーされない。** 作品に `tools/` をコピーした場合は作品ディレクトリで
`python3 tools/... --workdir .`、キットから呼ぶ場合は
`python3 /path/to/vibe-sakka/tools/... --workdir /path/to/work` で実行する。

```sh
# 原稿の衛生 lint (URL/出典/台帳ID/ビート見出し/重複/stale export)
python3 tools/manuscript_lint.py --workdir . out/*.md
python3 tools/manuscript_lint.py --json --workdir . out/*.md
python3 tools/manuscript_lint.py --fix scenes/*.md      # 安全な自動修正のみ

# export: 計画順に連結。lint E があれば書かずに失敗
python3 tools/export.py --workdir . --md --txt --epub
python3 tools/export.py --workdir . --release --no-report   # 公開ゲート込み

# 公開ゲート: 契約・推敲・外部読者テスト・out/ 清浄・lint
python3 tools/release_gate.py --workdir .
python3 tools/release_gate.py --workdir . --no-report

# ツール自体の自己テスト (CI と同じ)
python3 tools/selftest.py
```

I/F・終了コード・既知の限界は `tools/README.md`。

## ディレクトリ構成 (作品ディレクトリ)

```
work.md              作品情報・面白さの設計・執筆ポリシー
craft/engine.md      物語エンジン (欲求・対立・代償・時計・約束)
craft/voice.md       文体の声 (サンプル段落・人称・テンポ)
canon/facts.md       正典メモ (確度ラベル・[秘密])
canon/history.md     正典の改訂履歴
entities.md          登場要素 (人物/場所/組織/物品/概念)
knowledge.md         誰が何をいつ知ったか
events.md            作中の出来事 (時系列の正本)
foreshadowing.md     伏線台帳 (張設・意味・回収予定・期限)
plan/tree.md         計画ツリー (話 → シーン)
contracts/<scene>.md Writing Contract (status・craft 欄)
scenes/<E>-<S>.md    本文 (rev・polished フラグ)
reviews/*.md         レビュー・興味監査・推敲記録・公開レポート
research/*.md        実世界の事実調査 (出典つき。本文へコピーしない)
proposals/ changesets/ scratch/ dialogue.md   提案・変更管理・メモ・対話ログ
build/               作業生成物 (lint/export レポート。公開しない)
out/                 公開物のみ (<title>.md / .txt / .epub)
```

`out/` には公開物しか置かない。企画書・調査・スクリプト・下書き・リンク集は
`plan/` `research/` `build/` に置く。

## この規範の使い方

- 規範・スキル・テンプレートは**デフォルト**であり、作者が選べば外してよい。
  作品の意図が規範より優先される。
- 機械が止めるのは「公開物の衛生」「壊れた帳簿」「外部読者テストの未実施」だけ。
  文体・構成・ジャンル・実験の可否、外部読者テストの合否は作者が決める。
- チェックリストやスコアカードは思考の補助。埋めること自体が目的ではない。
- 試作 (単場面・実験) は `scratch/` に契約なしで書いてよい。公開対象に
  するときだけ、契約・推敲・公開ゲートを通す。

## 面白さの最低線 (公開前の目安)

1. 冒頭に、読者が知りたくなる何かがある
2. 場面の前後で、状況・関係・認識のどれかが変わる
3. 感情やテーマを説明だけで済ませていない
4. 章末に、次を読む理由が残る
5. 本文に、URL・出典・台帳ID・制作メモがない
6. 外部の初読者テストと推敲の記録がある

## 既存作品への導入

すでに本文・設定・計画がある作品ディレクトリにも導入できる。

```sh
cp -r /path/to/vibe-sakka/.agents ./
cp /path/to/vibe-sakka/AGENTS.md ./
cp -r /path/to/vibe-sakka/tools ./
cp -r /path/to/vibe-sakka/templates ./
mkdir -p craft build

# 診断 (既存形式の互換。公開判定は緩めない)
python3 tools/manuscript_lint.py --workdir . --legacy out/*.md
python3 tools/release_gate.py --workdir . --legacy
```

手順の詳細は `docs/MIGRATION.md`。既存原稿は「推敲 → 外部読者テスト →
公開ゲート」の順に通す。原稿は削る方向に直し、水増ししない。

## ドキュメント

- `AGENTS.md` — 規範 (何を守るか)
- `docs/CRAFT.md` — 技芸の在庫 (フック・場面・台詞・具体化・退屈の症状)
- `docs/PHILOSOPHY.md` — なぜ面白さを工程にするのか
- `docs/DIAGNOSIS.md` — 破綻しない退屈が生まれる構造と対策
- `docs/DESIGN.md` — 設計仕様 (開発者向け)
- `docs/MIGRATION.md` — 既存作品への導入
- `docs/VERIFICATION.md` — 検証手順と実測値
- `tools/README.md` — ツールの I/F と限界
- `examples/` — 要約体 → 場面化の実例、lint 0 の最小作品
- `.agents/skills/` — 作業手順 (14 スキル)

## ハーネス別のスキル配置

| ハーネス | スキルの置き場所 |
| --- | --- |
| Codex / Cursor / Gemini CLI / OpenCode / Amp / Cline … | `.agents/skills/` のまま自動認識 |
| Devin | `.devin/skills/` にコピー |
| Claude Code | `.claude/skills/` にコピー |
| その他 | `AGENTS.md` から各 `SKILL.md` を辿る |

## ライセンス

MIT (LICENSE 参照)。
