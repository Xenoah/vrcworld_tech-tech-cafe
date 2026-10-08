# v0.6.1 — 安全ガラス・明るい室内・華やかな街並み

- **スポーン背後をガラスで閉鎖**。PC／Quest共通の連続BoxColliderを床から屋根まで設置し、南壁の5 m開口から落ちる問題に対応。
- **全体の明るさを改善**。カフェ照明1.65倍、FPV／カート1.35倍。入口・ラウンジ・上階に補助灯、夜間の環境色と床・壁の基準色を調整。
- **環境グローを強化**。PC Bloomは0.16→0.60。PC／Questの器具グローも強め、入口・テラスまで広げました。SOFT GLOW／LOW EMISSIONでローカル調整可能。
- **街並みを再設計**。24棟の段状高層建築、光る窓と冠部、屋上庭園、2本の空中回廊。Questでも外装の発光を保持。

## 更新の詳細

### 1. スポーン背後の落下対策

南壁中央の開口に6面の安全ガラス、真鍮の縦枠、目線下の細い表示線、足元灯を追加しました。床から屋根まで1つのBoxColliderで覆い、両側の壁・床・屋根と重ねて、ガラスの継目も通り抜けられない形状にしています。

| 項目 | 仕様 |
| --- | --- |
| 開口幅／衝突範囲 | 開口5 m、衝突は幅5.12 × 高さ9.8 × 厚さ0.24 m |
| 衝突中心 | Unity `(14, 4.8, 0.125)` m |
| PC／Quest | どちらも安全ガラスの描画・衝突を保持 |
| 外景 | ガラスは影を落とさず、不透明な遮蔽物としても扱わない設定 |

スポーン位置、既存のワープ着地点・床・階段・着席位置は維持しています。Questで東側の装飾窓を省略する処理から、安全ガラスを分離しました。

### 2. 室内・全時間帯の明るさ

カフェ既存灯の出力を1.65倍、FPV／カートを1.35倍にし、BlenderとUnity生成用マニフェストへ反映しました。倍率は光源の設定値で、実機で測定した明るさではありません。

- 入口・中央ラウンジ・上階南通路に、ベイク用の補助灯を3灯追加。
- 東・北側にコーブ照明を配置し、床石・左官・木・鋼材の基準色を調整。
- 夜間環境光と昼夜の素材補助光を増やし、暗い面の見やすさを改善。
- カートの青紫色は維持し、路面補助光と固定Tintを明るく調整。
- Unityのベイク光強度上限を6→10に変更。プレビューの露出は従来値を維持。

### 3. 環境グロー

| 設定 | v0.6.0 | v0.6.1 |
| --- | ---: | ---: |
| PC Bloom intensity | 0.16 | 0.60 |
| Bloom threshold | 1.15 | 1.05 |
| Bloom soft knee / diffusion | 0.55 / 4 | 0.60 / 5 |
| PC 器具グロー 暖色／寒色 | 0.035 / 0.030 | 0.090 / 0.075 |
| Quest 器具グロー 暖色／寒色 | 0.028 / 0.023 | 0.060 / 0.050 |

器具グローの範囲を広げ、入口・テラスにも追加。PCの画面全体のBloomにはPost Processing Stack v2が必要です。Questは器具グローと発光材を使用し、SOFT GLOW／LOW EMISSIONは引き続きプレイヤーごとに調整できます。

### 4. 周辺建築

単純な30棟を、各3段のセットバックを持つ24棟へ変更しました。石の柱と水平帯、金属感のある不透明ガラス外装、暖色・寒色の窓、発光する冠部、屋上庭園、2本の空中回廊を配置。東テラスと南側のスポーンガラスから見える街並みを整えました。

高さは基部から22〜62 m。棟ごとの配置・高さは固定し、再生成しても変わりません。材質ごとに6メッシュへまとめ、追加テクスチャ・リアルタイム光源・衝突形状は使っていません。街並みは背景用で、屋上・空中回廊への歩行ルートやワープはありません。

## 収録ワールドの構成

| エリア | 仕様・用途 |
| --- | --- |
| THE COMMONS | 28 × 18 m、2階建て。カフェ・バー・発表ステージ・DJブース・静かな会話室・東テラス |
| VECTOR | 36 × 26 m、高さ8 m。8ゲート、操縦席・観戦席を備える独立FPVフロア |
| APEX / NEON SWITCHYARD | 148 × 160 m、全長1,268.83 m、幅5.2 m、34コーナー、路面高0.35／4.55／8.75 mの3層屋内カート |
| 移動・外部システム | カフェからFPV／カートへ往復ワープ。ドローンはVRC+、カート車両は所有者側でCVS2を導入 |

今回、FPV・カートのコース形状やワープ先は変更していません。CVS2車両・VRC+ドローン・AudioLink本体は同梱しません。

## スクリーンショット

**この版の実モデルをBlender 4.5.3 / Cyclesでレンダリングしています。Unity／VRChatで撮影した画像ではありません。** カート全景のみ屋根・手前2面の壁・トラスを非表示にしたカットアウェイです。

### カフェ全景 — 光源・素材色・環境光の調整

![明るくなったカフェ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/01_Entrance_160cm.png)

### スポーン後方 — ガラス・真鍮枠・足元灯

![スポーン背後の安全ガラス](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/21_Spawn_Glass.png)

### 上階 — 補助灯・コーブ照明・器具グロー

![上階とグロー](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/04_Mezzanine_160cm.png)

### 東テラス — 窓越しに見える街並み

![テラスから街並み](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/22_Horizon_Skyline.png)

### 周辺建築 — 段状外観・光る冠部・屋上庭園

![周辺建築](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/23_City_Architecture.png)

### VECTOR — FPVフロアの照明

![FPVの照明](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/11_FPV_Course.png)

### APEX — 明るくした3層コースの全景

![カート全景](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.1/16_Kart_Overview.png)

## ダウンロード・導入

| 添付ファイル | 内容 |
| --- | --- |
| `The_Commons_Compact_v0.6.1.unitypackage` | Unity導入用。PC／Questモデル・素材・シーン生成Editor・UdonSharp・シェーダー |
| `The_Commons_Compact_v0.6.1_Full.zip` | 編集用Blender・FBX・glTF・CAD・設計資料・全ソース・プレビュー画像 |
| PNG 7枚 | 上記の更新後モデル画像を原寸で添付 |
| `SHA256SUMS-v0.6.1.txt` | 2種類の配布物・検証JSON・PNG 7枚のSHA-256 |
| `release-validation-v0.6.1.json` | 公開元コミット、配布内容の照合結果、画像・配布物のサイズとハッシュ |

1. VCCのWorldsプロジェクトへUnityパッケージをインポート。SDK／UdonSharpはVCC側で導入します。
2. PC Bloomを利用する場合はPost Processing Stack v2を導入します。未導入でも器具グローは使用できます。
3. **The Commons → Build PC World / Build Quest World** で新しいシーンを生成。
4. **The Commons → Bake lighting** で再ベイクし、必要なCVS2／AudioLink等を所有者側で設定。
5. VRChat SDKのBuild & Testで、後方ガラス・各ワープ・昼夜の明るさ・グローの調整をPC／Questそれぞれ確認してください。

**既存の生成シーンには自動適用されません。** CVS2等を追加した古いシーンは残し、新しい生成シーンへ必要な設定を移してください。制作基準はUnity 2022.3.22f1／SDK 3.10.5／Built-in Render Pipelineで、現在の対応版はVCC・公式指定に従ってください。

## 検証範囲

**共通形状46項目＋カート15項目、計61項目すべて合格。** スポーン後方1,650境界サンプル、スポーンの空間、PC／Questガラス、街並み予算、既存の床・階段・FPV・カートを検査しています。C#12ファイルの構文検査、配布物と公開ソースの全バイト一致、画像・チェックサムも確認しています。

| 書き出し形状 | PC | Quest |
| --- | ---: | ---: |
| ワールド全体 | 318,781 tris／193メッシュ | 263,899 tris／185メッシュ |
| うち街並み | 30,236 tris／6メッシュ | 18,804 tris／6メッシュ |
| 街並みの上限設定 | 36,000 tris | 28,000 tris |

メッシュ数は書き出し単位で、Unity実機のDraw Call数とは異なります。

**Unity/Udon・シェーダーコンパイル、ライトベイク、VRChat実歩行／両眼表示／FPSは未検証。** 制作データの公開であり、VRChatへのアップロードではありません。CVS2車両・VRC+ドローンのシステムは同梱しません。v0.6.0図面集は過去資料として同梱し、最新ガラスはv061のCAD重ね図、外観は今回の画像で確認できます。

[変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.6.1/Documentation/CHANGES_v0.6.1_JA.md) / [現在の詳細仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.6.1/README.md) / [Unityへの引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.6.1/UNITY_MCP_HANDOFF.md)
