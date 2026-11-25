---
name: release-gate
description: 公開前チェック。manuscript_lint / release_gate / export --release を実行し、out/ 清浄・リンク0・台帳ID0・推敲記録・外部読者テスト・全話hook/pull を確認する。不合格時は作者に選択肢付きで報告する。「公開したい」「出していいか確認して」「export して」「リリースして」で使う。
---

# release-gate — 公開前ゲート

v1 は「禁止事項 OK / 秘密 OK」だけで出荷可とし、`out/` に企画書・調査・
スクリプトが混ざり、`(了)` が二重のまま公開された。release-gate は
**決定的検査で落とせるものは全部落とし、意味判断は記録で確認する**工程である。
ゲートを通らない原稿を `out/` に出さない。

## いつ使うか

- `polish` の後、`out/` に公開物を書く直前。
- `export` で原稿を書き出す時 (export 自体も内部で lint を走らせる)。
- 「公開していい?」と聞かれた時は、必ずこの手順を実行してから答える。

## 入力

- 作品ディレクトリ (work.md / craft/ / contracts/ / scenes/ / reviews/ / out/)。
- `reviews/polish-*.md` (推敲記録) と `reviews/beta-*.md` (外部読者テスト)。
- `templates/release-checklist.md` (チェック用紙。記入先は
  `reviews/release-checklist-<YYYYMMDD>.md`)。

## 手順

### 1. 前提を確認する

- [ ] 全話の `polish` が終わっている (`reviews/polish-*.md` が1件以上)。
- [ ] `beta-read` が外部コンテキストで実施済みで、interest gate に合格している。
- [ ] `scenes/*.md` のヘッダが `polished: true` になっている。
- [ ] 契約 (`contracts/*.md`) が全シーン分あり `status: approved`。

満たしていない場合は、公開ではなく `polish` / `beta-read` / `write-scene` に
差し戻す。ここで先に進むと、後のゲートで落ちる。

### 2. lint を実行する (決定的検査)

```bash
# 公開物の衛生検査 (E 0 件が必須。W は推敲対象として記録)
python3 tools/manuscript_lint.py --workdir . out/*.md
python3 tools/manuscript_lint.py out/*.txt

# source も検査する。out/ は派生物なので、scenes に E が残っていれば公開不可
python3 tools/manuscript_lint.py --workdir . scenes/*.md

# 機械可読で件数を取る場合
python3 tools/manuscript_lint.py --json --workdir . out/*.md
```

- `E` が1件でもあれば **不合格**。`polish` に戻して直す。
- `W` は出荷可だが、`polish` 記録に対処方針を書く (無視する場合も理由を書く)。
- E の内訳と直し方は `docs/DESIGN.md` §5.1 の表を見る。
  例: E L001 URL残留 / E L003 ビート見出し / E L009 `(了)` 重複 /
  E L007 stale export。
- **公開物は md だけではない。** `out/*.txt` も同じ E 基準で検査する。
  txt と md/scenes の一致 (stale) は `release_gate.py` と
  `export.py --release` が最終確認する。`manuscript_lint.py --workdir` は
  md 用 (txt に付けると本文の見出し差を stale と誤検出する)。
  md だけ直して txt が古いまま、という v1 の失敗はゲートで落とす。
- `--fix` は **source (`scenes/*.md`) に掛ける**。out/ に掛けても次の export で
  戻るうえ、scenes の E は消えない (`.agents/skills/polish/SKILL.md`)。

### 3. 公開ゲートを実行する (状態検査)

```bash
python3 tools/release_gate.py --workdir .
```

検査項目 (`docs/DESIGN.md` §5.3):
- `work.md`: status active / 面白さの設計・禁じ手・声が空でない。
- `craft/engine.md` `craft/voice.md` が存在する。
- 計画上の全シーンに approved 契約がある。
- `scenes/*.md` が存在し `polished: true`。**scenes の lint も E 0 件。**
- 伏線台帳に回収期限超過がない (`期限: YYYY-MM-DD` の書式)。
- **`reviews/beta-*.md` が1件以上**あり、`context: external` と
  `interest_gate: pass` が記入され、スコアカード10観点に点数と引用がある。
  外部化されていない自己採点 (`context: self`) は合格に数えない。
- **`reviews/polish-*.md` が1件以上**あり、`before_chars` / `after_chars` が
  正の整数、`cut_rate` が 0.0–1.0、`editor` と `date` が記入されている。
  空ファイルやテンプレートの記入例残りは不合格。
- `out/` が公開物のみ。**`out/*.txt` も lint E 0 件**で md と一致する。
- lint が E 0 件。

不合格なら exit 1。レポートは `reviews/release-<YYYYMMDD>.md` に書かれる。
このファイルは gate の自動生成で、実行のたびに上書きされる。手動チェックの
記録は `reviews/release-checklist-<YYYYMMDD>.md` に別ファイルで残す。

### 4. export を実行する (公開物の生成)

```bash
# まず通常 export で原稿を確認
python3 tools/export.py --workdir .

# 公開用: 状態検査 + out/ 清浄 + lint を通してから書き出す
python3 tools/export.py --workdir . --release --md --txt
```

- `--release` は生成物を `build/staging/` に作り、`tools/release_gate.py` を
  通ってから `out/` を置き換える。**不合格なら `out/` は一切変更しない**
  (前回公開した良い版を壊さない)。
- ゲートは lint・契約・推敲・beta/polish の中身・out/ 清浄まで見る。
  1つでも落ちれば書き出さずに exit 1。
- `out/` に書いてよいのは `<title>.md` / `.txt` / `.epub` のみ。
  企画書・調査ノート・スクリプト・下書き・画像を置かない。
- `--no-lint` は使わない (検査を飛ばすため)。

### 5. 意味判断を記録で確認する (自動化できない項目)

機械的な厳格ゲートは衛生・工程面 (`manuscript_lint.py` / `release_gate.py`) に寄せ、
表現面は `craft/engine.md` / `craft/voice.md` に宣言された狙い (意図的な逸脱を
含む) を尊重する。以下は `templates/release-checklist.md` で1話ずつ確認し、
`reviews/release-checklist-<YYYYMMDD>.md` に記録する (自動レポート
`reviews/release-<YYYYMMDD>.md` とは別ファイル。gate はそちらを上書きするが、
手動チェックリストには触れない)。

- [ ] **全話 hook/pull**: 各話の冒頭3行に問いがあり、章末に未解決の引きがある
      (`craft/engine.md` / `craft/voice.md` に静かな余韻等の意図的な逸脱を
      宣言している場合は、その狙いが機能しているか確認する)。
- [ ] **外部読者テスト**: 全話 (または設定した単位) で `beta-read` 済み。
      `reviews/beta-*.md` に `context: external` と `interest_gate: pass` が
      あり、`templates/interest-scorecard.md` の判定が high 1 / medium 3 未満。
      **同一コンテキストの自己採点はテストとして数えない。**
- [ ] **out/ 清浄**: リンク0 / URL0 / 出典0 / 台帳ID0 / 制作メモ0。
- [ ] **引用ファイアウォール**: `research/` の原文・数値・出典が本文に
      コピーされていない。出典は `research/` にだけ残る。
- [ ] **献本・権利表記など**: 必要な帰属表示がある (任意)。

### 6. 最終確認

```bash
# 5つのコマンドがすべて成功することを確認
python3 tools/manuscript_lint.py --workdir . scenes/*.md && \
python3 tools/manuscript_lint.py --workdir . out/*.md && \
python3 tools/manuscript_lint.py out/*.txt && \
python3 tools/release_gate.py --workdir . && \
python3 tools/export.py --workdir . --release --md --txt
```

- 成功: 作者に「公開可」と、生成物・記録のパスを報告する。
- 失敗: 次の §7 に従って報告する。**ゲートを通さず公開しない。**

## 不合格時の作者への報告の仕方

ルール: 1メッセージ1問。**生のファイル編集をさせない。** 選択肢で聞く。
「何が落ちたか」「なぜ公開できないか」「どう直すかの選択肢」を自然言語で。

```text
公開ゲートで2件止まりました。公開はまだできません。

1) out/ に企画書 (browser-wars_企画書_v2.md) が残っています
   → (A) build/ へ移す (B) 削除する (C) 公開物として別名で残す
2) 第3話にビート見出し (「一」「二」) が3箇所あります
   → (A) 場面化して書き直す (推奨・30分) (B) 見出しだけ削る (内容は要約のまま)

まず1) はどれにしますか。
```

報告に含めるもの:
- 落ちた検査の名前と件数 (コマンドの出力を貼る)。
- 各件の「意味」(読者に何が起きるか)。例: 「ビート見出しは要約体の印で、
  読者が小説ではなくあらすじを読むことになります」。
- 選択肢と推奨。所要時間の目安。
- 直した後に再実行するコマンド。

- ○ 「第2話の push が弱いです。章末が総括で終わっていて、次を読む理由が
  ありません。(A) 新情報を1つ足す (B) 選択を残して切る」
- × 「第2話が不合格です。直してください。」(何をどう直すかがない)

## 出力・記録先

| 出力 | パス |
| --- | --- |
| 公開レポート (gate が生成・毎回上書き) | `reviews/release-<YYYYMMDD>.md` |
| export レポート | `build/export-report.md` |
| 公開物 | `out/<title>.md` / `.txt` / `.epub` |
| チェック用紙 (手動記入。gate は触らない) | `reviews/release-checklist-<YYYYMMDD>.md` |

## アンチパターン

- **gate を飛ばして公開**: exit 1 を無視する。公開物の信頼を一度で失う。
- **`--no-lint` / `--legacy` の常用**: 検査を飛ばすためのフラグを通常運用で
  使わない。`--legacy` は v1 作品の移行時のみ。
- **out/ に作業物を置く**: 企画書・調査・スクリプト・下書きを out/ に置かない。
- **整合性だけで「面白い」と報告**: gate 合格は「破綻していない」であって
  「面白い」ではない。面白さは `beta-read` のスコアカードで判定する。
- **自己採点で外部読者テストを代用**: 同一コンテキストの採点は無効。
- **scenes を lint せず out だけ直す**: out は派生物。source の E は消えない。
- **不合格を隠して「ほぼ完成」と報告**: 落ちた検査・件数・影響を必ず伝える。
- **作者にファイルを直させる**: 選択肢と自然言語で聞く (AGENTS.md 対話の振る舞い)。

## 関連

- `docs/DESIGN.md` §5 (tools 仕様) / §9 (受入条件)
- `templates/release-checklist.md` — チェック用紙
- `.agents/skills/polish/SKILL.md` — 前工程 (推敲記録)
- `.agents/skills/beta-read/SKILL.md` — 興味監査 (interest gate)
- `.agents/skills/export/SKILL.md` — export の手順
- `tools/manuscript_lint.py` / `tools/release_gate.py` / `tools/export.py`
