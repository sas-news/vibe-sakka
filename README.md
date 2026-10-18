# Vibe作家 (vibe-sakka) — AI執筆ワークスペース規範キット

AIエージェントを**物語のオーケストレーター**として動かすための規範セット。
人間はノリと方向性だけを語り、正典・時系列・知識・計画の帳簿仕事はすべて
エージェントが請け負う。どんなエージェントハーネス (CLI・IDEエージェント等)
でも動く、ファイルだけの創作環境を用意する。

**中核原則: 人間は物語の意思決定者であり、情報管理者ではない。**

設定・正典・時系列・知識・伏線・計画・本文の依存関係を、人間が手作業で
同期する運用にしない。創作上の決定と改変はすべて対話を入口とし、エージェントが
影響範囲と変更案を作り、承認を得てから、検証可能な変更としてファイルに適用する。

## この規範が強制すること

- **対話が唯一の創作操作窓口** — 相談だけでは正典を変えない。決定は提案
  (`proposals/`) か変更セット (`changesets/`) として記録し、承認を得て適用する
- **Writing Contract ゲート** — シーンの目的・視点・必須イベント・禁止事項・
  状態変化・前後接続を定義し承認されるまで、本文生成を開始しない
- **確度の区別** — 確定 / 約束済み / 仮置き / 意図的未確定 / 未判断、
  および秘密 (読者にも未登場人物にも知られたくない事実) を正典のラベルで管理
- **変更は影響分析つき** — L0 (表現のみ) から L3 (Retcon) まで分類し、
  影響範囲・衝突・下流修正を提示してから適用
- **生成→検査→修正の分離** — 本文は writer → 決定的チェックリスト → critic
  の順で検査し、high 違反は1回だけ書き直す
- **実世界の事実も検証する** — 歴史・専門知識・手続などの現実依存事実は
  `research/` に記録・出典管理し、未検証のまま確定しない
- **自律運転に境界** — 明示許可・レベル (draft=提案まで / auto=自己承認
  で完走)・上限・停止条件つき

## 使い方

```sh
mkdir my-work && cd my-work
git init   # 推奨 (本文・正典の履歴とロールバックを git に任せられる)
cp -r /path/to/vibe-sakka/. .   # 末尾「/.」で .agents/ 等のドットファイルもコピーされる
```

エージェントハーネスを起動して「新しい作品を始めたい」と話しかけるだけ。
`.agents/skills/init-work` に従って対話ヒアリングが始まり、ファイルが作られる。

## ハーネス別のスキル配置

スキルは `.agents/skills/` に置いてある — Codex・Cursor・Gemini CLI・
OpenCode・Amp・Cline など多くのハーネスがプロジェクト内スキルを探す共通の
場所 (Agent Skills 規格) で、ディレクトリごとコピーすれば自動認識される。

| ハーネス | スキルの置き場所 | 規範本体 |
| --- | --- | --- |
| `.agents/skills/` 対応 (Codex, Cursor, Gemini CLI, OpenCode, Amp, Cline …) | そのまま自動認識 | `AGENTS.md` |
| Devin | `.agents/skills/*` を `.devin/skills/` にコピー | `AGENTS.md` |
| Claude Code | `.agents/skills/*` を `.claude/skills/` にコピー | `AGENTS.md` をそのまま読む (v2.1.277+ は CLAUDE.md なしなら AGENTS.md をネイティブ対応) |
| その他・未対応 | `AGENTS.md` 内の対応表から各 SKILL.md への経路を辿って運用 | `AGENTS.md` |

スキルをどこにも置かなくても AGENTS.md が常時読まれる規範本体として機能し、
対応表から手順ファイルへ辿れる。各 SKILL.md は frontmatter の description で
用途を宣言済み (対応ハーネスではそれが呼び出しのトリガーになる)。

## ディレクトリ構成 (作品ディレクトリ)

```
work.md              作品情報・創作憲章・執筆ポリシー・canon_revision
canon/facts.md       正典メモ (確度セクション別、[秘密] ラベルつき)
canon/history.md     正典の改訂履歴 (追記のみ)
entities.md          登場要素 (人物/場所/組織/物品/概念 + 別名)
knowledge.md         誰が何をいつ知ったか (知識イベント)
events.md            作中の出来事 (作中時間・参加者・結果。時系列の正本)
foreshadowing.md     伏線台帳 (張設場所・意味・回収予定・状態)
plan/tree.md         計画ツリー (話→シーン、状態つき)
contracts/<scene>.md Writing Contract (status: draft/approved/rejected)
scenes/<E>-<S>.md    本文 (先頭に rev 番号。旧版は scenes/history/ へ)
proposals/*.md       保留中の提案
changesets/*.md      変更セット (影響分析・承認・適用の記録)
reviews/*.md         レビュー findings と修正候補
research/*.md        実世界の事実調査の記録 (出典つき)
scratch/             行き場のないアイデア・断片メモ (正典ではない)
out/                 書き出した原稿 (export 先)
dialogue.md          対話ログ (決定の出所として追記)
```
