# tools — 決定論的ツール

v1 の失敗 — 推敲漏れ・資料リンク残留・要約体の出荷・stale export・`out/` の
汚染 — を、モデルの注意力ではなく機械的に防ぐためのツール群です。

- 対象: Python 3.12 以上。**外部ライブラリなし** (標準ライブラリのみ)。
- 日本語ファイル名・日本語本文をそのまま扱います。
- `--json` を付けると機械可読 JSON を stdout に出します。
- 終了コードは共通で **0 = 合格 / 1 = ゲート不合格 / 2 = 使い方・IO エラー**。

```
tools/
  manuscript_lint.py   原稿の lint (E 12 種 / W 10 種)・stale export 検査・安全な --fix
  export.py            scenes/ を計画順に連結し out/ に md/txt/epub を書く
  release_gate.py      公開前ゲート (状態・契約・推敲・out/ 清浄・lint E0)
  init_work.py         templates/ から作品ディレクトリの骨格を生成
  selftest.py          tools/tests/ の unittest を実行 (CI と同じコマンド)
  tests/               fixtures と unittest
  README.md            このファイル
```

## クイックスタート

```bash
# 1. 作品ディレクトリを作る
python3 tools/init_work.py ~/works/灯の話 --title "灯の話" --mode short

# 2. 本文を書き、lint する (out/ の原稿を検査)
python3 tools/manuscript_lint.py --workdir ~/works/灯の話 ~/works/灯の話/out/灯の話.md

# 3. export する (lint E があれば書かずに失敗)
python3 tools/export.py --workdir ~/works/灯の話 --txt --epub

# 4. 公開ゲート
python3 tools/release_gate.py --workdir ~/works/灯の話
```

キットの外に作品を置く場合も、`--workdir` に作品ディレクトリを渡せば同じように
動きます。

---

## 1. manuscript_lint.py

原稿 Markdown の決定論的 lint です。入力は **export 済みの原稿**、または
`scenes/*.md` を連結したものです。シーンファイルを直接渡す場合は、先頭の
タイトル行・YAML ヘッダ・`---` 区切りを自動的に読み飛ばします。

```
python3 tools/manuscript_lint.py [--json] [--fix] [--workdir DIR]
                                 [--legacy] [--glossary FILE] FILE...
```

| 引数 | 意味 |
| --- | --- |
| `FILE...` | 検査する原稿 (複数可) |
| `--json` | `{"errors":[],"warnings":[],"infos":[],"stats":{},"files":[]}` を stdout に出す |
| `--fix` | 安全な自動修正のみ行い、修正内容を stdout に列挙する |
| `--workdir DIR` | 作品ディレクトリ。`scenes/` と `out/` を比較して stale export を検査 |
| `--legacy` | v1 作品の互換。現在の lint では判定を変えません (craft 必須項目の検査は `release_gate.py` が担当) |
| `--glossary FILE` | 英字語の許可リスト (1 行 1 語、`#` でコメント)。W006 の除外に使う |

### 出力

```
E L001 reference  out/foo.md:42  出典ラベル「出典:」が本文に残っています
W W001 emotion    out/foo.md:88  感情の名指しが多い (1,200字あたり 4.2, 9 箇所)
統計: chars=12345 scenes=17 chapters=6 sentences=812 dialogue_ratio=0.42
E 1 / W 1 / I 0
```

`stats` の定義:

- `chars`: 本文文字数 (空白・改行を除く。章見出しの文字は含む)
- `scenes`: シーンとして数えた入力ファイル数。`--workdir` で `out/*.md` を
  検査した場合は `workdir/scenes/*.md` の件数
- `chapters`: `## 第N話 ...` 見出しの数
- `sentences`: `。．！？!?` で区切った文の数
- `dialogue_ratio`: `「」『』` 内の文字数 / `chars`

### 検査コード (E = 公開不可)

| code | 内容 | `--fix` |
| --- | --- | --- |
| L001 | URL / Markdown リンク / `出典:` `参照:` `資料:` `引用:` `ソース:` / `research/` 参照 | 不可 |
| L002 | 台帳メタ混入 (`canon/` `contracts/` `scenes/` `plan/` `proposals/` `changesets/` `work.md`、`p-0001` `cs-0001` `f001` `ent-c01` `ev01` `fs01` `ke01` `rev N`) | 不可 |
| L003 | ビート見出し (`一` `二` … の単独行)、`【…】` 単独行、本文中の `#` 見出し、`（第N話・了）` 等の制作メモ | 不可 |
| L004 | 重複ブロック: 15 字以上の同一行が 2 回以上 / **同一章内**の同一文 (章をまたぐ反復は W) | 不可 |
| L005 | 話見出しの順序異常 (欠番・重複・逆行) | 不可 |
| L006 | プレースホルダ (`[※未執筆]` `TODO` `FIXME` `XXX` `要確認` `<<` `{{` `（※`)。「未定」は単独行・`（未定）`・`[未定]`・値が未定 のときだけ (通常文は通す) | 不可 |
| L007 | stale export (`--workdir` 指定時のみ) | 不可 |
| L008 | エンコーディング異常 (BOM / CRLF / CR 単独 / デコード不能) | BOM・改行の統一 |
| L009 | `(了)` / `（了）` の重複、本文中の (了) | 末尾の 1 つを残して除去 |
| L010 | 区切り記号の混在 (`◆` / `◇` / `***`)、区切りの連続 | `◆` に統一・連続を 1 本に |
| L011 | scene ID 混入 (`シーン 1-2`、`1-2` の単独行) | 不可 |
| L012 | 空シーン/極端な短さ (話あたり本文 200 字未満) | 不可 |

### 警告コード (W = 出荷可、推敲対象)

| code | 内容 (閾値は 1,200 字あたり) |
| --- | --- |
| W001 | 感情の名指し (悲しい/嬉しい/怖い/寂しい/つらい/美しい/すごい/とても 等) が 3.0 以上 |
| W002 | 抽象語 (こと/もの/気持ち/感じ) が 8.0 以上 |
| W003 | 台詞比率が 10% 未満 or 70% 超 |
| W004 | 長段落 (600 字超) / 長文 (120 字超) |
| W005 | 章内の同一 4-gram の反復 (5 回以上、章ごとに上位 2 件) |
| W006 | glossary 未登録の英字語 (3 文字以上、ファイルごとに最大 8 語) |
| W007 | 和文直後の半角 `!?`、和文間の不自然な半角空白 (ファイルごとに最大 4 件) |
| W008 | 「言った/思った/見た」が 4 回以上かつ密度 4.0 以上 (章ごと) |
| W009 | 要約体 (「〜ことになる」「〜のである」「〜だろう」) が 3.0 以上 |
| W010 | 同じ 2〜3 字始まりの行が 5 行以上 (章ごと、台詞・見出しは除く) |

閾値は **目安** です。警告は公開を止めませんが、推敲 (`polish`) の対象として
扱ってください。

### `--fix` が直すもの

BOM、CRLF / CR、行末空白、3 連以上の空行、区切り記号の混在 (`◆` に統一)、
連続した区切り、末尾の重複 `(了)`。**本文の語句は書き換えません。** 修正後は
再 lint した結果で終了コードを返します。

```bash
cp -r out build/out.bak           # 念のため退避
python3 tools/manuscript_lint.py --fix --workdir . out/灯の話.md
```

### stale export の判定 (`--workdir`)

`scenes/*.md` をシーン ID (`1-2` など) の昇順に連結した本文と、`out/*.md` の
本文を **正規化して** 比較します。次の差は許容します (それ以外の 1 文字でも
差分なら L007):

- 行頭の `# タイトル`、`## 第N話 タイトル` の見出し行
- 区切り線 (`◆` `◇` `***` `---` など、その行だけのもの)
- 行をまたぐ改行・空白 (すべて除去して連結)

`(了)` は本文の一部として比較します (区切り線と違い、正規化で除外しません)。

逆に、**語句の変更・追加・欠落・順序変更はすべて差分**です。判定できない
事情がある場合は L007 を無視せず、`export.py` で作り直してください。

### 既知の限界

- 意味判断 (退屈・感情の動き・整合性) はしません。`beta-read` / `polish` の担当です。
- L006 の「未定」はプレースホルダ文脈のみです。地の文の「行き先は未定だった」は通りません。
- L008 はファイル単位の判定です。混在改行の位置までは示しません。
- L004 の文重複は「同一文 20 字以上」の完全一致のみです。章をまたぐ同一文は W に落とします (意図的なモチーフを止めないため)。
- 章見出しのない原稿は全体を 1 章として扱います。

---

## 2. export.py

`plan/tree.md` の公開順に `scenes/<E-S>.md` の本文だけを連結し、`out/` に
公開原稿を書き出します。**本文は変えません**。変えるのは次の 2 点だけです。

- 話の境に `## 第N話 タイトル` を挿入する
- シーンファイル末尾の単独 `---` (ファイル区切り) を落とし、シーン間を空行 1 つで
  連結する
- `--separator` 指定時だけ、同一話内のシーン間に同じ区切りを挿入する
  (v1 の md=`◆` / txt=`◇` 不統一の再発防止)

```
python3 tools/export.py [--workdir .] [--order 1-1,1-2,...]
                        [--title TITLE] [--separator SEP]
                        [--md] [--txt] [--epub]
                        [--release] [--no-lint] [--legacy] [--json]
```

| 引数 | 意味 |
| --- | --- |
| `--workdir DIR` | 作品ディレクトリ (既定: カレント) |
| `--order LIST` | 公開順を明示する。`plan/tree.md` を解析できないときの代替 |
| `--title TITLE` | 作品タイトル。既定は `work.md` の `title:` |
| `--separator SEP` | 同一話内のシーン間に入れる区切り (例: `◆`)。既定はなし |
| `--separator SEP` | 同一話内のシーン間に入れる区切り (例: `◆`)。md/txt で同じ区切りになる。既定はなし |
| `--md` | Markdown を出力 (既定で出力される) |
| `--txt` | 投稿用プレーンテキストも出力 |
| `--epub` | 最小 EPUB3 も出力 |
| `--release` | `build/staging/` に生成し、`release_gate` 合格後にだけ `out/` へ移動 |
| `--no-lint` | 書き出し前の lint をスキップ (非推奨) |
| `--no-report` | `--release` 時にゲートのレポートを書かない (CI 用) |
| `--legacy` | v1 作品の互換 (lint / gate に渡す) |
| `--json` | 結果を JSON で stdout に出す |

### 計画の読み方

`plan/tree.md` に次の形の行があることが前提です (正本は `templates/plan-tree.md`)。

```
## 第1話 灯 [generated]

- シーン `1-1` 朝の灯 [generated] 少女が灯をともす — 契約: contracts/1-1.md, 本文: scenes/1-1.md
```

- `## 第N話 タイトル [状態]` から話タイトルを取ります (`[状態]` は捨てる)。
- `- シーン \`E-S\` ...` の **並び順が公開順** です。推測で並べ替えません。
- 解析できない (行がない・表形式だけ等) ときは exit 2 で
  `--order 1-1,1-2,2-1` の指定を促します。
- `--order` でも話単位の連続性は検査します (同じ話が飛び飛びなら exit 2)。

### 出力

- `out/<title>.md` — 標準出力物。先頭に `# <title>`、話の境に
  `## 第N話 タイトル` を挿入します。
- `out/<title>.txt` — `--txt`。Markdown 記号 (`#` `>` `**` `*` `` ` ``) を
  落とし、話見出しを `第N話 タイトル` のプレーン行にします。
- `out/<title>.epub` — `--epub`。`zipfile` だけで作る最小 EPUB3
  (mimetype / container.xml / package.opf / nav.xhtml / content.xhtml)。
  表紙画像・縦書き指定はありません。

`out/` に書いてよいのは `<title>.md` `.txt` `.epub` だけです。作業物は
`build/` に書きます。

### lint と release

- 書き出す前に生成内容を lint し、E が 1 件でもあれば **out/ に書かずに exit 1**。
- `--release` は `build/staging/` に生成し、`release_gate.py` が **合格したときだけ**
  `out/` へ移動 (os.replace) します。不合格時は staging を消し、`out/` は
  一切変更しません (公開済みの原稿を壊さない)。exit 1。
- レポートは `build/export-report.md`: 公開順・話数・シーン数・文字数・lint の
  指摘・ゲート結果・出力ファイル。

### 既知の限界

- シーンファイル名は `scenes/E-S.md` が前提です。v1 の `scenes/1.md`
  (1 話 1 シーン) 形式はそのままでは export できません (シーン名を `E-S` に
  揃えるか、v1 の export を継続してください)。
- EPUB は本文と目次だけの最小構成です。画像・表紙・CSS は入れません。
- `--title` を `work.md` のタイトルと変えると、`--release` の out/ 名検査は
  export の出力名を追加許可して通しますが、`release_gate.py` 単体では
  `work.md` のタイトル名だけを公開物とみなします。

---

## 3. release_gate.py

公開前ゲートです。1 つでも error があれば exit 1。レポートは
`reviews/release-YYYYMMDD.md` に書きます (上書き可・自動生成専用)。

**`--legacy` は「公開判定の緩和」ではありません。** v1 形式の互換 (面白さの
設計7項目・`craft/`・`polished: true`・`plan/tree.md` 解析の欠落) だけを警告に
落とし、**`reviews/polish-*.md` と `reviews/beta-*.md` の欠落・中身不足、
`out/` 汚染、lint E は legacy でも error** です。v1 作品は「何が足りないか」が
出て不合格になり、推敲記録と外部読者テストを用意してから再実行します
(`docs/MIGRATION.md` §8.5)。
手動の公開チェックリストは `reviews/release-checklist-YYYYMMDD.md` に分けて
書いてください (自動レポートは毎回上書きされるため、追記しても残りません)。
`--no-report` を付けるとレポート自体を書きません (CI 用)。

```
python3 tools/release_gate.py [--workdir .] [--legacy] [--json]
                              [--no-report] [--today YYYY-MM-DD]
```

| 検査 | 内容 | `--legacy` |
| --- | --- | --- |
| `work.md` | `status: active`、面白さの設計の必須7項目 (約束/冒頭のフック/ジャンルの快楽/感情の弧/禁じ手/声/面白さの基準) が個別に実文で埋まっている (テンプレ説明・blockquote・`<…>` は値と数えない) | 空欄は警告 |
| `craft/` | `craft/engine.md` `craft/voice.md` が存在し空でない。engine は必須要素 (約束/欲求/対立/代償/時計/快楽/禁じ手) に実文があり、テンプレート未記入コピーでない | 欠落は警告 |
| 外部読者テスト | `reviews/beta-*.md` が 1 件以上あり、`reader:`/`context: external` と `interest_gate: pass` を含む | 同じ (error。v1 でも必須) |
| 契約 | 計画上の全シーンに `contracts/E-S.md` があり `status: approved` | 同じ (error) |
| 本文 | `scenes/E-S.md` があり `polished: true` | 未推敲は警告 |
| 伏線 | `foreshadowing.md` の `[planted]` に `期限: YYYY-MM-DD` があり期限を過ぎていない (期限なしは警告。`張設:` の日付は期限と読まない) | 同じ (error/警告) |
| 推敲記録 | `reviews/polish-*.md` が 1 件以上・空でない・`before_chars`/`after_chars` か `cut_rate` の数値がある・テンプレート未記入コピーでない | 同じ (error。v1 でも必須) |
| `out/` 清浄 | `<title>.md` `.txt` `.epub` 以外 (ディレクトリ含む) がない | 同じ (error) |
| lint | `out/*.md`・`out/*.txt`・`scenes/*.md` を lint して E 0 件 (シーン単位では 200字下限は課さない)。`--release` 時は staging 原稿と stale も検査 | 同じ (E0) |

- `--today` は伏線期限の基準日とレポート名に使います (テスト用。既定は今日)。
- 表示は `release gate: 合格 (gate E 0 / W 0, lint E 0 / W 4)` のように
  **lint の W 件数も併記**します (品質シグナルとして見る)。
- `--json`: `{"ok":bool,"errors":[],"warnings":[],"checks":[],"report":path}`。

### 既知の限界

- 伏線の期限は `期限: YYYY-MM-DD` の直後だけを読みます。`張設:` などの日付は
  期限と誤認しません。相対表現・話数指定の回収予定は判定しません。
- 期限が未記入の `[planted]` は **警告** (公開は止めない) です。回収予定日を
  `期限:` で書くことを推奨します。
- beta/polish の内容検査は「記録としての形」だけを見ます。スコアの妥当性や
  外部コンテキストの真偽は機械では判定できません (記録の有無と申告を検査)。
- 計画は `plan/tree.md` の v2 書式 (`## 第N話` + `- シーン \`E-S\``) が前提です。
  `--legacy` では解析できない場合に `scenes/*.md` で代用します (警告)。
- 推敲記録 (`reviews/polish-*.md`) は v1 でも必要です。v1 作品を公開する前に
  1 件作ってください。
- `out/` の名前検査は `work.md` のタイトルに依存します。タイトル未設定の
  作品では拡張子だけの検査になり、警告を出します。

---

## 4. init_work.py

`templates/` から作品ディレクトリの骨格を生成します。

```
python3 tools/init_work.py <target-dir> --title "..." [--mode short|serial]
                           [--force] [--json]
```

生成物:

```
work.md            title / mode / status: setup を記入済み
canon/facts.md  canon/history.md  entities.md  knowledge.md
events.md  foreshadowing.md  dialogue.md  plan/tree.md
craft/engine.md  craft/voice.md
contracts/ scenes/ scenes/history/ proposals/ changesets/
reviews/ research/ scratch/ out/ build/
```

- 既存ディレクトリは `--force` がない限り拒否します (exit 2)。
- `--force` は「既存ディレクトリでも続行し、**存在しないファイルだけ**作る」
  動作です。既存ファイルは上書きしません。
- `templates/craft-engine.md` / `craft-voice.md` が未作成でも落ちません
  (最小骨格を書きます)。
- `--json`: `{"ok":true,"workdir":...,"created":[...]}`。

---

## 5. selftest.py と CI

```bash
python3 tools/selftest.py        # 全テスト
python3 tools/selftest.py -v     # 詳細
python3 tools/selftest.py lint   # test_lint だけ
```

`tools/tests/fixtures/` の fixture で次を検証します (ネットワーク・git 非依存):

- lint: `good.md` exit 0 / URL・出典 (L001) / ビート見出し (L003) / `(了)` 重複
  (L009) / 区切り混在 (L010) / 台帳ID・scene ID (L002/L011) / 重複行 (L004) /
  stale export (L007) / BOM・CRLF (L008) / `--fix` で 0 になる `fixable.md`
- export: YAML ヘッダ除去・話見出し挿入・公開順・`--order`・txt/epub・
  lint E で書かない・`--release` 合格
- release_gate: v2 合格 fixture / v2 不合格 fixture / v1 (`--legacy`) 合格 fixture /
  txt・scenes の lint、beta・polish の中身、面白さの設計の空洞、伏線期限の3ケース、
  `--no-report`、テンプレート未記入コピーの不合格
- export: `--release` 失敗時に out/ が byte-identical・成功時は staging から移動
- init_work: 骨格生成・`--force` の扱い

CI (`.github/workflows/kit-ci.yml`) は ubuntu-latest × Python 3.12 / 3.13 で
`python3 tools/selftest.py` を実行するだけです。

---

## 6. v1 作品での使い方 (`--legacy`)

v1 作品は `craft/` と `polished:` がないため、v2 のゲートはそのままでは
通りません。`--legacy` で **v1 形式の互換だけ** を警告に落として検査できます
(面白さの設計7項目・`craft/`・`polished: true`・表形式 plan の解析欠落)。
一方、次は legacy でも **error** のままです。

- `reviews/polish-*.md` がない / 空 / `before_chars`・`after_chars` / `cut_rate` の
  数値がない (推敲なしの公開を許さない)
- `reviews/beta-*.md` がない / `external` でない / `interest_gate: pass` でない
  (外部読者テストなしの公開を許さない)
- `out/` に公開物以外がある / lint E がある

つまり v1 作品の `--legacy` は「何が足りないか」を出して **不合格** になり、
polish と beta の記録を用意してから再実行します (`docs/MIGRATION.md` §8.5)。

```bash
# 1. 現状把握: まず lint でアーティファクトを洗い出す (ファイルは変えない)
python3 tools/manuscript_lint.py --workdir ~/works/old-work ~/works/old-work/out/旧作.md

# 2. 安全な修正だけ当てる (本文の語句は変えない)
python3 tools/manuscript_lint.py --fix --workdir ~/works/old-work ~/works/old-work/out/旧作.md

# 3. 計画が v2 書式なら export、表形式なら --order で公開順を明示
python3 tools/export.py --workdir ~/works/old-work --order 1-1,1-2,2-1 --txt

# 4. ゲート (legacy)
python3 tools/release_gate.py --workdir ~/works/old-work --legacy
```

v1 でよく落ちる点:

- `out/` に企画書・調査・スクリプトが混ざっている → ゲートが error。
  `build/` か元の場所へ移す。
- `reviews/polish-*.md` がない → `polish` を通して記録を作る。
- `scenes/N.md` 形式 (1 話 1 シーン) は export の対象外です (`--legacy` でも
  解決しません)。`docs/MIGRATION.md` §8.4 に従い `scenes/N-1.md` にリネームして
  ください (エラーメッセージにも案内が出ます)。
- `(了)` の重複・区切りの混在・ビート見出しは lint E。`--fix` と手直しで消す。

---

## 7. 触ってはいけないもの

- 既存作品のファイルは変更しません ( lint は読み取り専用ですが `--fix` は
  書き換えます。実行前にバックアップを取ってください)。
- `git` 操作はしません。commit / push は Lead (人間または統合担当) の仕事です。
- 外部ライブラリを追加しません。`pytest` も使いません。
