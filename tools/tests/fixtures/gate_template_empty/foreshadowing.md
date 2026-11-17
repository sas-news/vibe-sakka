# foreshadowing.md — 伏線台帳

> 伏線 = 「張った場所・意味・回収予定・期限・状態」の追跡。追加・状態更新は
> 変更セット経由 (ops: add_foreshadow / resolve_foreshadow / retire_foreshadow)。
> レビューで「張りっぱなし」「回収忘れ」を洗い出す。
> **機械可読形式を変えない。** `tools/release_gate.py` は `- (fs…)` 行の
> `期限:` だけを回収期限として読む。
>
> - `期限:` は**回収予定日** (YYYY-MM-DD)。`張設:` の日付とは別物。混同しない。
> - `[planted]` かつ `期限` が今日より前なら gate は error。
> - `[resolved]` / `[abandoned]` は検査対象外。回収済みは期限を残してよい。
> - 期限が未定の `planted` は書かない (未定なら `[仮置き]` にするか、期限を決める)。

<!-- 1行 = 伏線1件 (形式を変えない):
- (fs01) [planted] <何を・どう張ったか> — 張設: <シーン> / 意味: <...> / 回収予定: <第N話 or 未定> / 期限: YYYY-MM-DD / 出所: <対話/本文>
記入例:
- (fs01) [planted] 主人公が櫛を見て一瞬手を止める — 張設: 1-2 / 意味: 姉の形見 / 回収予定: 第3話 / 期限: 2026-12-01 / 出所: 本文
-->

## 状態: planted | partially_resolved | resolved | abandoned

- (fs01) [planted] <何を・どう張ったか> — 張設: <シーン> / 意味: <...> / 回収予定: <第N話 or 未定> / 期限: YYYY-MM-DD / 出所: <対話/本文>
