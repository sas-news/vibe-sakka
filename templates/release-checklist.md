# reviews/release-<YYYYMMDD>.md — 公開前チェックリスト

> `release-gate` で使う手動チェック用紙。記入して
> `reviews/release-<YYYYMMDD>.md` に保存する (gate が自動生成するレポートに
> 追記してよい)。**チェックのない公開はしない。**
> 決定的検査はコマンドに任せ、ここでは「意味判断」と「確認漏れ」を防ぐ。

```yaml
date: 2026-11-17
work: "<作品タイトル>"
version: v1.0.0
releaser: ai
```

## 0. 前提

- [ ] 全話に `polish` を通した (`reviews/polish-*.md` が1件以上)。
- [ ] `beta-read` を外部コンテキストで実施した (`reviews/beta-*.md`)。
- [ ] interest gate 合格 (high 0 / medium 2以下)。
- [ ] 全シーンの契約が `status: approved`。
- [ ] `scenes/*.md` のヘッダが `polished: true`。

## 1. 決定的検査 (コマンド)

```bash
python3 tools/manuscript_lint.py --workdir . out/*.md
python3 tools/release_gate.py --workdir .
python3 tools/export.py --workdir . --release --md --txt
```

- [ ] lint: E 0件 / W 記入例: 2件 (W001 感情語)
- [ ] release_gate: exit 0
- [ ] export --release: exit 0、`out/` は `.md` `.txt` `.epub` のみ
- [ ] 3コマンドを**同じ原稿**に対して実行した (途中で本文を変えていない)。

## 2. 公開物 (out/) の清浄

- [ ] out/ に企画書・調査ノート・スクリプト・下書き・画像がない。
- [ ] 本文に URL / Markdownリンク / 出典 / `research/` 参照がない。
- [ ] 本文に台帳ID (`f001` `ev01` `1-2` 等)・ファイル名・制作メモがない。
- [ ] 本文にビート見出し (`一` `二` `【…】`) がない。
- [ ] 末尾・章末の `(了)` 重複・区切り記号の混在がない。

記入例: 「out/ は sample.md / sample.txt の2ファイル。リンク0、ID0。」

## 3. 全話の意味判断

1話ずつ確認する。hook/pull は引用で示す (自己申告にしない)。

| 話 | 冒頭フック (引用) | 章末の引き (引用) | interest gate | 備考 |
| --- | --- | --- | --- | --- |
| 第1話 | 記入例: 「忘れ物預かり所は、駅の西口に、昨日からあった。」 | 記入例: 「まだ書かれていない日付があった。」 | pass | — |
| 第2話 | | | | |

- [ ] 全話に hook がある (冒頭3行で問いが立つ)。
- [ ] 全話に pull がある (未解決・具体・次を読む理由)。

## 4. 引用ファイアウォール

- [ ] `research/` の URL・出典・原文・数値が本文にコピーされていない。
- [ ] 事実を使った箇所は創作として言い換えられている。
- [ ] 出典は `research/` にだけ残っている。

記入例: 「調査ノートの3件のURLは本文になし。年号のみ創作として使用。」

## 5. 最終

- [ ] タイトル・著者名・版表記が正しい。
- [ ] `work.md` の status が active、`canon_revision` が現行。
- [ ] 公開レポート (`reviews/release-<date>.md`) にこの記録を統合した。
- [ ] 作者に「公開可」と生成物パスを報告した。

## 不合格時の報告

1メッセージ1問。選択肢つきで、生のファイル編集をさせない
(`.agents/skills/release-gate/SKILL.md` §7)。報告に含めるもの:
落ちた検査・件数・読者への影響・選択肢・再実行コマンド。

記入例:
```text
公開ゲートで1件止まりました。out/ に企画書が残っています。
(A) build/ へ移す (B) 削除する — どちらにしますか。
```

## 記入例 (完成したチェックの1行)

`- [x] lint: E 0件 / W 2件 (W001 感情語) — 2026-11-17 14:02 実行`
