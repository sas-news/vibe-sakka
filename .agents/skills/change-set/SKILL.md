---
name: change-set
description: 正典・設定・計画・本文の変更を分類→影響分析→変更セット起票→承認→適用する手順。L0-L3 分類、ops 語彙、強制改変 (force_override) もここ。「設定を変えて」「過去話を直して」「無理やり変えて」で使う。
---

# change-set — 変更管理

既存の正典・計画・本文を変える全操作が対象。

## 分類 (L0–L3) — 曖昧なら安全側 (大きい方) に

| L | 内容 | フロー |
| --- | --- | --- |
| L0 表現のみ | 意味・事実・人物状態を変えない文体調整 | 対象の下書き内で差分を作り局所検査。承認は明示指示で足りる |
| L1 シーン意味変更 | 台詞・行動・場面の結果が変わる | 変更セット + シーンの出来事・開始終了状態の再抽出 + 近隣シーン再検査 |
| L2 正典・人物・時系列・伏線 | 設定・知識・関係・場所・作中時間・伏線に影響 | 変更セット + 依存をたどる影響分析 + 明示的承認 |
| L3 基盤変更/Retcon | 作品前提・世界法則・根本動機・長期アーク・結末 | 再計画範囲を明示 + 明示的承認なしに適用しない |

## 手順 (適用フロー)

1. 作者の意図を要約し、曖昧な点を確認する。
2. 現在の `canon_revision` を固定して変更セットの `base_revision` にする。
3. **ops を書く** (`templates/changeset.md` の語彙):
   retire_fact / revise_fact / add_fact / set_fact_commitment /
   update_work / rewrite_scene / add_entity / update_entity /
   retire_entity / add_knowledge_event / retract_knowledge_event /
   add_event / revise_event / retire_event / add_foreshadow /
   resolve_foreshadow / retire_foreshadow / update_plan /
   add_entry / update_entry / retire_entry (作品固有ストア用)。
4. **影響分析**: 変更対象を参照しているものを洗う —
   - `canon/facts.md` の fID を `scenes/` `contracts/` `knowledge.md`
     `plan/tree.md` から grep する
   - `entities.md` の言及・別名が本文に出るシーンを洗う
   - 時系列 (どの出来事が先か)・伏線 (未回収の筋)・後続計画への影響を
     列挙する
   - 固定事項との衝突、下流修正案の選択肢、未解決の懸念・確信度を書く
5. `changesets/cs-NNNN-<slug>.md` に status: proposed で起票し、
   影響分析を自然言語で作者に提示する。
6. **承認後に適用**:
   a. base_revision が変わっていないか再確認 (変わっていたら影響を再計算)
   b. 適用前検証: ops の参照先 (fID/entID/sceneID) が存在し現行か、
      rewrite_scene の本文が契約の決定的検査を通るか確認
   c. ops を適用: facts.md の行を改訂 (ID維持)・entities/knowledge/plan/
      work を更新・scenes は rev+1 で旧本文を history へ
   d. `canon/history.md` に各行の変更を追記、work.md の
      canon_revision を +1
   e. 変更セットの status を applied に、承認者・時刻・結果を記録
   f. 競合や重大な失敗があれば一部だけ確定せず、保留して作者へ説明
7. **レビュー**: `.agents/skills/review-change` を走らせる (L1 以上は必須)。

## 強制改変 (force_override)

対話フローを迂回する緊急経路。レビュー省略の機能ではない。

1. 作者が対象と変更内容を直接指定する。「強制」と明示された操作のみ。
2. 警告を示し、変更理由を記録する。
3. `kind: force_override` の変更セットに変更前スナップショット (対象行の
   現行値) を保存してから適用する (検証ゲートを迂回してよいが記録は必須)。
4. 影響範囲を `review_required` と印す (changeset と影響シーンのヘッダに記す)。
5. 直後に `.agents/skills/review-change` を実行し、衝突・修正候補・不確実性を報告。
6. 関連範囲の自律執筆・自動確定を停止し、修正が必要なら対話に戻す。
7. 修正・再レビュー完了までその範囲を整合性保証済みとして扱わない。

## 本文の手編集 (manual_edit)

作者が `scenes/` を直接編集していたら `kind: manual_edit` の変更セットに
差分を記録して検査を走らせる。L0 相当なら記録のみで執筆継続、
L1 以上なら承認・検査フローに載せる。`canon/` `plan/` 等の構造データの
直接編集は force_override として扱う。

## やってはいけないこと

- ops なし・影響分析なしで既存正典を書き換える
- 承認前に適用する (L0 の明示指示された文体調整を除く)
- 競合した変更をそのまま上書きする
