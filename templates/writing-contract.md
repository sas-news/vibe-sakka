# contracts/<scene>.md — Writing Contract

> 本文生成のゲート。ファイル名はシーンID (例: `contracts/1-2.md`)。
> **status: approved になるまで本文生成を開始しない。**
> 正典上の境界 (下記「契約内容」) に加え、**面白さの設計 (craft 欄)** を
> 持つ。craft 欄の埋め方は `.agents/skills/scene-craft/SKILL.md`。

```yaml
scene: "1-2"           # シーンID (plan/tree.md と一致)
status: draft          # draft | approved | rejected
base_revision: 3       # 作成時点の canon_revision (競合検出用)
scene_type: real       # real | dream | memory | hypothetical | other
                     # (実時間を進めない場面は状態違反検査の対象外)
```

## 契約内容

> **契約は「このシーンで動かせない境界」だけを定めてよい。**
> 全部埋める必要はない — 探索的なシーンなら role・pov・forbidden だけ
> 決めて残りを柔軟に開けるのは正当な契約。逆に、固定すべき要素を
> 曖昧にしないこと。

- **role** — この話・シーンが物語に果たす役割:
- **situation** — 開始時点の状況・時間・場所:
- **pov** — 視点人物・視点の方針:
- **participants** — 参加する人物 (ent-ID):
- **knowledge_notes** — 視点人物が知っている/知らないこと:
  (秘密の正典を扱う場合、ここに宣言 or knowledge.md に記録が必須)
- **required_events** — 起こすべき出来事:
  - (1行1イベント)
- **forbidden** — 避けるべき出来事・開示してはいけない情報:
  - (1行1項目)
- **agency** — 誰が・何を選ぶ/決めるか (主体性ビート。受動的なシーンを
  計画段で可視化する):
- **state_changes** — 終了時点で変化する状態:
- **end_state** — シーンの終着点1行 (これを越えたらオーバーラン):
- **connections** — 上位アークとのつながり・前後シーンへの因果的接続:
- **style** — 文体・視点・テンポなどの表現方針:
- **fixed_vs_flexible** — どの要素が固定で、どの要素が柔軟か:

## craft 欄 (面白さの設計)

> 本文生成の入力。`scene_job` / `dramatic_question` / `want` / `obstacle` /
> `turn` / `cost` が空のまま approved にしない。空なら
> `.agents/skills/scene-craft/SKILL.md` に戻って設計する。
> 記入例: `turn: ソラは「開く」を自慢するつもりで来て、自分が最後の一人だと知る。`

- **scene_job** — この場面が物語で果たす仕事 (1文):
- **dramatic_question** — この場面の問い (答えを知りたくなる形):
- **want** — 視点人物が今この場面で欲しいもの (具体的に):
- **obstacle** — それを阻むもの (人物・規則・時間・自己):
- **turn** — 場面で起きる転 (予想→裏切り→納得):
- **cost** — 転・選択が払う代償 (失うもの):
- **entry** — 入り方 (遅く入る。直前の説明を削る):
- **exit** — 出方 (早く出る。余韻を残す位置):
- **button** — 場面を閉じる一行 (余韻・引き):
- **detonator** — 予想を裏切る強いビート (話に最低1つ):
- **concrete_details** — 五感で書く具体物3つ:
- **subtext** — 台詞の下で本当にやり取りされていること:
- **skip_test** — この場面を飛ばしたら物語が壊れるか (壊れないなら削る/統合):
- **pov_filter** — 視点人物の認知フィルター (何に気づき、何を見落とすか):
- **voice_notes** — 声の指示 (`craft/voice.md` との対応):
- **prose_floor** — 本文の下限字数 (下限であって目標ではない。水増し禁止):
- **prohibit_summary** — true 固定 (要約体・ビート見出し・あらすじの清書を禁止):

## 承認記録

- 提案: proposals/p-XXXX.md
- 承認: <日時・方法 (対話での明示承認)>
- 却下/差戻し履歴:
