# reviews/<date>-<target>.md — レビュー記録

> 変更セット適用後・強制改変後に、影響範囲のシーン本文と現行正典を
> 検査した記録。

```yaml
target: cs-0001          # レビュー対象 (変更セット/シーン)
date: 2026-01-01
scenes_reviewed: 0
```

## findings

<!-- 形式 (1行1件):
- [high] <rule>: <detail> — 対象: scene 1-2 / f003
  severity: high=必須イベント欠落・禁止違反・正典と明確に矛盾
            medium=契約の意図から外れるが致命傷ではない
            low=些細な違和感 / info=参考情報 (notes 欄でもよい)
  rule: contract.forbidden / contract.required_events / canon.secret_leak /
        canon.provisional_use / canon.secret_knowledge / pov / time / state /
        plan / plot_thread / style
-->

## notes

<確信を持てない検査結果・判断保留した事項 —「問題なし」と断定しない>

## 修正候補

<findings から導いた修正案。fixer 手順: 各 finding に rewrite_scene /
revise_fact / add_fact / none (人間判断) のいずれかを割り当て、
kind: revision の変更セットとして起票する。修正の変更セットへのレビューで
再提案はしない (1段で停止)>

## 結論

- <解決/未解決>、review_required 範囲の扱い
