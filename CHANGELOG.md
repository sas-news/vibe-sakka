# CHANGELOG

## v2.0.0 — 2026-11-17

**「面白さを工程にする」大改修。** v1 は破綻しない退屈を量産した。
v2 は、面白さを設計・検査・改稿・公開する工程を追加し、帳簿を下支えに降ろす。

### 追加

- **craft 層**: `spark` (企画の角度・ログライン・フック)、`scene-craft`
  (欲求・障害・転・代償・スキップテスト)、`polish` (全原稿の推敲)、
  `release-gate` (公開前ゲート) の 4 スキル。
- **決定論的ツール** (`tools/`、Python 標準ライブラリのみ):
  - `manuscript_lint.py`: URL・出典・台帳ID・ビート見出し・重複・
    `(了)` 重複・区切り混在・文字化け・stale export を検出。`--fix` 対応。
  - `export.py`: plan 順の決定論的連結。lint 不合格なら書かずに失敗。
    md / txt / epub (zipfile) を生成。`--release` でゲート込み。
  - `release_gate.py`: 契約・`polished` フラグ・伏線・推敲記録・`out/` 清浄・
    lint を検査。`--legacy` で v1 作品に対応。
  - `init_work.py`: 作品ディレクトリの雛形生成 (`craft/` `build/` 含む)。
  - `selftest.py` + `tests/fixtures/`: ツール自体の自己テスト。
- **ドキュメント**: `docs/PHILOSOPHY.md` (思想)、`docs/CRAFT.md` (技芸の正本)、
  `docs/DIAGNOSIS.md` (v1 の失敗証拠と対応表)、`docs/MIGRATION.md` (移行手順)、
  `docs/DESIGN.md` (設計仕様)。
- **テンプレート**: `craft-engine.md` / `craft-voice.md` /
  `interest-scorecard.md` / `polish-report.md` / `release-checklist.md`。
- **examples**: `before-after.md` (要約体 → 場面化の実例と注釈)。
- **CI**: `.github/workflows/kit-ci.yml` (self-test + lint)。

### 変更

- `AGENTS.md`: 面白さを中核原則に。面白さの4条件、要約禁止、外部読者テスト、
  推敲必須、公開ゲート、引用ファイアウォール、短編/連載モード、v1 失敗の
  再発防止を明記。
- `README.md`: v1 の何がダメだったか / v2 が変えたこと / 30秒クイックスタート /
  ツール I/F / 面白さの最低線 / 移行方法。
- `write-scene`: writer プロンプトに面白さの指示。要約体・ビート見出し・
  感情の名指しを失格に。craft 欄を入力に追加。revise は整合性1回+興味2回。
- `beta-read`: 興味スコアカードを必須化。外部化を必須のまま、「次を読む理由」
  「退屈した箇所」を必ず聞く。
- `autonomy`: 「膨張パス」を禁止。「場面化パス」「削減パス」を定義。
  品質停車点で interest / polish を必須化。完走 ≠ 品質合格。
- `plan-work`: 各話に hook / promise / detonator / payoff / skip test を必須化。
- `init-work`: craft ヒアリングと short / serial モードを追加。
- `export`: `tools/export.py` 経由を必須化。`out/` は公開物のみ。
- `research`: 引用ファイアウォールを追加。出典は `research/` にだけ残す。
- `change-set` / `review-change`: 軽量モードを追加。polish は L0 の推敲工程。
- `templates/work.md`: 「面白さの設計」節を追加。
- `templates/writing-contract.md`: craft 欄 (dramatic_question / want /
  obstacle / turn / cost / detonator / skip_test 等) を追加。
- `templates/scene.md`: `polished` フラグと `polish_review` を追加。
- `templates/beta-review.md`: 興味スコアカード節を追加。
- `templates/research-note.md`: 引用ファイアウォールと本文への転用欄を追加。

### 修正 (v1 の実害)

- 原稿末尾の `(了)` 重複・区切りの混在を検出して修正できるようにした。
- `out/` に企画書・調査リンク・スクリプトが残る問題を公開ゲートで阻止。
- 12話 8,500 字の要約体を「出荷可」にしたレビュー基準を、
  興味監査 + 推敲 + 公開ゲートに置き換え。

### 監査修正 (独立レビュー2本の指摘を反映)

- `export --release` を `build/staging/` 経由に変更。ゲート不合格時は `out/` を
  一切変更しない (v1 の「未推敲のまま公開物が更新される」経路を封鎖)。
- 公開ゲートの lint 対象を `out/*.md` から `out/*.txt` + `scenes/*.md` へ拡張。
  ソース側の `(了)` 重複・URL・stale export も見逃さない。
- ゲートが `reviews/beta-*.md` (external + interest_gate: pass + スコアカード) と
  `reviews/polish-*.md` (before/after または cut_rate) の**中身**を必須化。
  空ファイル・テンプレコピーでは合格しない。
- 「面白さの設計」7項目を個別検査 (blockquote・プレースホルダ・記入例を値と
  みなさない)。`craft/engine.md` の必須要素とテンプレコピーも検査。
- 伏線の期限を `期限: YYYY-MM-DD` から読み、`張設:` の日付を誤認しない。
- `L004` の同一文重複を章スコープ化 (章間のモチーフ反復は W)。
- `L006` の「未定」をプレースホルダ文脈のみに限定 (地の文の「未定」は通す)。
- 自動レポート `reviews/release-<date>.md` と手動チェックリスト
  `reviews/release-checklist-<date>.md` を分離。`--no-report` を追加。
- `--legacy` は v1 形式の互換のみ (設計/craft/polished/plan 解析を warn)。
  polish/beta 記録・out/ 清浄・lint E は legacy でも error。
- CI に sample-work の lint / gate / `export --release` を追加。
- docs: VERIFICATION の実測値更新、MIGRATION の `--fix` 対象と N.md リネーム手順、
  DESIGN の I/F (staging/--no-report/検査範囲/legacy)、AGENTS の全ファイル索引を追加。

### 非互換

- `out/` の用途が「生成物すべて」から「公開物のみ」に変わった。
  既存作品は `docs/MIGRATION.md` に従い、作業物を `plan/` `research/` `build/`
  へ移す。
- v1 の `scenes/` は `--legacy` で lint / gate できる。ただし export は
  `scenes/<E-S>.md` 前提のため、v1 の `scenes/<N>.md` (1話1ファイル) は
  `scenes/<N>-1.md` へリネームする (`docs/MIGRATION.md` §8.4)。
  `polished: true` が無いシーンは公開ゲートで警告になる。推敲してフラグを立てる。

## v1.0.0 — 2026-10-18

- 初版。正典・Writing Contract・変更セット・伏線・知識・計画のファイル規範。
- 生成→検査→修正の分離、beta-read、autonomy、export。
