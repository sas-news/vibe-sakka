# vibe-sakka v2 — 設計仕様 (DESIGN)

> この文書は v2 改修の唯一の正本仕様。実装者はまずこれを読み、担当スコープの
> 「要件」と「受入条件」に従う。仕様と矛盾する実装をしない。迷ったら仕様が優先。
> 文書は日本語。コード内の識別子・コメントは英語可。外部依存は追加しない。

---

## 0. なぜ改修するのか (v1 の失敗)

v1 は「破綻しない作品」を作る装置としては動く。しかし **「面白い作品」を作る装置では
ない**。整合性の帳簿 (canon / contracts / changesets) が品質のすべてを占め、
面白さを **設計し・検査し・改稿し・公開する工程が存在しない**。

実作品2本を分析して確認された失敗:

1. **要約が本文として出荷された。** 12話の「小説」が全編8,500字、1話あたり
   700字で、「一 / 二 / 三 / 四」というビート見出し付きのあらすじだった。
   契約は「必須イベント」を満たすことだけを要求し、writer プロンプトには
   「面白く書け」が一行もなかった。審査 (`review-01`) は
   「禁止事項 OK / 秘密 OK」とだけ記録し、出荷可とした。
2. **推敲が工程にない。** 原稿は `(了)` の二重、区切りの不統一、誤字
   («場所だかなら»)、挿入パスによる台詞破損などを残したまま公開された。
   検査は「正典との矛盾」しか見ず、文章そのものを読む工程がなかった。
3. **資料と作品の境界がない。** `out/` に企画書・調査リンク・生成スクリプトが
   作品と同居し、「公開物」と「作業物」の区別がなかった。`research/` の
   出典URLが最終成果物に混ざる経路が塞がれていない。
4. **分量インセンティブが逆。** 「字数目安に不足」への対処が「膨張パス」
   (挿入で水増し) だった。削る工程・場面化する工程は存在しなかった。
5. **外部読者テストが最後の任意工程。** 章ごとの強制ではなく、閾値は
   「読者が閉じるか」だけで、退屈 (読み飛ばす) を修正に回す回路が弱い。
6. **帳簿が重すぎる。** 短編でも proposal / contract / changeset / review /
   events / knowledge の同期を要求し、モデルの注意を整合性に使い切る。
   面白さに使うはずの注意力が、管理作業に食われている。

**v2 の中心命題: 面白さを工程にする。整合性はその下支えに降ろす。**

---

## 1. 設計原則

1. **面白さが目的、整合性は手段。** 整合性検査に落ちないことは出荷条件であって
   目的ではない。どの工程も「読者は次を読みたくなるか」に答える責任を持つ。
2. **書く前に面白さを設計する。** 企画 (`spark`) → 物語エンジン (`craft/engine.md`)
   → 話の設計 (hook / promise / escalation / payoff) → 場面設計 (scene-craft) の
   順に、面白さの仮説を言語化してから本文に入る。
3. **要約を本文と呼ばない。** 場面は「誰が・何を欲し・何に阻まれ・何が変わるか」
   を、地の文と台詞で演じる。ビート見出し・箇条書き・「〜することになる」の
   要約体は自動失格。
4. **推敲は必須工程。** 全原稿に対して削る・具体化する・声を揃える・読み上げる
   パスを必ず1回以上通す。推敲記録 (`reviews/polish-*.md`) のない原稿は出荷しない。
5. **公開物と作業物を分ける。** `out/` は公開物のみ。企画書・調査・スクリプト・
   中間原稿は `plan/` `research/` `build/` に置く。`out/` にURL・出典・台帳ID・
   メタ情報が1つでもあれば公開ゲートで落とす。
6. **決定論で捕まえられるものは決定論で捕まえる。** 参照リンク残留・台帳ID混入・
   ビート見出し・重複・文字化け・古いexport は `tools/` の lint が担当。
   意味判断 (退屈・感情の動き・意外性) は外部読者テストが担当。
7. **軽量モードを既定にする。** 短編・単発は「spark → 契約1枚 → 執筆 →
   興味監査 → 推敲 → 公開ゲート」。正典・変更セットは必要になった時だけ。
   連載・長編のみ full モードで v1 の帳簿を維持する。
8. **自律運転でも品質ゲートは飛ばさない。** auto は「承認を省く」だけであって
   「検査を省く」ではない。完走 ≠ 品質合格。
9. **規範は創造を縛らない (厳格ゲートは衛生面へ、表現面は強力なデフォルトへ)。**
   冒頭3段落の型・感情名指し回避・転と代償などの表現規範は迷ったときの強力な
   デフォルトとし、`craft/engine.md` や `craft/voice.md` で狙いを宣言すれば
   意図的に外してよい。検査するのは「破綻」と「退屈」であって、奇抜さ・過剰さ・
   実験・意図的な違和ではない。
10. **ハーネス非依存。** ファイルと Python 3 標準ライブラリだけで動く。
    サブエージェントが使えない環境では、別セッション/外部LLMへの貼り付けで
    外部読者テストを代替できる。

---

## 2. 全体像

```
[作者のノリ]
   │
   ▼
(1) spark ……… 企画を面白くする。5案 → 角度 → ログライン → フック草案
   │            craft/engine.md に「面白さの源泉・約束・欲求・対立・代償・時計・快楽」を書く
   ▼
(2) plan-work … 話ごとに hook / promise / detonator / payoff を必須記入
   │            (あらすじの時点で面白くなければ本文にしない)
   ▼
(3) scene-craft + contract … 場面の欲求・障害・転・代償・入/出・スキップテスト
   │            (淡々としそうなときの打開策カタログは任意選択)
   ▼
(4) write-scene … 場面として書く。要約禁止。声・具体・台詞・五感。
   │            決定的検査 (整合性) + critic (整合性) + セルフ興味監査
   ▼
(5) beta-read (章ごと・新規コンテキスト) … 興味スコアカード+診断用の問いで外部評価
   │            閾値超過 → revise (最大2回) → なおダメなら作者に報告
   ▼
(6) polish (全原稿) … ノイズを削り味を残す / 具体化 / 声を揃える / 読み上げ
   │            / 残存アーティファクト除去。reviews/polish-*.md を残す
   ▼
(7) release-gate + export … lint 0 error / gate 合格 / out/ を公開物のみに
   │            → out/<title>.md / .txt / .epub
   ▼
[読者]
```

v1 との差分: (1)(3 craft)(5 強制)(6 新規)(7 新規)。帳簿は full モードのみ。

---

## 3. ファイル構成 (キット)

```
AGENTS.md                     規範 (Lead 執筆)
README.md                     入口 (Lead 執筆)
CHANGELOG.md                  変更履歴 (Lead)
.gitignore                    __pycache__ / build / *.pyc
docs/
  DESIGN.md                   本仕様
  DIAGNOSIS.md                v1 失敗の証拠と v2 の対応表
  PHILOSOPHY.md               v2 の思想 (面白さ=工程)
  CRAFT.md                    クラフト規範 (技芸の正本)
  MIGRATION.md                v1 作品の移行手順
  VERIFICATION.md             検証手順と実測値
.agents/skills/
  orchestrator-dialogue/      既存 改稿
  init-work/                  既存 改稿 (craft ヒアリング+軽量モード)
  spark/                      新規
  plan-work/                  既存 改稿
  scene-craft/                新規
  write-scene/                既存 改稿
  beta-read/                  既存 改稿 (興味監査を必須化)
  polish/                     新規
  release-gate/               新規
  export/                     既存 改稿 (tools/export.py 経由を必須化)
  research/                   既存 改稿 (引用ファイアウォール)
  change-set/                 既存 改稿 (軽量運用)
  review-change/              既存 改稿
  autonomy/                   既存 改稿 (膨張パス禁止・品質ゲート)
templates/
  work.md, writing-contract.md, scene.md, beta-review.md, research-note.md   改稿
  craft-engine.md, craft-voice.md, interest-scorecard.md,
  polish-report.md, release-checklist.md                                     新規
  (既存の canon/entities/events/... は変更しない)
tools/
  manuscript_lint.py          決定論的 lint
  export.py                   決定論的 export
  release_gate.py             公開ゲート
  init_work.py                作品ディレクトリ生成
  selftest.py                 self-test ランナー
  tests/                      fixtures + unittest
  README.md
examples/
  README.md
  before-after.md             v1的要約 → v2的場面の書換え実例 (注釈付き)
  sample-work/                小さな実例 (任意。作るなら lint 0 error 必須)
.github/workflows/kit-ci.yml  selftest + lint
```

### 3.1 作品ディレクトリ (v2 で追加されるもの)

```
work.md                ++ 面白さの設計 (約束/フック/快楽/感情の弧/禁じ手/声)
craft/engine.md        物語エンジン (欲求・欠落・対立・代償・時計・約束)
craft/voice.md         文体の声 (サンプル段落・禁止語彙・リズム)
plan/tree.md           各話に hook/promise/detonator/payoff 必須
build/                 作業生成物 (lint/export レポート・epub 中間) — 公開しない
out/                   公開物のみ (manuscript.md/.txt/.epub)
```

`out/` 禁止: 企画書・調査ノート・スクリプト・下書き・リンク集・画像。
`build/` と `out/` の区別を全スキルが守る。

---

## 4. 出来事・状態の語彙

- **spark**: 企画を成立させる最小の面白さ。角度・ログライン・フック・約束。
- **engine**: 作品全体を駆動する構造 (主人公の欲求/欠落/恐怖、対立、代償、
  時計、ジャンルの快楽、モチーフ)。
- **detonator**: 章に最低1つ必須の「読者の予想を裏切り、かつ納得させる」
  強いビート。例: 反転、暴露、喪失、選択の代償、意外な具体物。
- **hook**: 冒頭で読者に立つ問い/異物感。
- **pull**: 章末に残す未解決の問い・予感。
- **skip test**: この場面を飛ばしたら物語が壊れるか。壊れないなら削る/統合する。
- **interest gate**: 外部読者テストの合否 (high 1 or medium 3 で再改稿)。
- **polish**: 推敲。削る・具体化・声・読み上げ・アーティファクト除去。
- **release gate**: lint 0 error + 状態検査 + out/ 清浄 + 推敲記録。
- **引用ファイアウォール**: 調査ノートのURL・出典・数値・原文を本文へ
  コピーしない。本文は創作、出典は research/ にのみ残す。

---

## 5. tools 仕様 (決定論的。Python 3 標準ライブラリのみ)

共通: `--json` を付けると機械可読 JSON を stdout に出す。日本語ファイル名を扱う。
終了コード: `0` 合格 / `1` ゲート不合格 / `2` 使い方・IO エラー。

### 5.1 `tools/manuscript_lint.py`

```
python3 tools/manuscript_lint.py [--json] [--fix] [--workdir DIR] [--legacy]
                                 [--glossary FILE] FILE...
```

- 入力は原稿 Markdown (export 済み、または scenes/*.md を連結したもの)。
- `--workdir` 指定時は `out/` の原稿と `scenes/` の本文を比較し、**stale export
  (原稿がシーンより古い/不一致)** を検出する。
- `--legacy` は v1 形式の互換 (面白さの設計・craft/・polished フラグ・
plan 解析の欠落を warn にする)。**polish/beta 記録・out/ 清浄・lint E は
gate と同じく error** (v1 の「推敲なしで公開」を再発させない)。
- `--fix` は安全な自動修正のみ: BOM/CRLF 統一、行末空白、3連以上の空行、
  重複した区切り線、末尾の重複 `(了)`、全角/半角の区切り統一。**本文の語句は
  書き換えない。**
- 出力例:
  ```
  E L001 reference  out/foo.md:42  出典: https://… が本文に残っています
  W W001 emotion    out/foo.md:88  「悲しかった」— 感情の名指し (1,200字あたり 4.2)
  ```
- 統計 (chars / scenes / chapters / dialogue_ratio / sentences) を末尾に出す。

検査コード (E = 公開不可):

| code | 内容 |
| --- | --- |
| E L001 | URL / Markdownリンク / `出典:` `参照:` `資料:` `引用:` `ソース:` / `research/` への参照 |
| E L002 | 台帳メタ混入: `canon/` `contracts/` `scenes/` `plan/` `proposals/` `changesets/` `work.md` `p-0001` `cs-0001` `f001` `ent-c01` `ev01` `fs01` `ke01` `rev N` |
| E L003 | ビート見出し・番号行: `^[一二三四五六七八九十百]+$` 単独行、`【…】` 単独行、`^#+ ` (本文中の見出し)、`（第N話・了）` 等の制作メモ |
| E L004 | 重複ブロック: 15字以上の同一行が2回以上 / 同一章内の同一文の重複 |
| E L005 | 話見出しの順序異常 (欠番・重複・逆行) |
| E L006 | プレースホルダ: `[※未執筆]` `TODO` `FIXME` `XXX` `要確認` `<<` `{{` `（※`。`未定` は行全体・`（未定）`・`[未定]`・`〜: 未定` のようなプレースホルダ文脈のみ (通常文の「未定」は対象外) |
| E L007 | stale export (`--workdir`) |
| E L008 | エンコーディング異常 (BOM/CRLF混在/デコード不能) |
| E L009 | 末尾・章末の重複 `(了)` / `（了）` |
| E L010 | 区切り記号の混在 (`◆` と `◇` と `***` の混用)、区切りの連続 |
| E L011 | scene ID 混入 (`シーン 1-2`、単独 `1-2` 行) |
| E L012 | 空シーン/極端な短さ (本文 200 字未満の話) |

警告 (W = 出荷可だが推敲対象):

| code | 内容 |
| --- | --- |
| W001 | 感情の名指し密度 (悲しい/嬉しい/怖い/寂しい/つらい/美しい/すごい/とても 等) |
| W002 | 抽象語密度 (「こと」「もの」「気持ち」「感じ」の連続) |
| W003 | 台詞比率が 10% 未満 or 70% 超 |
| W004 | 長段落 (600字超) / 長文 (120字超) |
| W005 | 章内の同一 4-gram 反復 (回数付き) |
| W006 | 英字の残留 (glossary 未登録の3文字以上) |
| W007 | 和文直後の半角 `!?` や不自然な空白 |
| W008 | 「言った/思った/見た」の連続 (同一章で突出) |
| W009 | 要約体の密度 (「〜ことになる」「〜のである」「〜だろう」) |
| W010 | 同一起始 (同一章で同じ2〜3字始まりの行が5回以上) |

`--fix` 対象: L008 の BOM/CRLF、行末空白、空行過多、L009 の重複末尾、L010 の
区切り統一 (既定 `◆`)。修正した内容を stdout に列挙する。

### 5.2 `tools/export.py`

```
python3 tools/export.py [--workdir .] [--order 1-1,1-2,...]
                        [--title TITLE] [--separator SEP]
                        [--md] [--txt] [--epub]
                        [--release] [--no-lint] [--legacy]
```

- `plan/tree.md` から公開順を読む。書式は `## 第N話 <タイトル> [状態]` と
  `- シーン \`E-S\` <タイトル> [状態] …`。パース不能ならエラーにし、
  `--order` を促す (推測で並べない)。
- 各 `scenes/E-S.md` の本文だけを連結する (YAML ヘッダ・タイトル行・
  `---` 区切りは落とす)。話見出しは `## 第N話 タイトル` を挿入。
- 本文の語句は変えない。ただし 3 連以上の空行を 2 連に正規化する
  (空白のみの整形。詩・実験形式で空行を保つ必要がある場合は、シーン本文の
  空行を 2 連以下にしてから export する)。
  区切りは既存本文に任せる。`--separator SEP` を指定した場合のみ、同一話内の
  シーン間に同じ区切り (例 `◆`) を md/txt 共通で挿入する
  (v1 の md/txt 不統一の再発防止)。
- 標準で `out/<title>.md` を書く。`--txt` は Markdown 記号を落とした
  プレーンテキスト (`第N話 タイトル` 行)、`--epub` は標準ライブラリの
  zipfile で最小 EPUB を書く (`out/<title>.epub`)。
- 実行前に lint を走らせ、E があれば **書かずに失敗** (`--no-lint` で回避可)。
- `--release` は `build/staging/` に生成 → `release_gate.py` 合格後にだけ
  `out/` へ移動する。**ゲート不合格時は `out/` を一切変更しない**。
  レポートは `build/export-report.md` に書く。
- `out/` に書いてよいのは `<title>.md` `.txt` `.epub` のみ (タイトルと一致する
  ファイル名。旧タイトルや別名の公開物が残っている場合は error)。

### 5.3 `tools/release_gate.py`

```
python3 tools/release_gate.py [--workdir .] [--legacy] [--json] [--no-report]
```

検査項目 (1つでも error なら exit 1):

- `work.md`: status active / 「面白さの設計」の必須7項目 (約束・冒頭のフック・
  ジャンルの快楽・感情の弧・禁じ手・声・面白さの基準) が実文で埋まっている
  (blockquote・プレースホルダ・記入例は値と数えない。legacy では warn)。
- `craft/engine.md` `craft/voice.md` が存在し、必須見出しに実文がある
  (legacy では warn)。
- 計画上の全シーンに `contracts/E-S.md` が存在し status approved。
- `scenes/E-S.md` が存在し `polished: true` (legacy では warn)。
- `foreshadowing.md` の回収期限 (`期限: YYYY-MM-DD`) 超過がない。期限未設定の
  planted は warn。
- `reviews/polish-*.md` が1件以上あり、**中身** (before/after 字数または
  cut_rate) がある。空ファイルは不可 (legacy でも error)。
- `reviews/beta-*.md` が1件以上あり、`context: external` と
  `interest_gate: pass` を含む。スコアカードの記録を必須とする
  (legacy でも error。v1 の「外部テストなしで出荷」を防ぐ中核)。
- `out/` の内容が `<title>.md/.txt/.epub` のみ (それ以外は error)。
- `manuscript_lint.py` を実行して E 0 件。対象は `out/*.md` / `out/*.txt` /
  `scenes/*.md` (ソースのアーティファクトも見逃さない)。
- レポートを `reviews/release-<YYYYMMDD>.md` に書く (自動生成。手動チェックは
  `reviews/release-checklist-<YYYYMMDD>.md` に分離する)。`--no-report` で
  書き込みを抑止できる (CI/読み取り検査用)。

### 5.4 `tools/init_work.py`

```
python3 tools/init_work.py <target-dir> --title "..." [--mode short|serial] [--force]
```

- `templates/` から作品骨格を生成。`craft/` `build/` `out/` も作る。
- `work.md` の title / mode / status: setup を埋める。
- 既存ディレクトリは `--force` がない限り拒否。

### 5.5 `tools/selftest.py`

- `tools/tests/` の unittest を実行。fixtures:
  - `good.md` → lint exit 0
  - `bad_url.md` / `bad_outline.md` / `bad_dup.md` / `bad_stale/` → 期待 code で exit 1
  - `fixable.md` → `--fix` 後に 0
- export の結合順・話見出し・YAML 除去を検証。
- release_gate の work fixture (legacy / v2) を検証。
- 外部依存なし。CI と同じコマンドで動く。

### 5.6 既知の限界 (v2.0.0)

- `manuscript_lint.py` は 1 ファイル (約1,000行)。22 検査 + stale + `--fix` + CLI を
  持つため。機能追加時はモジュール分割してよい (I/F は不変)。
- `release_gate.py` は自動レポート (`reviews/release-<date>.md`) を書く。
  手動チェックリストは `reviews/release-checklist-<date>.md` に分離し、
  ゲートは上書きしない。
- lint の `--legacy` は現状 no-op。v1 互換の緩和は `release_gate.py` 側で行う。
- `export.py` は `scenes/<E-S>.md` を前提とする。v1 の `scenes/<N>.md`
  (1話1ファイル) は `--order` でも解決しないため、`<N>-1.md` にリネームする
  (`docs/MIGRATION.md` §8.4)。
- EPUB は最小 EPUB3 (表紙・画像・CSS なし)。
- `examples/before-after.md` は規範の説明用で、v1 引用部に意図的に E を残す。
  lint 0 の実例は `examples/sample-work/`。
- EPUB の `dcterms:modified` は生成日時を使うため、同じ入力でも日付が変わると
  バイト列が変わる (内容の決定性は保たれる)。完全再現が必要なら `--date` を
  将来追加する。

---

## 6. スキル要件 (各 SKILL.md の必須内容)

frontmatter (`name`, `description`) は v1 と同じ形式。本文は日本語・簡潔・
実行可能な手順。長すぎる講義をしない (目安 80–180行)。各スキルは必ず
「いつ使うか」「入力」「手順」「出力/記録先」「アンチパターン」を含む。

### 6.1 spark (新規)
- 入力: 作者のノリ・ジャンル・制約・参考。
- 手順: 角度を5つ作る (誰の物語か / 何を失うか / 何が普通と違うか / どんな
  具体物が残るか / どんな声で語るか) → 各案を「1行ログライン + 冒頭3行 +
  この作品にしかない具体物1つ + 面白さの源泉 (何で読者を引っ張るか) +
  類似作品との差分 + 危険 (つまらなくなる罠)」で書く → 作者に選ばせる/混ぜる →
  `work.md` の面白さの設計と `craft/engine.md` を作る。
- 必須ゲート: 「この作品を一言で売るなら」「読者が最初に知りたくなる問いは何か」
  「その問いに答えが出るまで引っ張れるか」に答えられない案は捨てる。
- アンチパターン: 設定だけの案 / 既視感のある案 / 主人公が受動的な案 /
  「テーマ」はあるが「事件」がない案。

### 6.2 scene-craft (新規)
- 場面の設計: dramatic_question / want / obstacle / turn / cost /
  entry (遅く入る) / exit (早く出る) / button (余韻の一行) / pov filter /
  concrete detail 3つ / subtext / skip test。
- 「この場面を要約すると1文になる。その1文に意外性と代償があるか」を確認
  (静かな余韻・日常系・実験構成などで意図的に外す場合は `craft/engine.md` /
  `craft/voice.md` に狙いを宣言)。
- 展開が淡々・お使いになりそうなときの「打開策カタログ (オプション)」を
  義務ではなく引き出しとして参照する (`docs/CRAFT.md` §4)。
- 台詞: 目的・言わないこと・齟齬。地の文: 五感・動作・具体名。
- アンチパターン集 (説明会話、感情の名指し、報告口調、全員丁寧、etc)。
- `templates/writing-contract.md` の craft 欄を埋める手順を書く。

### 6.3 polish (新規)
- 全原稿を1回通す工程。手順:
  1. 通読して「どこで退屈したか」を付箋 (行番号) で記録。
  2. ノイズを削り、作品の味を残す: AI特有の冗長な言い換え・説明過多・重複は
     容赦なく削るが、`craft/voice.md` に定めた「削らない味」(温度・リズム・
     生活感・意図的な過剰さ) や初見読者向けの最小限の補助線は守る。
     削減率 (10–20% 等) は機械的な目標にしない。
  3. 具体化: 抽象語・感情語・比喩を具体物/動作に置換 (意図的な心情吐露など
     `craft/voice.md` で宣言された味は尊重)。
  4. 声: 台詞だけ抜いて誰か判別できるか。語り口を揃える。
  5. リズム: 長短・段落・改行。読み上げて詰まる箇所を直す。
  6. 境界: 章頭/章末のフックと引きを強化。
  7. アーティファクト掃除: `manuscript_lint.py` 0 error / `--fix` 適用。
  8. `reviews/polish-<date>.md` に before/after 字数・増減率・主な変更・守った味を記録。
- 削った結果 200字未満になった場面は統合を検討。

### 6.4 release-gate (新規)
- 公開前チェックリスト (`templates/release-checklist.md`) に沿う。
- コマンド: `python3 tools/release_gate.py` / `manuscript_lint.py` / `export.py --release`。
- out/ 清浄、リンク0、ID0、推敲記録あり、全話 hook/pull (または宣言した意図的逸脱) あり、
  外部読者テスト済み。
- 不合格時は作者に「何が落ちたか」を選択肢付きで報告。ゲートを通さず公開しない。

### 6.5 既存スキル改稿
- `write-scene`: writer プロンプトに **面白さの指示** を追加。要約禁止・場面化・
  具体・台詞・転・五感 (`craft/voice.md` / `craft/engine.md` に宣言された味や
  意図的な逸脱は尊重)。検査に **興味監査 (自己)** を追加。revise は
  「整合性 1回 + 興味 2回」まで。文字数目安は下限として扱い、水増し禁止。
- `beta-read`: 外部化必須 + **興味スコアカード** (`templates/interest-scorecard.md`)
  を必ず使う。診断用の問い: 離脱ポイント / 推進力と予定調和 (お使いになっていないか) /
  温度と人物の厚み / 完全初見の理解度 / 次のページを読む理由 / 一番記憶に残った
  具体物 / 予想を裏切られた箇所 / 感情が動いた箇所。
  high 1 or medium 3 で revise 発火、polish 前なら polish に回す。
- `autonomy`: 「膨張パス」を禁止し「場面化パス」「削減パス (ノイズを削り味を残す)」
  を定義。品質停車点で interest gate + polish を必須化。完走≠合格。上限に達しても
  未合格なら未完了。
- `plan-work`: 各話に hook / promise / detonator / payoff / structure tag /
  skip test を必須。あらすじの段階で面白さを検査。
- `init-work`: craft ヒアリング (約束・快楽・声・禁じ手・感情の弧) と
  short/serial モード選択。`craft/` 生成。
- `export`: `tools/export.py` 経由を必須化。out/ は公開物のみ。手作業連結の禁止。
- `research`: 引用ファイアウォール節を追加。調査結果の「本文への転用」欄
  (言い換え・創作上の扱い・出してよい形) を必須化。URL/出典は本文・out/ に
  出さない。転用時に本文へコピーしない。
- `change-set` / `review-change`: 軽量モードでは L0/L1 を簡略化。ただし
  「推敲 (polish) は変更セット不要の L0 工程」と明記。整合性レビューに
  「退屈/要約体/感情の名指し」の観点を追加。
- `orchestrator-dialogue`: 相談を「面白さの相談」と「管理の相談」に分ける。
  面白さの相談は spark / scene-craft / polish に接続。管理の質問を最小化し、
  一度に1つ。作者にファイル管理をさせない原則は維持。

### 6.6 共通の禁止 (全スキル)
- 本文の代わりに「あらすじ」「ビート一覧」を書くこと。
- 「一 / 二 / 三」の番号見出しを本文に入れること。
- 文字数を満たすための水増し・挿入パス。
- `out/` に企画書・調査・スクリプト・リンクを置くこと。
- 整合性検査を通しただけで「面白い」と報告すること。

---

## 7. テンプレート要件

- `work.md`: 既存に加え「面白さの設計」節を追加 —
  約束 (読者に渡す快楽) / 冒頭のフック / ジャンルの快楽 / 感情の弧 /
  禁じ手 (この作品がやらないこと) / 声 (文体・人称・テンポ) /
  面白さの基準 (この作品で「面白い」と言える具体) / モード (short|serial)。
- `writing-contract.md`: 既存に加え craft 欄 —
  scene_job / dramatic_question / want / obstacle / turn / cost /
  entry / exit / button / detonator / concrete_details / subtext /
  skip_test / pov_filter / voice_notes / prose_floor (下限字数) /
  prohibit_summary (true 固定)。
- `scene.md`: `polished: false` と `polish_review:` を追加。
- `beta-review.md`: 興味スコアカード節と「読者が次を読む理由」を追加。
- `research-note.md`: 「引用ファイアウォール」節 (本文にコピーしない/
  転用時の言い換え/出典はここにだけ残す) を追加。
- 新規: `craft-engine.md`, `craft-voice.md`, `interest-scorecard.md`,
  `polish-report.md`, `release-checklist.md`。各テンプレートは記入例1行付き。

---

## 8. 文体・表記の共通ルール (全成果物)

- 日本語。repo の既存文書と同じ「だ・である」調 (docs/AGENTS) と
  「です・ます」調 (README) を使い分ける。スキルは「である」調。
- 見出しは `##` まで。過剰な絵文字・装飾は使わない。
- コードブロックには実行可能なコマンドを書く。
- 今日の日付は 2026-11-17。CHANGELOG のバージョンは v2.0.0。
- ファイル間参照は実在パスで書く (壊れたリンクを残さない)。
- 用語は本仕様の §4 に統一する。

---

## 9. 受入条件 (Definition of Done)

1. すべての新規/改稿ファイルが存在し、参照リンク切れがない。
2. `python3 tools/selftest.py` が全テスト成功。
3. `python3 tools/manuscript_lint.py examples/sample-work/out/*.md` が exit 0。
   `examples/before-after.md` 内の v1 引用例は意図的に E を検出する
   (規範の説明用。CI の lint 対象外)。
4. `examples/before-after.md` が、v1 の要約体と v2 の場面化の違いを
   具体的に示し、どの規範で直したか注釈している。
5. `tools/export.py` で fixture 作品を export でき、`--release` が通る。
6. 各 SKILL.md が「いつ使うか/手順/記録先/アンチパターン」を含み、
   `tools/` の実コマンド名と一致している。
7. AGENTS.md から全スキル・tools・docs へ到達できる。
8. v1 作品を壊さない: `--legacy` で lint/gate が動く。
9. 実作品 (ato-de-yomu) に新 export/lint を適用し、`(了)` 重複などの
   アーティファクトが消えた原稿を生成できる (v2.0.0 で実施済み。
   `docs/VERIFICATION.md` §8 に実測値)。
10. 独立レビュー (別コンテキスト) で重大な矛盾・リンク切れ・未実装がない。

---

## 10. 担当スコープ (並列実装)

| 担当 | 書いてよいファイル |
| --- | --- |
| Lead | AGENTS.md, README.md, CHANGELOG.md, .gitignore, docs/DESIGN.md, docs/DIAGNOSIS.md, docs/PHILOSOPHY.md, docs/MIGRATION.md, docs/VERIFICATION.md, 統合修正 |
| craft-author | `.agents/skills/{spark,scene-craft,polish,release-gate}/SKILL.md`, `docs/CRAFT.md`, `templates/{craft-engine,craft-voice,interest-scorecard,polish-report,release-checklist}.md`, `examples/**` |
| process-rewriter | `.agents/skills/{orchestrator-dialogue,init-work,plan-work,write-scene,beta-read,export,research,change-set,review-change,autonomy}/SKILL.md`, `templates/{work,writing-contract,scene,beta-review,research-note}.md` |
| tools-engineer | `tools/**`, `.github/workflows/kit-ci.yml` |

- 担当外のファイルは編集しない (読むのは自由)。インターフェース変更が必要なら
  Lead にメッセージする。
- 既存ファイルの全面書換えは可 (改稿指定のため)。ただし他担当の内容を
  取り込まない (重複を避ける)。
- git 操作は Lead のみ。commit/push をしない。
- 仕様にない新規ファイルを勝手に増やさない (必要なら Lead に提案)。
