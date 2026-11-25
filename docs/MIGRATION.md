# MIGRATION — v1 作品を v2 に移行する

v1 の作品データ (canon / plan / scenes / contracts / reviews) はそのまま使える。
v2 は **規範・スキル・ツール・テンプレートを追加し、工程を足す**。既存原稿を
壊さない。ただし v1 の `scenes/<N>.md` (1話1ファイル) 形式は `scenes/<N>-1.md`
へのリネームが必要 (§8.4)。移行は「追加 → 検査 → 推敲 → 興味監査 → 公開ゲート」
の順に進める。

## 1. キットをコピーする

作品ディレクトリで:

```sh
# 規範・スキル
cp -r /path/to/vibe-sakka/.agents ./
cp /path/to/vibe-sakka/AGENTS.md ./

# テンプレートとツール
cp -r /path/to/vibe-sakka/templates ./
cp -r /path/to/vibe-sakka/tools ./
mkdir -p build craft
```

- `.agents/skills/` に新しいスキルが増える (`spark` / `scene-craft` /
  `polish` / `release-gate`)。既存スキルは v2 版に置き換わる。
- 作品データ (`work.md` / `canon/` / `plan/` / `scenes/` / `contracts/` …) は
  コピーしない。既存のものをそのまま使う。

## 2. craft ファイルを作る

```sh
cp templates/craft-engine.md craft/engine.md
cp templates/craft-voice.md  craft/voice.md
```

`craft/engine.md` に、作品の面白さの核を書く:

- 主人公が欲しいもの / 欠けているもの / 恐れているもの
- 対立 (誰・何が止めるか)
- 代償 (望みを叶えると失うもの)
- 時計 (期限・締切・迫るもの)
- 読者への約束 (ジャンルの快楽。何を渡すと宣言するか)
- モチーフ (反復する具体物・イメージ)

`craft/voice.md` に、文体の声を書く:

- 人称・距離・テンポ・一文の長さ
- この作品で使う語彙 / 使わない語彙
- 声のサンプル段落 (100〜200字。以後の本文はこれに寄せる)

## 3. work.md に「面白さの設計」を追記する

既存の創作憲章・執筆ポリシーは残し、次の節を追加する (雛形:
`templates/work.md`)。

- **モード**: short | serial
- **約束**: 読者に渡す快楽 (1〜3行)
- **冒頭のフック**: 第1話冒頭で読者に立たせる問い
- **禁じ手**: この作品がやらないこと (例: 設定説明から始める、全員が説明のために喋る、感情を名指しする)
- **声**: `craft/voice.md` への参照
- **感情の弧**: 読者の感情がどう動くか (例: 不安 → 共感 → 喪失 → 静かな希望)
- **面白さの基準**: この作品で「面白い」と言える具体例 (1〜3行)

`serial` の場合は v1 の帳簿 (canon / knowledge / foreshadowing / changesets) を
そのまま維持する。`short` の場合は契約1枚と推敲・公開ゲートだけを必須にする。

## 4. 既存作品を検査する (legacy モード)

v1 作品には `craft/` や `polished` フラグがないため、`--legacy` で検査する。

```sh
# 原稿の衛生検査 (scenes との stale も見る)
python3 tools/manuscript_lint.py --workdir . --legacy out/*.md

# 公開ゲートの状態検査 (craft 欠落は warning 扱い)
python3 tools/release_gate.py --workdir . --legacy
```

検出される典型:

- `L001` URL・出典・参照・資料リンクの残留
- `L002` 台帳ID・ファイルパスの混入
- `L003` ビート見出し (`一` 単独行)・制作メモ
- `L004` 重複行、`L009` `(了)` の重複、`L010` 区切り記号の混在
- `L007` stale export (out/ が scenes より古い/不一致)
- `W001` 感情の名指し、`W005` 反復、`W009` 要約体

`--fix` で安全なもの (BOM/CRLF、行末空白、空行過多、重複した末尾 `(了)`、
区切り統一) は自動修復できる。本文の語句は書き換えない。**`--fix` は正本の
`scenes/*.md` に対して行う** (`python3 tools/manuscript_lint.py --fix scenes/*.md`)。
`out/` は export で再生成される派生物なので fix しない (`--workdir` を付けて
`out/*.md` を fix しても、次の export で戻る)。

`--legacy` は検査を実行するフラグであり、検査を飛ばすフラグではない。v1 作品は
`reviews/polish-*.md` がないため `release_gate.py --legacy` は
**「推敲記録なし」で不合格になる (正常)**。§5〜§7 の移行手順を通してから
公開判定する。

## 5. 原稿を救出する (推敲)

自動修正のあと、`polish` スキルで全原稿を推敲する:

1. 通読して「退屈した箇所」「意味が取りにくい箇所」を行番号で記録。
2. AI特有の冗長な言い換え・前置き・説明過多・重複を削る (`craft/voice.md` に定めた味や初見向けの最小限の補助線は残す。削減率はノルマにしない)。
3. 抽象語・感情語・比喩を具体物と動作に置換。
4. 台詞だけ抜いて誰の発話か判別できるか確認。声を揃える。
5. 章頭・章末のフックと引きを強化。
6. `python3 tools/manuscript_lint.py --fix scenes/*.md` → E 0 を確認
   (`out/` は export の派生物なので fix しない)。
7. `reviews/polish-<date>.md` に before/after 字数・削除率・主な変更を記録。

**やってはいけない**: 字数を満たすための挿入 (膨張パス)。v1 がこれで
台詞破損を起こした。足すのではなく、場面化し直すか削る。

## 6. 興味監査を行う

`beta-read` スキルで、正典・計画を知らない新規コンテキストに原稿だけを
渡し、`templates/interest-scorecard.md` で採点する。特に聞くこと:

- どこで読むのをやめたくなったか
- 次を読む理由は何か
- 一番記憶に残った具体物は何か
- 予想を裏切られた箇所はあるか
- 感情が動いた箇所はあるか

high 1 件 or medium 3 件以上なら `polish` または `write-scene` の revise に
戻す。結果は `reviews/beta-*.md` に残す。

## 7. 公開ゲートと export

```sh
# 原稿を再生成 (scenes から。手作業の連結は禁止)
python3 tools/export.py --workdir . --md --txt --epub

# 公開前ゲート
python3 tools/release_gate.py --workdir .

# out/ に公開物以外が混ざっていないか
ls out/
```

`out/` に残すのは `<title>.md` / `.txt` / `.epub` だけ。企画書・調査ノート・
生成スクリプト・リンク集は `plan/` `research/` `build/` へ移す。
`export.py --release` はゲート込みで実行し、失敗時は何が落ちたかを表示する。

## 8. 既存作品の典型パターン別メモ

### 8.1 あらすじ体で書かれてしまった作品

- `scenes/` の各話がビート見出しで区切られている場合、そのまま推敲しても
  場面にはならない。**場面化パス** (要約を場面として演じ直す) が必要。
- 手順: `scene-craft` で場面の欲求・障害・転・代償を設計し直す →
  `write-scene` で書き直す (rev+1、旧版は `scenes/history/`) →
  `beta-read` → `polish`。
- 契約が「必須イベント」だけで作られている場合は、craft 欄を追記してから
  書き直す。少なくとも dramatic_question / want / obstacle / turn / cost /
  detonator は埋める。

### 8.2 out/ に資料が混在している作品

- `out/` の非公開物を `plan/` に移す (例: `out/企画書.md` → `plan/企画書.md`)。
- 企画書内の外部URLは `plan/` に残してよい (公開物ではない)。
  本文・`out/` には URL を出さない。
- `python3 tools/manuscript_lint.py out/*.md` で L001/L002 が 0 になるまで
  原稿を直す (原稿にリンクが混ざっている場合は削除ではなく、その内容を
  物語内の事実として書き直す)。

### 8.3 v1 の contracts / reviews が残っている作品

- `contracts/` は v2 の craft 欄がなくても動く (`release_gate --legacy`)。
  書き直す話から新しい契約に置き換える。
- 過去の `reviews/` は履歴として残す。v2 の推敲記録・公開記録は
  別ファイル (`polish-*.md` / `release-*.md` / `release-checklist-*.md`) に
  追記する。`release-<date>.md` は gate の自動生成 (上書き)、
  `release-checklist-<date>.md` は手動チェックの記録。

### 8.4 v1 の `scenes/<N>.md` (1話1ファイル) 形式

v1 の一部の作品は `scenes/1.md` のように 1 話 1 ファイルで書かれている。
v2 の `export.py` は `scenes/<E-S>.md` (例 `1-1.md`) を前提とするため、
次のどちらかで対応する:

- **推奨**: ファイルを `scenes/<N>-1.md` にリネームする (第N話のシーン1)。
  `git mv scenes/1.md scenes/1-1.md` のように行い、本文の内容は変えない。
  `plan/tree.md` のシーン行も `- シーン \`N-1\` ...` に直す。
  `scenes/history/1/` がある場合は `scenes/history/1-1/` へ同様に移す。
- 一時的な回避: 公開順を明示して `--order 1-1,2-1,...` を渡す。
  ただしファイル名が `<E-S>` でないと export は読めないため、結局リネームが要る。

`plan/tree.md` が表形式 (v1 の一部) でパースできない場合も、シーン行を
`- シーン \`E-S\` ...` の正規形に直すか、`--order` を使う。推測で並べさせない
のが v2 の設計。

### 8.5 既存作品の検証で fail するのが正常

`--legacy` は検査を**実行する**フラグであり、検査を飛ばすフラグではない。
craft ファイルや `polished: true` の欠落は警告に緩めるが、`reviews/polish-*.md`
がない・`out/` に公開物以外がある、などは `--legacy` でも不合格になる。
v1 作品に `release_gate.py --legacy` をかけて不合格になるのは
「v1 の成果物がそのままでは公開不可」という正しい判定である (正常)。
§4〜§7 の移行手順 (検査 → 推敲 → 興味監査 → 公開ゲート) を通してから
公開判定する。

## 9. 移行チェックリスト

- [ ] `.agents/skills/` に v2 の 14 スキルがある (`spark` / `scene-craft` /
      `polish` / `release-gate` を含む)
- [ ] `AGENTS.md` が v2
- [ ] `tools/` がある。`python3 tools/selftest.py` が通る
- [ ] `work.md` にモードと面白さの設計がある
- [ ] `craft/engine.md` と `craft/voice.md` がある
- [ ] `out/` が公開物のみ
- [ ] `manuscript_lint.py --legacy` で E 0
- [ ] `release_gate.py --legacy` が合格 (または残課題が明示されている)
- [ ] `reviews/polish-*.md` がある
- [ ] 外部読者テストを1回以上通した
