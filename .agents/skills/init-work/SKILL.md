---
name: init-work
description: 新しい作品を対話ヒアリングから立ち上げる。モード (short|serial) 選択、面白さの設計 (約束・快楽・声・禁じ手・感情の弧・基準) のヒアリング、craft/engine.md・craft/voice.md の生成。「新しい作品を始めたい」「作品を作りたい」で使う。
---

# init-work — 作品の対話初期化

長大な入力フォームではなく対話から開始する。最初に決めるのは設定ではなく
**この作品の面白さ**と**モード**である。

## いつ使うか

- 白紙から新しい作品を始めるとき。
- 続編・書きかけ原稿から始めるとき。
- 既存作品のモードや craft を後から整えるとき。

## 入力

- 作者のノリ・ジャンル・制約・参考作品。
- 既存素材 (続編・書きかけ原稿の場合)。
- `templates/work.md`、`templates/craft-engine.md`、`templates/craft-voice.md`。

## 手順

1. **起点の確認**: 白紙 / 続編・スピンオフ / 書きかけ原稿・素材の取り込み。
   - 続編・スピンオフ: 前作から `canon/facts.md`・`entities.md`・
     `knowledge.md`・`events.md` をコピー継承 (ID・canon_revision を維持し、
     出所に前作を記す)。計画・契約・本文は新規。`craft/` は新規に作る。
   - 書きかけ: 既存本文は `scenes/` に rev 1・source: manual で配置。設定
     メモは正典候補に仕分け、作者確認したものだけ `canon/facts.md` に入れる。
2. **モード選択** (`work.md` の `mode`):
   - `short` (既定・短編/単発): spark → 簡易計画 → 契約1枚 → 執筆 →
     興味監査 → 推敲 → 公開ゲート。正典・変更セット・提案は必要時だけ。
     推敲と公開ゲートは通す。
   - `serial` (連載): 従来の帳簿 (正典・計画・変更セット・レビュー) を維持し、
     全工程に面白さのゲートを足す。
3. **骨格の生成**:
   `python3 tools/init_work.py <target-dir> --title "<タイトル>" --mode short`
   (連載なら `--mode serial`) を使う。`--force` は既存ディレクトリにも生成する
   (既存ファイルは上書きしないが、意図しない混在を避けるため作者の明示指示が
   あるときだけ)。ツールが使えない環境では `templates/` から `work.md`・
   `canon/`・`craft/`・`plan/`・`contracts/`・`scenes/`・`reviews/`・
   `research/`・`build/`・`out/` を作り、`work.md` の title/mode/status を
   手で埋める。
4. **craft ヒアリング** (一度に全部聞かず、重要な順に1つずつ):
   - **約束** — 読者に何を渡す作品か (快楽・読後感)
   - **ジャンルの快楽** — このジャンルで読者が期待する快感と供給方法
   - **声** — 文体・人称・テンポ。好きな一文を1つ書いてもらう
   - **禁じ手** — この作品がやらないこと
   - **感情の弧** — 読者の感情をどこからどこへ動かすか
   - **面白さの基準** — この作品で「面白い」と言える具体例
5. **craft の生成**:
   - `work.md` の「面白さの設計」節を埋める (空欄のまま active にしない)
   - `craft/engine.md` — `templates/craft-engine.md` を雛形に、欲求/欠落/
     恐怖・対立・代償・時計・約束・ジャンルの快楽を書く
   - `craft/voice.md` — `templates/craft-voice.md` を雛形に、サンプル段落・
     人称・テンポ・禁止語彙を書く
   - 白紙なら、骨格生成 (手順3) の**後**に `.agents/skills/spark/SKILL.md` で
     企画を面白くしてから engine を書く (順序は init_work.py → spark →
     engine。spark の内容はここに書かない)
6. **憲章・ポリシーの確認**: 媒体・長さ・連載性・公開頻度、確定したいもの/
   意図的に未確定にするもの、許容する実験、変えてはならない前提、計画の
   先行範囲、自律運転ポリシー (off/draft/auto・上限・停止条件)。
7. **初期の正典・登場要素**: short では必要最小限。確定した設定は
   `canon/facts.md` に、人物等は `entities.md` に初期登録する (初期登録は
   変更セット不要 — 出所を「対話」と記す)。
8. **active 化**: 面白さの設計の必須欄 (約束/フック/快楽/声/禁じ手/基準)、
   `craft/engine.md`・`craft/voice.md`、憲章の骨格、`mode` が埋まったら
   `work.md` の status を active にする。
9. **`dialogue.md`** に初期化の決定を要約追記する。

## 出力・記録先

- `work.md` (title/premise/genre/mode/status + 面白さの設計 + 憲章 + ポリシー)
- `craft/engine.md`、`craft/voice.md`
- `canon/facts.md`、`entities.md`、`plan/tree.md`、`dialogue.md`
- 空ディレクトリ一式 (`contracts/` `scenes/` `reviews/` `research/` `build/` `out/`)

## アンチパターン

- 設定だけ聞いて面白さ (約束・快楽・声) を聞かない。
- 全設定を先に決めさせる (結末未確定は意図的か未判断かを明記すればよい)。
- short なのに従来の全帳簿を要求し、注意力を管理作業に食わせる。
- craft 欄を空のまま active にする。
- 面白さの設計を `canon/facts.md` に書く (方針と事実を混ぜる)。
