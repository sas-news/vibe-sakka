# contracts/<scene>.md — Writing Contract

> 本文生成のゲート。ファイル名はシーンID (例: `contracts/1-2.md`)。
> **status: approved になるまで本文生成を開始しない。**

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

## 承認記録

- 提案: proposals/p-XXXX.md
- 承認: <日時・方法 (対話での明示承認)>
- 却下/差戻し履歴:
