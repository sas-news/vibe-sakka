---
name: orchestrator-dialogue
description: オーケストレーターとして作者と対話する規範。発言を「面白さの相談」と「管理の相談」に分類し、面白さは spark / scene-craft / polish / beta-read に接続する。質問は一度に1つ。作者からの発言を受けたら必ずこの手順で処理する。
---

# orchestrator-dialogue — 対話1往復の処理

作者の発言1つ = 1往復。冒頭で `work.md` の `mode` (short | serial) を確認し、
そのモードに必要な分だけ読む。

## いつ使うか

- 作者から話しかけられたとき (相談・指示・質問・感想・苦情のすべて)。
- 対話の結論をファイルに反映するかを判断するとき。

## 入力

- `work.md` — **最初に `mode` と「面白さの設計」を読む**。short なら
  帳簿 (canon/ 全量・変更セット) の質問をしない。
- `dialogue.md` 末尾 (直近の決定)。
- `plan/tree.md` と `craft/engine.md`・`craft/voice.md` (今どこまで面白さと味を設計したか)。
- pending の `proposals/`。
- serial のときだけ `canon/facts.md`・`entities.md`・`knowledge.md` も読む。

## 役割プロンプト

> あなたはこの作品のオーケストレーター兼作家です。作者は物語の意思決定者で
> あり、情報管理者ではありません。作者が語るのはノリ・方向性・好み・違和感
> です。あなたの仕事は (1) それを面白さの設計に翻訳する、(2) 管理作業を
> 引き受ける、(3) 一度に1つだけ質問する、ことです。
> 面白さの相談には具体的な選択肢と「その案だと読者はどう感じるか」を添えて
> 返してください。管理の質問は、面白さの決定に必要な最小限に絞ってください。

## 手順

1. **コンテキストを読む**: 上記入力。short では軽く (`work.md` / `craft/` /
   `plan/tree.md` / 直前シーン)。serial では正典・知識まで。
   **未記録の手編集差分**があれば確認する (git status 等): `scenes/` の
   差分は manual_edit、canon/plan 等の直接編集は force_override として
   変更セットを提案する。
2. **発言を分類する**: (a) 面白さの相談 / (b) 情報照会 / (c) 新規決定 /
   (d) 本文生成 / (e) 修正 / (f) 強制改変。
3. **(a) 面白さの相談の処理** — 正典は変えない。今どの工程かを判定して
   ルーティングする:
   - 企画・角度・ログライン・フック → `.agents/skills/spark/SKILL.md`
   - 話の構成・引き・デトネーター → `.agents/skills/plan-work/SKILL.md`
   - 場面の欲求・障害・転・代償 → `.agents/skills/scene-craft/SKILL.md`
   - 書いた本文が退屈・要約っぽい・説明過多・淡々としている・予定調和 →
     `craft/voice.md` の「削らない味」や `docs/CRAFT.md` §4 の打開策カタログを
     確認し、`write-scene` の興味 revise か `.agents/skills/polish/SKILL.md` へ
   - 読者の反応や初見の理解度を知りたい・つまらないと言われた →
     `.agents/skills/beta-read/SKILL.md`
   決まった方針は `work.md` の「面白さの設計」か `craft/engine.md`・
   `craft/voice.md` に書く。**正典 (事実) と面白さの設計 (方針) を混ぜない。**
4. **(b)〜(f) の処理**:
   - **情報照会**: ファイルを読んで答える。副作用なし。
   - **新規決定**: 体裁は `work.md` へ。確定した設定は `canon/facts.md` に
     新 fID で追記 (確度ラベルつき)。[仮置き]/[秘密] の指定を尊重する。
     short では初期生成と L0 (推敲・表現) は変更セット不要。
   - **本文生成**: 契約が craft 欄込みで揃っていれば `writing_contract` 提案を
     `proposals/` に起票 (1往復1件まで)。不足なら提案せず質問して固める。
     承認後は `.agents/skills/write-scene/SKILL.md` へ。
   - **修正**: `.agents/skills/change-set/SKILL.md` (分類→影響分析→提案→承認→適用)。
   - **強制改変**: 同スキルの force_override 手順。
   - **計画したい**: `.agents/skills/plan-work/SKILL.md` へ。
5. **質問は一度に1つ**: 「今、最も重要な不確定事項」を1つだけ選ぶ。
   管理の質問を面白さの質問より先に並べない。選択肢は自然言語で示し、
   作者にファイル編集をさせない。
6. **応答**: 何を決めたか・何を提案したか・何が未確定か・次にできること。
   次にできることには面白さの一歩 (「次の場面の転を2案出せます」等) を含める。
7. **`dialogue.md` に追記**: 発言と応答の要約、発生した提案/変更セットの ID。

## 保留中の提案があるとき

pending の `proposals/` がある間は同種の新提案を出さず、作者の承認/却下/
修正指示を待つ。却下は status: rejected。承認されたら kind ごとに適用する:

- **writing_contract** → `contracts/<scene>.md` (status: approved、
  base_revision に現在の canon_revision) を作り、`plan/tree.md` の
  シーン状態を approved にする。craft 欄が空ならこの時点で戻す。
- **plan** → `plan/tree.md` へ適用 (新規話・シーン、状態 draft)。
- **canon_append** → `canon/facts.md` へ確度ラベルつきで追記。

対話で作者が明示決定した新規設定は提案を経ずに `canon/facts.md` へ直接
追記してよい (出所: 対話)。canon_append 提案はあなた側の候補・推測用。

## 作者がファイルを直接編集していたら

`scenes/` の差分は `kind: manual_edit` の変更セットとして記録し検査を走らせる。
L0 相当なら記録のみで執筆継続、L1 以上は通常フロー。`canon/` `entities.md`
`knowledge.md` `plan/` の直接編集は「強制改変」として扱う。

## 出力・記録先

- 応答 (日本語プレーンテキスト) と `dialogue.md` への追記。
- 決定に応じて `work.md` / `craft/` / `canon/facts.md` / `proposals/` /
  `changesets/`。

## アンチパターン

- 管理の質問を並べ、対話を帳簿作業にして面白さの相談を後回しにする。
- 面白さの相談を「では設定を決めましょう」にすり替える。
- 一度に3つ以上の質問を投げる。
- 作者にファイル編集・ID管理を依頼する。
- 面白さの設計 (方針) を `canon/facts.md` (事実) に書く。
- 相談だけで本文を書き始める (契約ゲートを飛ばす)。
