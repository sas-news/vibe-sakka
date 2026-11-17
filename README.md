# Vibe作家 v2 — 面白さを工程にする AI 執筆ワークスペース

AI エージェントを**物語のオーケストレーター兼作家**として動かすための規範キット。
人間はノリと方向性だけを語り、面白さの設計・整合性・改稿・公開の作業は
エージェントが請け負う。どんなエージェントハーネス (CLI・IDEエージェント等) でも
動く、ファイルと Python だけで完結する創作環境。

**中核原則: 面白さが目的。整合性はその下支え。**

---

## v1 の何がダメだったか

v1 は「破綻しない作品」を作る装置としては動いた。しかし **「面白い作品」を
作る装置ではなかった**。実運用では次のことが起きた:

- 12話の「小説」が全編 8,500 字、1話 700 字。全話が `一 / 二 / 三` の
  ビート見出し付きの**あらすじ**として出荷された。
- 原稿に `(了)` の重複、区切りの不統一、誤字、挿入パスによる台詞破損が
  残ったまま公開された (推敲工程が存在しなかった)。
- `out/` に企画書・調査リンク・生成スクリプトが作品と同居し、公開物と
  作業物の区別がなかった。
- 字数不足への対処が「膨張パス」(挿入で水増し) だった。
- レビューは「禁止事項 OK / 秘密 OK」とだけ記録し、**退屈を検査しなかった**。

原因は単純で、**面白さを設計・検査・改稿・公開する工程が存在しなかった**。
writer プロンプトに「面白く書け」は一行もなく、帳簿の同期が品質のすべてを
占めていた。

## v2 が変えたこと

| 工程 | v1 | v2 |
| --- | --- | --- |
| 企画 | 前提を聞いて計画へ | `spark` で角度・ログライン・フック・固有の具体物を設計 |
| 設計 | 契約は必須イベントのみ | 物語エンジン + 場面の欲求/障害/転/代償/スキップテスト |
| 執筆 | 「矛盾しないこと」が指示 | 「読者を退屈させないこと」が指示。要約体は自動失格 |
| 検査 | 整合性のみ | 整合性 + **外部読者による興味監査** (スコアカード) |
| 改稿 | 整合性違反の書直し1回 | 興味の revise + **全原稿の推敲 (削る/具体化/声/読み上げ)** |
| 公開 | 連結して `out/` へ | **公開ゲート** (lint 0 error / out 清浄 / 推敲記録) |
| 帳簿 | 短編でも全同期 | 短編は軽量モード。帳簿は必要になった時だけ |
| 衛生 | 人の注意力 | `tools/` の決定論的 lint (URL/ID/ビート見出し/重複/stale) |

## 30秒でわかる使い方

```sh
# 1. 作品ディレクトリを作る (テンプレート・craft/・build/・out/ を生成)
python3 /path/to/vibe-sakka/tools/init_work.py my-work --title "作品名" --mode short
cd my-work

# 2. エージェントハーネスを起動して話す
#    「面白い短編を書きたい。まず企画から」→ .agents/skills/spark が動く
#    「計画を立てて」→ plan-work
#    「書いて」→ scene-craft → write-scene
#    「読者目線で読んで」→ beta-read (新規コンテキスト必須)
#    「推敲して」→ polish
#    「公開して」→ release-gate → export

# 3. 公開前チェック (人が打ってもよい)
python3 /path/to/vibe-sakka/tools/manuscript_lint.py out/*.md
python3 /path/to/vibe-sakka/tools/release_gate.py
```

キットを使わず既存ディレクトリに展開する場合:

```sh
mkdir my-work && cd my-work && git init   # git 推奨
cp -r /path/to/vibe-sakka/. .            # 末尾「/.」で .agents/ 等もコピー
```

## インストール要件

- Python 3.12 以上 (ツールは標準ライブラリのみ。追加インストール不要)
- エージェントハーネス (Codex / Cursor / Gemini CLI / Claude Code / Devin /
  OpenCode / Cline / DSH …)
- git (推奨。原稿と正典の履歴・ロールバック用)

### ハーネス別のスキル配置

| ハーネス | スキルの置き場所 |
| --- | --- |
| Codex / Cursor / Gemini CLI / OpenCode / Amp / Cline … | `.agents/skills/` のまま自動認識 |
| Devin | `.devin/skills/` にコピー |
| Claude Code | `.claude/skills/` にコピー |
| その他 | `AGENTS.md` 内の対応表から各 `SKILL.md` を辿って運用 |

スキルをどこにも置かなくても `AGENTS.md` が常時読まれて規範として機能する。
`AGENTS.md` は「何を守るか」、`.agents/skills/` は「どうやるか」、
`docs/CRAFT.md` は「面白さの技芸」、`tools/` は「機械が捕まえる衛生」。

## 工程の全体像

```
[作者のノリ]
   │
   ▼
spark          企画を面白くする (5案 → 角度 → ログライン → フック草案)
   │           craft/engine.md に約束・欲求・対立・代償・時計・快楽を書く
   ▼
plan-work      話ごとに hook / promise / detonator / payoff を必須記入
   │           (あらすじの時点で面白くなければ本文にしない)
   ▼
scene-craft    場面の欲求・障害・転・代償・入/出・スキップテスト
   ▼
write-scene    場面として書く。要約禁止。具体・台詞・五感・声・転。
   │           整合性検査 + セルフ興味監査
   ▼
beta-read      新規コンテキストの読者が興味スコアカードで採点 (章ごと必須)
   │           high 1 or medium 3 → revise (最大2回) → ダメなら作者へ
   ▼
polish         全原稿の推敲。10–20%削る / 説明を殺す / 声 / 読み上げ /
   │           アーティファクト除去。reviews/polish-*.md を残す
   ▼
release-gate   lint 0 error / out/ 清浄 / 推敲記録 / 状態検査
   ▼
export         out/<title>.md / .txt / .epub
   ▼
[読者]
```

## ツール

すべて Python 3 標準ライブラリ。作品ディレクトリで実行する。

```sh
# 衛生 lint: URL・出典・台帳ID・ビート見出し・重複・文字化け・stale export
python3 tools/manuscript_lint.py out/作品名.md
python3 tools/manuscript_lint.py --json out/作品名.md
python3 tools/manuscript_lint.py --fix out/作品名.md        # 安全な自動修正のみ
python3 tools/manuscript_lint.py --workdir . out/作品名.md  # scenes との stale 検査

# export: plan/tree.md の順に連結。lint で E があれば書かずに失敗
python3 tools/export.py --workdir . --md --txt --epub
python3 tools/export.py --workdir . --release   # 公開ゲート込み

# 公開ゲート: 章構成・craft ファイル・契約・polished フラグ・伏線・out/ 清浄
python3 tools/release_gate.py --workdir .
python3 tools/release_gate.py --workdir . --legacy   # v1 作品の互換検査

# 作品の雛形生成
python3 tools/init_work.py ../new-work --title "新作" --mode short

# ツール自体の自己テスト (CI と同じ)
python3 tools/selftest.py
```

詳細は `tools/README.md`。

## ディレクトリ構成 (作品ディレクトリ)

```
work.md              作品情報・面白さの設計・執筆ポリシー・canon_revision
craft/engine.md      物語エンジン (欲求/欠落/恐怖・対立・代償・時計・約束・快楽)
craft/voice.md       文体の声 (サンプル段落・人称・テンポ・禁止語彙)
canon/facts.md       正典メモ (確度セクション別、[秘密] ラベル)
canon/history.md     正典の改訂履歴 (追記のみ)
entities.md          登場要素 (人物/場所/組織/物品/概念 + 別名)
knowledge.md         誰が何をいつ知ったか
events.md            作中の出来事 (作中時間・参加者・結果。時系列の正本)
foreshadowing.md     伏線台帳 (張設場所・意味・回収予定・状態)
plan/tree.md         計画ツリー (話→シーン。hook/promise/detonator/payoff)
plan/                企画書・調査メモの退避先 (公開物ではない)
contracts/<scene>.md Writing Contract (status 必須。craft 欄つき)
scenes/<E>-<S>.md    本文 (先頭に rev、polished フラグ。旧版は scenes/history/)
proposals/*.md       保留中の提案
changesets/*.md      変更セット (影響分析・承認・適用の記録)
reviews/*.md         レビュー・興味監査・推敲記録・公開レポート
research/*.md        実世界の事実調査 (出典つき。本文へコピー禁止)
scratch/             行き場のないアイデア・断片 (正典ではない)
build/               作業生成物 (lint/export レポート。公開しない)
out/                 公開物のみ (manuscript.md / .txt / .epub)
dialogue.md          対話ログ (決定の出所として追記)
```

**`out/` には公開物しか置かない。** 企画書・調査・スクリプト・リンク集・
下書きは `plan/` `research/` `build/` に置く。これは趣味ではなく公開ゲートの
検査対象。

## 短編モードと連載モード

- **short (既定)**: 短編・単発。`spark` → 簡易計画 → 契約1枚 → 執筆 →
  興味監査 → 推敲 → 公開。正典・変更セットは必要時のみ。
- **serial**: 連載・長編。v1 の帳簿 (正典・知識・伏線・変更セット) を維持し、
  話ごとの外部読者テストと品質停車点を必須にする。

`work.md` のモードで切り替わる。作品形態 (短編/連載/続編) の詳細は
`AGENTS.md`。

## 面白さの最低線 (これを下回る原稿は公開しない)

1. 冒頭 3 段落に「異物」か「問い」か「声」がある (説明から始めない)。
2. 各場面に欲求・障害・転・代償がある (何も変わらない場面がない)。
3. 感情は名指しせず、動作・具体物・台詞で示されている。
4. 章末に読者が持つ未解決の問いがある。
5. ビート見出し・あらすじ・台帳ID・URL・制作メモが本文にない。
6. 外部の初読者が「次を読みたい」と答えた (スコアカードで確認)。
7. 推敲記録 (`reviews/polish-*.md`) と公開ゲートの合格記録がある。

## v1 作品の移行

```sh
# キットの規範・スキル・ツールをコピー (作品データは保持)
cp -r /path/to/vibe-sakka/.agents ./
cp /path/to/vibe-sakka/AGENTS.md ./
cp -r /path/to/vibe-sakka/tools ./
cp -r /path/to/vibe-sakka/templates ./
# 既存作品の検査 (craft/ や polished フラグがなくても動く)
python3 tools/manuscript_lint.py --workdir . --legacy out/*.md
python3 tools/release_gate.py --workdir . --legacy
```

移行手順の詳細は `docs/MIGRATION.md`。既存原稿は「推敲 → 興味監査 →
公開ゲート」の順に通す。原稿そのものは削る方向にしか直さない
(水増ししない)。

## ドキュメント

- `AGENTS.md` — 規範 (何を守るか)
- `docs/PHILOSOPHY.md` — なぜ面白さを工程にするのか
- `docs/DIAGNOSIS.md` — v1 の失敗モードと v2 の対応
- `docs/CRAFT.md` — 面白さの技芸 (フック・場面・台詞・推敲・AI の退屈症状)
- `docs/DESIGN.md` — v2 の設計仕様 (開発者向け)
- `docs/MIGRATION.md` — v1 からの移行
- `docs/VERIFICATION.md` — 検証手順と実測値
- `.agents/skills/` — 作業手順 (14 スキル)
- `tools/README.md` — ツールの I/F と限界
- `examples/before-after.md` — 要約体 → 場面化の実例

## ライセンス

MIT (LICENSE 参照)。
