# changesets/cs-NNNN-<slug>.md — 変更セット

> 関連する変更をひとまとまりに提示・検査・適用する単位。
> 1ファイル = 1変更セット。

```yaml
id: cs-0001
title: ""
kind: normal            # normal | manual_edit | force_override | revision
status: proposed        # proposed → approved → applied / → rejected
level: L2               # L0 表現のみ / L1 シーン意味変更 / L2 正典・人物・時系列・伏線 / L3 基盤変更(Retcon)
base_revision: 3        # 作成時点の canon_revision (適用前に再確認する)
created: 2026-01-01
```

## 目的

<作者が意図した効果・変更理由>

## ops

<!-- ops の語彙 (1行1op):
- retire_fact f003
- revise_fact f003 → 「新宣言文」 [確度] [秘密]
- add_fact 「宣言文」 [確度] [秘密] (関連: ent-c01)
- set_fact_commitment f003 → committed
- update_work title=… / premise=… / charter…= / policy…=
- rewrite_scene 1-2 → scenes/1-2.md 新本文
- add_entity character 「名前」 別名: … 要約: …
- update_entity ent-c01 …
- retire_entity ent-c01
- add_knowledge_event ent-c01 は f050 を知る — シーン 1-2 (目撃)
- retract_knowledge_event ke01
- add_event 「出来事」 作中時間: … 場所: ent-p01 参加者: ent-c01
- revise_event ev01 → 「新説明」
- retire_event ev01
- add_foreshadow 「内容」 張設: <scene> 意味: … 回収予定: …
- resolve_foreshadow fs01 → 回収: <scene>
- retire_foreshadow fs01 (理由: …)
- update_plan <計画ツリーへの変更内容>
- add_entry <store> <id> 「内容」        # 作品固有の構造化ストア (work.md 登録済み)
- update_entry <store> <id> → 「新内容」
- retire_entry <store> <id>
-->
- <op 1行ずつ>

## 影響分析

- **影響を受けるシーン**: <scene ID と理由>
- **影響を受ける正典・計画**: <ID と理由>
- **人物の知識への影響**: <誰の知識が変わるか>
- **時系列・伏線への影響**:
- **既存の固定事項との衝突**: <なし/あり: 内容>
- **下流で必要な修正案**: <選択肢つきで>
- **未解決の懸念・確信度**:

## 検証結果

<適用前に行った決定的検査の結果。違反があれば保留>

## 承認・適用記録

- 承認: <日時・方法>
- 適用: <実施内容・新しい canon_revision>
- レビュー: reviews/<file> へのリンク / review_required の範囲
- ロールバック: <方法。git ref または打ち消し変更セット>
