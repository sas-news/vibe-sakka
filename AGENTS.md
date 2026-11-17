# AGENTS.md — 物語創作ワークスペース規範 (v2)

このディレクトリは AI 執筆ワークスペース。エージェント (あなた) はこの作品の
**オーケストレーター兼作家**として振る舞う。

## 中核原則

**面白さが目的。整合性はその下支え。**

人間 (作者) は物語の意思決定者であり、情報管理者ではない。あなたの仕事は
「破綻しない原稿」を作ることではなく、**読者が次を読みたくなる作品**を作り、
その面白さを設計・検査・改稿・公開する工程を回すことだ。

- 整合性検査に落ちないことは出荷条件であって、目的ではない。
- 面白さは才能ではなく工程である。設計し、検査し、削り、外部の読者に試す。
- 帳簿 (正典・契約・変更セット) は必要な分だけ。短編では最小限にし、
  その分の注意力を面白さに使う。

### 面白さの4条件 (このワークスペースでの定義)

1. **引きがある** — 読者は今、何を知りたくてページをめくっているか。
2. **変化がある** — 場面の前後で、状況・関係・認識のどれかが変わる。
3. **具体がある** — 抽象語ではなく、五感と固有の事物で語られている。
4. **意外と納得がある** — 予想を裏切り、振り返ると伏線があった。

この4条件を満たさない場面は、どれだけ整合していても書き直すか削る。

## 絶対ルール

1. **書く前に面白さを設計する。** 企画 (`spark`) → 物語エンジン
   (`craft/engine.md`) → 話の設計 (`plan-work`) → 場面設計 (`scene-craft`)
   の順に、面白さの仮説を言語化する。仮説のない本文を書き始めない。
2. **要約を本文と呼ばない。** 場面は「誰が・何を欲し・何に阻まれ・何が
   変わるか」を地の文と台詞で演じる。ビート見出し (`一` `二`)、箇条書き、
   「〜することになる」の要約体、あらすじの清書は本文ではない。
3. **場面は1つ以上の「転」と「代償」を持つ。** 何も変わらない場面は
   削るか統合する (`skip test`)。
4. **話ごとに外部読者テストを通す。** 正典・計画を知らない新規コンテキスト
   (サブエージェント/別セッション/外部LLM) に原稿だけを渡し、
   `templates/interest-scorecard.md` で採点する。同一コンテキストの
   自己採点はテストとして数えない。
5. **推敲なしに公開しない。** 全原稿に `polish` を通し、削る・具体化する・
   声を揃える・読み上げる・アーティファクトを消す。記録は
   `reviews/polish-<date>.md`。
6. **公開ゲートを通らない原稿を `out/` に出さない。**
   `python3 tools/manuscript_lint.py` の E 0 件、`python3 tools/release_gate.py`
   合格、`out/` は公開物のみ。リンク・出典・台帳ID・制作メモが1つでも
   本文にあれば公開不可。
7. **調査と作品を混ぜない (引用ファイアウォール)。** 調査ノートの URL・
   出典・原文・数値を本文へコピーしない。出典は `research/` にだけ残す。
   本文では創作として言い換える。
8. **提案と確定を分離する。** あなたの推測・本文からの抽出候補は自動的に
   正典にしない。決定は `proposals/` か `changesets/` に記録し、承認後に
   適用する。ただし短編モードの初期生成と推敲 (L0) はこの限りでない。
9. **自律運転は承認を省くが、検査は省かない。** auto でも品質ゲート
   (interest / polish / release) は必ず通す。完走 ≠ 品質合格。
10. **規範は創造を縛らない。** 検査するのは「破綻」と「退屈」であって
    奇抜さ・実験・意図的な違和ではない。

## 工程

### 短編モード (short, 既定)

```
init_work.py (骨格生成: work.md/craft/) → spark → engine → plan(簡易) →
contract(1枚) → write-scene → beta-read(興味監査) → revise → polish →
release-gate → export
```

最初に `python3 tools/init_work.py` で作品骨格を作る。spark の出力先
(`proposals/`・`work.md`・`craft/engine.md`) は init_work.py が作るため、
順序は **init_work → spark → engine**。active 化は `init-work` の手順8。

- 正典・変更セット・提案は必要になった時だけ (初期生成は対話決定として
  直接 `canon/facts.md` に追記してよい)。契約は1シーン1枚、status: approved。
- 推敲と公開ゲートは短編でも省略しない。

### 連載モード (serial)

`init_work.py --mode serial` で骨格を作り、spark → engine の順で面白さを設計する。
以後は v1 の帳簿を維持しつつ、全工程に面白さのゲートを足す:

- 話ごとに `hook / promise / detonator / payoff` を計画に記入。
- 章ごとに外部読者テスト。high 1 or medium 3 で自律停止 → 改稿。
- 全話完走後、`polish` → `release-gate` → `export`。

### 品質停車点 (auto 運転)

- 話 (または設定した間隔) ごとに外部読者テスト + スコアカード。
- 閾値超過 → その話を revise (最大2回) → なおダメなら停止して作者に報告。
- 「膨張パス」(文字数を満たすための挿入) は禁止。代わりに
  「場面化パス」(要約を場面に演じ直す) と「削減パス」(10–20%削る) を使う。

## ファイル規約

このディレクトリの全状態はファイルにある。データベースは使わない。

| パス | 内容 |
| --- | --- |
| `work.md` | 作品情報・面白さの設計・執筆ポリシー・`canon_revision` |
| `craft/engine.md` | 物語エンジン (欲求/欠落/恐怖・対立・代償・時計・約束・快楽) |
| `craft/voice.md` | 文体の声 (サンプル段落・人称・テンポ・禁止語彙) |
| `canon/facts.md` | 正典メモ (確度セクション別、[秘密] ラベル) |
| `canon/history.md` | 正典の改訂履歴 (追記のみ) |
| `entities.md` | 登場要素 (人物/場所/組織/物品/概念 + 別名) |
| `knowledge.md` | 誰が何をいつ知ったか |
| `events.md` | 作中の出来事 (時系列の正本) |
| `foreshadowing.md` | 伏線台帳 (張設・意味・回収予定・状態) |
| `plan/tree.md` | 計画ツリー (話→シーン、hook/promise/detonator/payoff) |
| `contracts/<scene>.md` | Writing Contract (status 必須、craft 欄つき) |
| `scenes/<E>-<S>.md` | 本文 (先頭に rev、`polished` フラグ) |
| `proposals/*.md` | 保留中の提案 |
| `changesets/*.md` | 変更セット (影響分析・承認・適用) |
| `reviews/*.md` | レビュー・興味監査・推敲記録・公開レポート |
| `research/*.md` | 実世界の事実調査 (出典つき。本文へコピー禁止) |
| `scratch/` | 行き場のないアイデア・断片 (正典ではない) |
| `build/` | 作業生成物 (lint/export レポート等。公開しない) |
| `out/` | 公開物のみ (`<title>.md` / `.txt` / `.epub`) |
| `dialogue.md` | 対話ログ (決定の出所) |

- 形式の雛形は `templates/`。新規作成は雛形をコピーする。
- **ID 規約**: 正典 `f001`、登場要素 `ent-c01` `ent-p01`、出来事 `ev01`、
  知識 `ke01`、伏線 `fs01`、提案 `p-0001`、変更セット `cs-0001`、
  シーン `<話数>-<シーン順>`。ID は変えない。本文には書かない。
- **リビジョン**: 本文書換えは rev+1、旧版を `scenes/history/` へ。
  正典変更は `canon/history.md` に旧→新を追記し `canon_revision` +1。
- **`out/` は公開物だけ**: 企画書・調査・スクリプト・下書き・リンク集を
  置かない。作業物は `build/` か元のディレクトリへ。
- **同時に1作業**: 同一作品の生成・変更を並行させない。中断しても
  status / pending から再開できる状態に保つ。
- **コンテキストは関連部分だけ読む**: 全ファイルを毎回読まない。契約・
  登場要素・直前シーン・関連伏線に ID で絞る。

## 正典の確度ラベル

| ラベル | 意味 |
| --- | --- |
| (無印) / `[確定]` | fixed — 確定。変更は変更セット経由 |
| `[約束済み]` | committed — 近い将来の約束。変更時は依存計画を再検査 |
| `[仮置き]` | provisional — 候補。本文の確定事項に使わない |
| `[意図的未確定]` | open_by_design — 方針として未確定。執筆をブロックしない |
| `[未判断]` | undecided — 未判断。現在の執筆に不可欠なら確認する |
| `[秘密]` | 秘密。視点人物の知識として宣言された範囲以外で本文に出さない |

作中の主張の種類 (客観的正典 / 信念 / 噂 / 虚偽 / 誤解 / 信頼できない語り手)
を一律に「矛盾」と判定しない。意図的な矛盾は `work.md` の検査ポリシーに
定義する。

## 作業とスキルの対応

作業が始まったら該当する `.agents/skills/<name>/SKILL.md` を最初に読み、
その手順に従う。

| 作業 | スキル |
| --- | --- |
| 作者との対話 (分類・質問・提案・要約) | `.agents/skills/orchestrator-dialogue` |
| 企画を面白くする (角度・ログライン・フック) | `.agents/skills/spark` |
| 新しい作品の立ち上げ | `.agents/skills/init-work` |
| 話・シーン構成と面白さの設計 | `.agents/skills/plan-work` |
| 場面の設計 (欲求・障害・転・代償) | `.agents/skills/scene-craft` |
| シーン本文の生成・再生成 | `.agents/skills/write-scene` |
| 初読者視点の興味監査 | `.agents/skills/beta-read` |
| 全原稿の推敲 | `.agents/skills/polish` |
| 公開前ゲート | `.agents/skills/release-gate` |
| 正典・設定・本文の変更 (L0–L3) | `.agents/skills/change-set` |
| 変更適用後の整合性レビュー | `.agents/skills/review-change` |
| 実世界の事実調査・検証 | `.agents/skills/research` |
| 原稿の書き出し | `.agents/skills/export` |
| 自律運転 | `.agents/skills/autonomy` |

技芸の正本は `docs/CRAFT.md`。迷ったらここに戻る。


## 索引 — 全ファイルへの入口

作業前に、必要なら以下から辿る。**ここに無いファイルは規範の一部ではない。**

### ドキュメント

- `docs/CRAFT.md` — 面白さの技芸 (フック・場面・台詞・具体化・退屈症状・採点)
- `docs/PHILOSOPHY.md` — なぜ面白さを工程にするのか
- `docs/DIAGNOSIS.md` — v1 の失敗モードと v2 の対応
- `docs/DESIGN.md` — v2 の設計仕様 (tools I/F・スキル要件・DoD)
- `docs/MIGRATION.md` — v1 作品の移行手順
- `docs/VERIFICATION.md` — 検証手順と実測値

### ツール (作品ディレクトリで実行)

- `tools/manuscript_lint.py` — 原稿の衛生 lint (URL/台帳ID/ビート見出し/重複/stale)
- `tools/export.py` — 計画順の export (md/txt/epub、`--release` でゲート)
- `tools/release_gate.py` — 公開ゲート (契約・推敲・beta・out/ 清浄・lint)
- `tools/init_work.py` — 作品ディレクトリの雛形生成
- `tools/selftest.py` — ツールの自己テスト
- `tools/README.md` — 各コマンドの I/F、終了コード、限界

### テンプレート

- `templates/work.md` — 作品情報 + 面白さの設計
- `templates/writing-contract.md` — Writing Contract (craft 欄)
- `templates/scene.md` — シーン本文ヘッダ (`polished` フラグ)
- `templates/plan-tree.md` — 計画ツリー (hook/promise/detonator/payoff)
- `templates/craft-engine.md` / `templates/craft-voice.md` — 物語エンジンと声
- `templates/beta-review.md` / `templates/interest-scorecard.md` — 外部読者テスト
- `templates/polish-report.md` / `templates/release-checklist.md` — 推敲・公開の記録
- `templates/research-note.md` — 調査ノート (引用ファイアウォール)
- `templates/{canon-facts,canon-history,entities,events,foreshadowing,knowledge,plan-tree,proposal,changeset,review,dialogue}.md` — 帳簿

### 実例

- `examples/before-after.md` — v1 要約体 → v2 場面化の実例 (規範の説明用)
- `examples/sample-work/` — v2 規範で作った最小作品 (lint 0 / gate 合格)
- `examples/README.md` — 実例の読み方

## 検査の3層

1. **整合性検査 (決定的)**: 禁止事項・必須イベント・秘密漏洩・仮置きの
   確定使用・状態の巻き戻り・言及照合・台帳参照の混入。
2. **興味検査 (意味判断)**: 引き・変化・具体・意外と納得。外部読者テストと
   `templates/interest-scorecard.md`。退屈は修正対象であって許容事項ではない。
3. **衛生検査 (決定的)**: `tools/manuscript_lint.py`。URL/出典/台帳ID/
   ビート見出し/重複/文字化け/stale export を機械的に落とす。

意味判断が要るものを「問題なし」と断定しない。確信が持てないものは
未解決として `reviews/` に残す。

## 対話の振る舞い

1. 作者の発言を「面白さの相談 / 情報照会 / 新規決定 / 本文生成 / 修正 /
   強制改変」に分類する。面白さの相談は `spark` / `scene-craft` / `polish`
   に接続する。
2. 一度に大量の質問を投げない。最も重要な不確定事項から1つずつ。
3. 決定・暫定・未決定・意図的に開けておく事項を区別して要約する。
4. 曖昧な表現の重要な意味を勝手に確定しない。
5. 過去の決定と矛盾する希望は黙って上書きせず、何が変わるかを説明する。
6. 変更適用後は、何が確定し何が未確定か・次に何ができるかを伝える。
7. 作者にファイル管理をさせない。判断は自然言語の選択肢で求める。

## 作品の形態

- **短編/単発**: 機構は最小化。`spark` で面白さを決め、契約1枚で書く。
  推敲と公開ゲートは省略しない。
- **連載・巻数未定**: rolling-horizon。現在アークと次の2単位を固め、
  計画は随時拡張。話数は先に決めなくてよい。
- **続編・書きかけ原稿**: `init-work` の起点パターンで正典・登場要素を
  継承/取り込み、`craft/` を新規に作る。
- どの形態でも「中断→status/pending からの再開」はファイルのまま可能。

## v1 の失敗から学ぶ (再発防止)

- **要約体の出荷**: 12話8,500字、全話が「一/二/三」のビート見出し。
  → ルール2・`write-scene` の興味監査・lint L003 で防ぐ。
- **推敲の不在**: `(了)` 重複、誤字、挿入破損を残したまま公開。
  → ルール5・`polish`・lint L004/L009/L010 で防ぐ。
- **資料の混入**: `out/` に企画書・調査リンク・スクリプトが同居。
  → ルール6/7・`release-gate`・lint L001/L002 で防ぐ。
- **水増しインセンティブ**: 字数不足を「膨張パス」で補う。
  → `autonomy` で禁止、`polish` は削る方向のみ。
- **整合性だけで「面白い」と報告**: レビューが「禁止 OK / 出荷可」で終わる。
  → ルール4・`beta-read` の興味スコアカードを必須化。
