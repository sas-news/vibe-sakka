---
name: review-change
description: 適用済み変更セット・強制改変・手編集の事後レビュー。影響シーンを整合性・興味/文体・衛生 (manuscript_lint) の3層で検査し、findings を記録して修正候補の変更セット (kind: revision) を起票する。変更セット適用後に必ず実行する。短編では L0/L1 を簡略化する。
---

# review-change — 変更の事後レビュー

変更セット適用・force_override・manual_edit の後に走る。整合性に
加えて「要約体・ビート見出し・感情の名指し・退屈」を検査する。

## いつ使うか

- 変更セット (L1 以上)・強制改変・手編集の直後 (必須)。
- polish で本文を変えた後の確認 (L0 は軽量モードでよい)。

## 入力

- 変更セット (`changesets/cs-NNNN-*.md`) の影響シーン一覧 (最大10シーン)
- 適用後の `canon/facts.md`、各シーンの契約
- `scenes/*.md` の現行本文、`work.md` の面白さの設計

## 手順

1. **対象を集める**: 影響シーン (本文があるもの、最大10)、適用後の正典、
   各契約。short の L0/L1 は影響シーン最大3でよい。
2. **各シーンを3層で検査**:
   - **整合性 (決定的)**: `.agents/skills/write-scene` の「決定的検査」と
     同じ — 禁止/必須/秘密漏洩/仮置き使用/台帳ID混入/言及照合/時系列/
     状態の巻き戻り。
   - **興味・文体 (意味判断)**: 要約体になっていないか / ビート見出し
     (`一` `二` `【】`) がないか / 意図のない感情名指しや説明過多がないか /
     場面に変化と代償 (または `craft/engine.md` に宣言した狙い) があるか /
     退屈・予定調和になっていないか / 作品の声・テンポ・視点・「削らない味」が
     揃っているか (`craft/voice.md` / `craft/engine.md` の宣言は尊重する)。
     違和感は low の finding か notes に書く。
   - **衛生 (決定的)**: `python3 tools/manuscript_lint.py <対象scenes>` を
     実行する。E は high (公開不可)、W は推敲対象として記録。E があれば
     修正候補を立てる。
   - **伏線滞留**: `foreshadowing.md` で回収予定を過ぎた planted や、張設
     シーンを書き換えられた伏線は finding。
   - 契約がないシーンは「契約なし」として正典との矛盾と衛生だけ見る。
3. **findings を記録**: `reviews/<date>-cs-NNNN.md` に
   `[severity] rule: detail — 対象` 形式で書く。
   rule の語彙: contract.forbidden / contract.required_events /
   canon.secret_leak / canon.provisional_use / canon.secret_knowledge /
   pov / time / state / plan / plot_thread / style /
   craft.summary_body (要約体) / craft.beat_heading (ビート見出し) /
   craft.emotion_naming (感情の名指し) / interest.boring (退屈) /
   hygiene.lint (lint E)。
   確信を持てないものは notes に (「問題なし」と断定しない)。
4. **polish 状態を戻す**: rewrite_scene で本文が変わっていたら
   `polished: false` に戻し、`.agents/skills/polish` の再実行が必要な旨を
   結論に書く (release-gate は `polished: true` を要求する)。
5. **報告**: 検査したシーン数・衝突件数・補足件数・lint の E/W 件数を
   作者に伝える。
6. **修正候補 (fixer)** — findings がある場合だけ:

## fixer 役割プロンプト

> あなたは小説作品の「修正案担当」です。レビューで検出された各 finding に
> 対し、修正候補を立ててください。修正は必ず以下のいずれか:
> - rewrite_scene: シーン本文を書き換える (修正後の本文全文。要約体を場面に
>   戻す場合は場面化で書き直す)
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

## 軽量モード (short) の簡略化

- L0 (推敲・誤字・表記): findings 記録は `reviews/polish-*.md` に一本化して
  よい。検査は lint と差分確認のみ。変更セットは作らない。
- L1: 影響シーン最大3を検査。canon 全量の再検査は L2 以上。
- ただし **E (lint) と秘密漏洩は short でも必ず検査する**。

## review_required の解除

force_override で `review_required` を付けた範囲は、レビューで findings が
解決 (または修正候補が承認・適用) されるまで印を外さず、その範囲の
自律執筆を続けない。

## 出力・記録先

- `reviews/<date>-cs-NNNN.md` (`templates/review.md` の形式 + 興味観点)
- 必要なら `changesets/` の kind: revision
- `dialogue.md` にレビュー結果の要約

## アンチパターン

- 整合性だけ見て「問題なし」と報告する (要約体・感情の名指し・退屈を見ない)。
- lint を実行せずにレビューを終える。
- 本文を変えたのに `polished: true` のままにする。
- 指摘の自動修正を連鎖させる (提案の提案)。
- 確信のない検査を「問題なし」と断定する。
