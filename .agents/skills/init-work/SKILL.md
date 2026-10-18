---
name: init-work
description: 新しい作品を対話ヒアリングから立ち上げる。StoryCharter・NarrativePolicy・初期の正典・登場要素を work.md / canon/facts.md / entities.md に作る。「新しい作品を始めたい」「作品を作りたい」で使う。
---

# init-work — 作品の対話初期化

長大な入力フォームではなく対話から開始する。

## 手順

1. **起点の確認**: まずどこから始めるかを聞く。
   - **白紙から**: 以下の手順をそのまま進める
   - **続編・スピンオフ**: 前作のワークスペースから `canon/facts.md`・
     `entities.md`・`knowledge.md`・`events.md` をコピー継承する
     (ID・canon_revision も維持し、各行の出所に前作を記す)。
     計画・契約・本文は新規として始める
   - **書きかけ原稿・素材の取り込み**: 既存本文は `scenes/` に
     rev 1・source: manual で配置。設定メモは正典候補として仕分けし、
     作者確認したものだけ `canon/facts.md` に入れる (推測で確定しない)
2. `templates/` から雛形をコピーして初期ファイルを作る:
   - `work.md` (status: setup, canon_revision: 0)
   - `canon/facts.md`, `canon/history.md`, `entities.md`, `knowledge.md`,
     `events.md`, `foreshadowing.md`, `plan/tree.md`, `dialogue.md`
   - 空ディレクトリ: `contracts/` `scenes/` `scenes/history/` `proposals/`
     `changesets/` `reviews/` `research/` `scratch/` `out/`
3. **ヒアリング**: 以下を一度に全部聞かず、重要なものから対話で少しずつ
   確認する:
   - 読者に味わってほしい体験・テーマ・トーン
   - 媒体・長さ・連載性・公開頻度の希望
   - 確定したいもの (結末・過去・正体・ルール) と、意図的に未確定のまま
     にしたいもの
   - 登場人物や世界の出発点
   - 許容する実験・意外性と、変えてはならない前提
   - どの範囲まで計画を固めてから本文を書くか
   - 自律運転のレベル (off / draft / auto)・実行上限・停止条件
4. **執筆方式の確認**: 以下のテンプレートを候補として提示し、
   作風・期間・先行計画の必要度から作者と選ぶ/調整する。
   - blueprint-first: 結末・真相・到達点・長期アークを本文より先に確定
   - rolling-horizon: 全体結末は未確定可。現在アークの到達点と次の
     2単位は固める
   - episodic: エピソード単位。長期設定は保つ
   - short-form: 焦点・対立・読後感・終わり方の条件を早期確認
   - experimental/custom: 独自ルール。意図的矛盾の種類を検査ポリシーに定義
5. **記録**: 決まった分を `work.md` の創作憲章・執筆ポリシーに書く。
   確定した設定は `canon/facts.md` に、登場人物等は `entities.md` に
   初期登録する (初期登録は変更セット不要 — 出所を「対話」と記す)。
6. **active 化**: 体裁 (title/premise/genre) と憲章の骨格が固まったら
   `work.md` の status を active にする。
7. `dialogue.md` に初期化の決定を要約追記する。

## 注意

- 初期設定は一度に完了しなくてよい。作業中に方針を更新できるが、既存の
  計画へ影響する変更は変更セットとして扱う。
- 「全設定を先に決める」ことを強制しない。ただし結末を未確定にするなら
  それが意図的 (open_by_design) か未判断かを憲章に明記する。
