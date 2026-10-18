---
name: review-change
description: 適用済み変更セット・強制改変・手編集の事後レビュー。影響シーンを決定的検査+criticで検査しfindingsを記録、修正候補の変更セット (kind: revision) を起票する。変更セット適用後に必ず実行する。
---

# review-change — 変更の事後レビュー

変更セット適用・force_override・manual_edit の後に必ず走る。

## 手順

1. **対象を集める**: 変更セットの影響シーン一覧 (本文があるもの、
   最大10シーンまで)、適用後の現行 `canon/facts.md`、各シーンの契約。
2. **各シーンを検査** — `.agents/skills/write-scene` の「検査」節と同じ2段:
   - 決定的検査 (禁止/必須/秘密漏洩/仮置き使用/言及照合)
   - critic 役割プロンプトで意味レベルの検査 (POV・文意矛盾・計画適合)
   - 文体レビュー: 作品の声・テンポ・視点の一貫性・表現の
     反復も確認し、違和感は low の finding か notes に書く
   - 伏線滞留: `foreshadowing.md` で回収予定を過ぎた planted や、
     張設シーンを書き換えられた伏線があれば finding にする
   - 契約がないシーンは「契約なし」として正典との矛盾だけ見る
3. **findings を記録**: `reviews/<date>-cs-NNNN.md` に
   `[severity] rule: detail — 対象` 形式で書く。
   rule の語彙: contract.forbidden / contract.required_events /
   canon.secret_leak / canon.provisional_use / canon.secret_knowledge /
   pov / time / state / plan / plot_thread / style。
   確信を持てないものは notes に (「問題なし」と断定しない)。
4. **報告**: 検査したシーン数・衝突件数・補足件数を作者に伝える。
5. **修正候補 (fixer)** — findings がある場合だけ:

## fixer 役割プロンプト

> あなたは小説作品の「修正案担当」です。レビューで検出された各 finding
> に対し、修正候補を立ててください。修正は必ず以下のいずれか:
> - rewrite_scene: シーン本文を書き換える (修正後の本文全文)
> - revise_fact: 既存の正典宣言を書き換える (新しい宣言文)
> - add_fact: 新しい正典宣言を追加する
> - none: 自動修正しない (人間の判断に任せる)
>
> 方針: 本文の不整合なら rewrite_scene で契約・正典に矛盾しない全文を
> 書き直す。正典の記述自体の問題なら revise_fact。不足する事実の補完なら
> add_fact。情報不足や作者の判断領域に踏み込む場合は none。

## 修正候補の起票

- fixer の出力を `kind: revision` の変更セット (例: 「修正候補: cs-0001」)
  として `changesets/` に起票する。承認→通常の適用フロー。
- **連鎖防止**: kind: revision の変更セットへのレビューでは再提案しない。
  自動提案は1段で止まる (提案の提案を生まない)。
- 同一シーンへの複数 rewrite は先勝ち — 全文を掛け合わせない。

## review_required の解除

force_override で `review_required` を付けた範囲は、レビューで findings が
解決 (または修正候補が承認・適用) されるまで印を外さず、その範囲の
自律執筆を続けない。
