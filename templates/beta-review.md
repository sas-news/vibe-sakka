# reviews/beta-<対象>-<date>.md — 初読者通読と興味監査

> 新規コンテキストで、正典・計画を持たない読者として読んだ記録。
> severity は「読者離脱度」(実読者が本を閉じるか) で較正する。
> スコアカードの観点定義は `templates/interest-scorecard.md`。
> `context` と `interest_gate` は**記入必須**。空のままでは release-gate が
> 不合格にする。`context: external` の根拠 (原稿のみを渡した) を本文中に1行残す。

```yaml
target: <話・範囲>
date: <YYYY-MM-DD>
manuscript: <export原稿へのパス>
context: ""            # 記入必須: external=新規コンテキスト / self=本文のみ再読 (self は合格に数えない)
scenes_reviewed: 0
interest_gate: ""      # 記入必須: pass | fail (high 1 or medium 3 で fail)
```

## 興味スコアカード (必須)

`templates/interest-scorecard.md` の10観点を 0–4 で採点し、根拠を本文の
具体 (行・台詞・描写) で書く。観点名は scorecard の定義をそのまま使う
(独自の観点を足すのは可、減らすのは不可)。スコアだけ書かない。

- 0–1点 = high / 2点 = medium / 3–4点 = 問題なしに換算する。
- **high 1件以上 or medium 3件以上で不合格。** 合計・平均は参考値。
- 引用できない観点は 0点。迷ったら低い方につける。
- 採点は**このファイルに記録する** (別ファイルに分けない。
  `reviews/interest-*.md` は作らない)。このファイルが判定の正本。

| # | 観点 | 点 (0–4) | 根拠 (本文の具体) |
| --- | --- | --- | --- |
| 1 | <観点名> | | |
| 2 | <観点名> | | |
| 3 | <観点名> | | |
| 4 | <観点名> | | |
| 5 | <観点名> | | |
| 6 | <観点名> | | |
| 7 | <観点名> | | |
| 8 | <観点名> | | |
| 9 | <観点名> | | |
| 10 | <観点名> | | |
| 合計 | | /40 | |

記入例: `1 | 冒頭フック | 3 | 「忘れ物預かり所は、駅の西口に、昨日からあった。」`

## 読者は次を読む理由

- どこで読むのをやめたか (行番号・話):
- 次のページを読む理由 (残った問い・気になる人物・回収されそうな約束):
- 記憶に残った具体物 (物・動作・台詞):
- 予想を裏切られた箇所 (意外と納得):
- 感情が動いた箇所 (どう動いたか。感情語の有無ではなく):
- 退屈した箇所 (どこからどこまで、何が足りないか):
- 既視感 (「どこかで読んだ」装置・人物・結末。なければ「なし」):

## findings

<!-- 1行1件:
- [high] <rule>: <detail> — 対象: scene 1-2

severity: high=読者が閉じる / medium=読み飛ばす / low=違和 / info=参考

rule: confusion / prerequisite / over-explain / tempo / emotion /
      hook / entertainment / repetition / formula / vocabulary /
      boring (退屈) / summary_body (要約体)
-->

## notes

<確信を持てないもの・判断保留した事項 — 「問題なし」と断定しない>

## 修正候補

<各 finding に rewrite_scene / polish / revise_fact / none を割り当て、
必要なら kind: revision の変更セットとして起票>

## 結論

- 閾値判定: <high 1件 or medium 3件以上 → 再生成発火・自律停止>
- 次工程: <polish へ (未推敲) / write-scene の興味 revise へ / release-gate へ>
