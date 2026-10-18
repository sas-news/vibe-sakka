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
depends_on: []            # 依存宣言: この本文が依拠した正典/計画/シーンのID
mentions: []              # 本文中に言及された登場要素ID (検査時に記録)
```

---

(ここに本文。段落は空行で区切る。見出し・解説・メタ発言は書かない)
