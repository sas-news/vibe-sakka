# scenes/<E>-<S>.md — シーン本文

> ファイル名はシーンID
> (例: `scenes/1-2.md` = 第1話シーン2)。本文はこのファイルが正本。
> 書き換えのたびに rev を +1 し、旧本文は `scenes/history/<E>-<S>/r<N>.md`
> へ退避 (git 管理下なら git 履歴でもよい)。

```yaml
scene: "1-2"
title: ""
rev: 1                    # 本文リビジョン番号
source: ai                # ai | manual_edit (人間の直接編集は manual_edit)
contract: contracts/1-2.md  # 生成に使った承認済み契約
change_set: null          # この rev を作った変更セット (あれば)
polished: false
polish_review: null       # 推敲記録: reviews/polish-<date>.md (未実施なら null)
depends_on: []            # 依存宣言: この本文が依拠した正典/計画/シーンのID
mentions: []              # 本文中に言及された登場要素ID (検査時に記録)
```

`polished` の行には行末コメントを付けない (`release_gate.py` が行全体を一致で
読む)。`polished: true` は `.agents/skills/polish/SKILL.md` の全手順を通し、
`reviews/polish-<date>.md` に記録を残したときだけ立てる。write-scene の
revise・change-set の rewrite_scene・手編集で本文が変わったら false に戻す。
`python3 tools/release_gate.py` は `polished: true` を検査する。

記入例: `polished: false` で write-scene が保存 → polish 後に
`polished: true` / `polish_review: reviews/polish-20261117.md` に更新する。

---

(ここに本文。段落は空行で区切る。見出し・解説・メタ発言は書かない)
