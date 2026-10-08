# THE COMMONS — Compact Edition

**v0.8.0 / 詳細モデル・Unity構築データ / 2026-10-08**

28×18m、1F +0.000m、2F +4.800m、屋根基準 +9.600mの制作データです。Blenderで編集できる実形状、FBX、glTF、生成テクスチャ、VRChat SDK用のシーン構築ツールとUdonSharpソースを含みます。

**Unity Editor / VRChatクライアントは制作環境になかったため、Unityでのコンパイル・ライトベイク・Build & Test・Quest実機・複数人通信は未検証です。公開済みワールドやビルド済み `.vrcw` ではありません。** Blenderレンダーと幾何検査の結果は `Preview/` と `Documentation/validation_report.json` に収録しています。

Unity MCPからの取得・構築は [UNITY_MCP_HANDOFF.md](UNITY_MCP_HANDOFF.md)、今回の修正は [CHANGES_v0.8.0_JA.md](Documentation/CHANGES_v0.8.0_JA.md) を参照してください。

**詳細仕様・寸法付き平面図・実モデルのデザインシートは [README](README.md) と [A3図面集PDF](Documentation/Design/The_Commons_v0.6.0_Design_Atlas.pdf) に整理しています。モデル版はv0.8.0、図面集はv0.6.0の過去資料です（カートの図面・デザインシートは旧コース）。最新のカートは `Preview/Design/09_Kart_Plan_v08.png` とv0.8.0の画像、ガラス・照明・街並みはv0.6.1の画像を参照してください。**

## v0.8.0の変更 — いろは坂型の複合7連ヘアピン・カルーセル・ジャンプ

APEX / NEON SWITCHYARDの走路だけを作り直しました。v0.7.0のS字が続く「うねり」を減らし、**全長1,141.23 m・26コーナー・3層** のコースにしています。モンツァ型のシケイン、高速コーナー、2か所のジャンプ、前版から引き継いだバンク付きの360°登坂カルーセル、ノルトシュライフェ型の複合区間、スパ型ヘアピン、SFC『スーパーマリオカート』のクッパ城のような直角（形のみ）、ラグナ・セカ型の下りのコークスクリュー、鈴鹿のような立体交差、日光いろは坂の地図を参考にした複合7連ヘアピンの下りを、縮小・左右反転して取り入れました。どのコース・道路・ゲームも再現していません。

![v0.8.0のカート全景（屋根・手前2壁・トラス非表示）](Preview/16_Kart_Overview.png)

- 中心半径6.0〜20 m、最大勾配11.92%（コークスクリュー）、カルーセルのバンク最大8°、立体交差3か所（最小クリアランス3.37 m）、ジャンプ2か所（高さ0.75 m・0.5 m）。
- 層の接続は4区間（カルーセル74.9 m、登坂56.9 m、コークスクリュー52.4 m、いろは坂494.8 m）。7連ヘアピンは平底の2頂点・涙滴形・半径が縮む・S字進入・2段・半径が広がる・2段のV字の7種類の複合ヘアピンで、斜めの脚の長さと向きが毎回変わります。
- 路面にT1〜T26の番号とジャンプ手前の「JUMP」。進行矢印はスロープ・バンク面に沿わせています。
- メインストレートの路面サンプルが変わったため、CVS2配置ガイドがX方向に最大0.67 m移動しました。**車両は新しいガイドに合わせて置き直してください。**
- **カフェ・FPV・街並み・カート建屋は変更していません。** Unity用メッシュのカート以外の記録はv0.7.0とバイト一致です。

コーナー一覧と参考にしたコーナーは [CHANGES_v0.8.0_JA.md](Documentation/CHANGES_v0.8.0_JA.md)、詳細仕様は [README](README.md) を参照してください。**新しいシーンの生成とライトの再ベイクが必要です。**

## v0.7.0の変更（前版）

33コーナーのテクニカルコースへ改修した版です。[CHANGES_v0.7.0_JA.md](Documentation/CHANGES_v0.7.0_JA.md) を参照してください。走路はv0.8.0で作り直しています。

## v0.6.1の変更


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


### v0.6.1の実モデル画像

v0.6.1のRelease画像7枚のうち、カフェ・FPV・街並みの6枚です（Blender 4.5.3 / Cycles、Unity／VRChatの実機画像ではありません）。カート全景はv0.8.0のコースに更新しました。

![明るくなったカフェ全景](Preview/01_Entrance_160cm.png)

![上階と環境グロー](Preview/04_Mezzanine_160cm.png)

![スポーン背後の落下防止ガラス](Preview/21_Spawn_Glass.png)

![テラスから見える街並み](Preview/22_Horizon_Skyline.png)

![24棟の周辺建築と冠部・屋上庭園](Preview/23_City_Architecture.png)

![明るくなったFPVフロア](Preview/11_FPV_Course.png)


**再生成・再ベイクが必要です。** 既存の生成シーンは残し、新しいシーンへ必要な設定を移してください。

## 最短の導入

1. VRChat Creator Companionで **Worldsプロジェクト** を作成します。制作基準は **Unity 2022.3.22f1**。Built-in Render Pipelineを使います。SDK / UdonSharpはVCCの導入分を利用します。
2. `Unity/Assets/TheCommons` を、作成したプロジェクトの `Assets` へフォルダーごとコピーします。Release v0.8.0のUnityパッケージをインポートする方法でも導入できます。
3. C#のインポートが完了したら、Unity上部メニュー **The Commons → Build PC World** を実行します。最初にUdonSharpをコンパイルし、メッシュ・マテリアル・コライダー・操作パネル・スポーン・照明を配置します。
4. シーンは `Assets/TheCommons/Generated/PC_日時/TheCommons.unity` に保存されます。既存シーンは上書きしません。
5. **The Commons → Bake lighting** でライトマップを生成します。PCはPBRと補助光、Questは頂点の環境色をベイク前の補助表示に使います。
6. VRChat SDK Control Panelで **Build & Test**。初回は入口、東階段、西階段脇ポータル、Quiet Room、モード切替を確認してください。
7. モバイル版は **Build Quest World** で別シーンを作り、Androidへプラットフォームを切り替えて同様にベイク・テストします。SDKで同じワールドとして管理する場合のBlueprintは所有者側で設定してください。

元資料が指定するCAD/JSONの不整合は、`Documentation/CAD_CHANGES_JA.md` に明示しました。採用した補完箇所は `CAD/The_Commons_Implementation_Overlay_v080.dxf` で確認できます。元CADは `SourceDesign/CAD/` にそのまま残しています。

## 入っているもの

| 場所 | 内容 |
|---|---|
| `Blender/The_Commons_Compact.blend` | 部材ごとに編集可能な建築・家具・AV・植栽・街並み。テクスチャとフォントは同梱フォルダーを相対参照 |
| `Blender/build_world.py` | 寸法を追跡できる再生成用ソース |
| `Unity/Assets/TheCommons/Models/` | PC/Quest FBXと、向き・単位を固定したUnity用メッシュデータ |
| `Unity/Assets/TheCommons/Scripts/` | 共有状態、発表、同期動画、移動、着席、音量ゾーン、ローカル快適設定 |
| `Unity/Assets/TheCommons/Textures/` | 建築素材6種＋専用印刷アトラス3種の生成原本 |
| `Unity/Assets/TheCommons/Media/` | 差し替え可能な4枚のスライド・6枚のポスター |
| `Unity/Assets/TheCommons/Audio/` | オリジナルの環境音・アンビエント・96 BPMのDJループ |
| `Preview/` | カフェ・小物・FPV・時間帯・カートの設計プレビュー（v0.8.0のカート画像11枚と平面図、v0.6.1の画像6枚を含む）、外部参照形式のglTFモデル |
| `SourceDesign/` | 元仕様、元CAD、元スケジュール、参考画像、添付PDF |

## モデルの細部

L字バーカウンター、木製リブ、真鍮の足掛け、11脚のスツール、バックバー3段のボトル、ラベル、棚下灯、エスプレッソマシン、グラインダー、カップとソーサー、テーブル灯、座面と背のクッション、脚、柱脚プレートとボルト、手すりとケーブル、段鼻灯、吊り下げロッド、2デッキ・4チャンネル一体型DJコントローラー、ジョグ、パッド、フェーダー、ノブ、AVラック、展示台、植木鉢と立体葉、本棚、外景を実形状で作っています。

PCには金属度・粗さ・弱い微細法線を使うPBR、Questには軽量な明暗とハイライトを設定しています。Blenderの画像はCyclesによる設計確認で、Unityシェーダーの描画結果とは完全一致しません。

## 操作と切り替え

| モード | 中央家具 | 発表 | 音と光 |
|---|---|---|---|
| Lounge | 4クラスタの家具 | スライド表示 | 暖色中心、低いBGM |
| Academic | 24席 | 15分/5分タイマー、Q&A、固定画面ポインター | BGM低下、ホログラム停止 |
| DJ / Live | 中央家具を非表示 | 同期動画を利用可能 | DJループ、DJ表示、逃げ場は維持 |
| Quiet Night | ラウンジ家具 | スライド表示 | 発光低減、静かなBGM |

- 初期状態はLounge。共有操作は初期設定でインスタンス所有者またはMasterに限定します。
- 入口右側とAV側にモード操作。発表者用パネルはステージ左側。
- 入口左側の動き低減・発光低減・DJ演出はローカル設定。動き低減は初期ON。
- 発表タイマーはサーバー時刻で共有します。終了するとLoungeへ戻ります。
- 上下階ポータルを入口側と西階段脇に設けています。
- 椅子は明示的なInteractで着席。通過するだけでは着席しません。
- Quiet Roomの内外でBGM/動画音量をローカルに減衰し、相手プレイヤーの距離・ゲインも調整します。防音やプライバシーを保証する仕組みではありません。
- PCの小型鏡はローカル、初期OFF。SDKの鏡シェーダーが見つからない場合は生成を省略し、Unity Consoleに表示します。Questには作りません。

## 動画とAudioLink

AV室のURL欄にHTTPS動画URLを入れ、LOAD URLを押します。SDKのVRCUnityVideoPlayerを利用し、主画面と上階補助画面で同じRenderTextureを表示します。URL・再生開始時刻・停止を共有し、途中参加者は再生時刻を補正します。ライブ配信など長さが確定しない媒体はシーク補正しません。URLの対応状況と許可設定はVRChat側に依存します。配信サービス別の再生は未検証です。

DJシェーダーはAudioLinkのグローバル `_AudioTexture` の4バンドを読みます。**AudioLink本体は同梱していません。** 利用する場合は公式AudioLinkをVCC経由で追加し、そのPrefabのAudioSourceを `AUD_Original DJ loop` または動画音源に接続してください。未導入時にも固定バー表示と低速演出で動作し、コンパイル時のAudioLink依存はありません。

## 素材と差し替え

- 木、左官、暗色テラゾー、黒皮鋼、真鍮、青緑の織布を個別に画像生成しました。
- アルベド画像は生成原本のまま。建築の6素材は **Mirror（鏡像反復）** を使い、境界の段差を防ぎます。生画像の左右・上下端が通常のRepeatで完全一致するとは保証していません。他の制作ソフトでもMirrorに設定してください。
- 専用アトラスは **Clamp**。DJ操作面、6種の酒ラベル、エスプレッソ機、コーヒー袋、本、AVラックに個別UVで割り当てています。DJ機材の個別操作部は装飾です。
- PCのインポート上限は共通素材1024、モバイルは512。法線・金属度・粗さは形状とシェーダーの値で整理しています。
- スライドは `Media/slide_0.png`〜`slide_3.png`、ポスターは `poster_0.png`〜`poster_5.png` を交換してからシーンを再構築できます。作成済みシーンは生成先のマテリアルのテクスチャを交換できます。
- 実際のスライド面はUnityで別の正規UV面を追加します。Blenderの文字入りスクリーンは確認用の静的表示です。
- 再生成時は `build_world.py → export_world.py → prepare_media.py --manifest-only → prepare_repository_assets.py → validate_world.py → validate_kart.py → package_release.py --metadata-only` の順。v0.8.0の画像は `render_kart_views.py` の11視点、カート平面図は `build_kart_plan.py`（numpy／Pillow）です。カフェ・FPV・街並みの画像は `render_atmosphere_views.py` の6枚（v0.6.1）を継続しています。C#構文検査は `validate_csharp.py`（tree-sitter / tree-sitter-c-sharpが必要）。画像・資料を確定してから `package_release.py → verify_release.py` で配布物を作成・照合します。Blender 4.5 LTS（v0.7.0以降はPyPIの `bpy` 4.5.14で生成）、Python側の numpy/scipy/Pillow/ezdxf/shapely が必要です。

## 検証の区分

実行済み: Blenderでモデル生成・保存・開き直し、v0.8.0のカート実モデル画像11枚とv0.6.1のカフェ・FPV・街並みの実モデル画像6枚（旧版の4時間帯画像は参考資料）、メッシュの有限数/インデックス/向き/データ末尾、外形/階高/ステージ/画面寸法、上階接続の平面検査、共通形状46項目＋カート18項目、カート以外のUnity用メッシュ記録とv0.7.0のバイト一致、C#構文12ファイル、SDK 3.10.5の公開メンバー照合。

未実行: Unity/Udonコンパイル、シェーダーコンパイル、Unityライトマップ、VRChat Build & Test、アップロード、複数人同期、視線追従やVR両眼、QuestのFPS/メモリ/ダウンロード容量測定。

**三角形数は書き出した全景の実測値です。FPSやSetPassの実測値ではありません。** バッチ数はライトマップ分割、鏡、ステレオ方式などで変化します。

西階段は48.14°です。正本の幅と奥行きに合わせた外観を残し、同位置のポータルを確実な代替動線にしています。VRChatのコントローラーで登坂できるかは実機確認が必要です。通常の主動線は勾配36.44°の東階段を想定します。

## 参照

- Unity指定版: https://creators.vrchat.com/sdk/upgrade/current-unity-version/
- 共有変数: https://creators.vrchat.com/worlds/udon/networking/variables/
- UdonSharp Editor API: https://udonsharp.docs.vrchat.com/editor-scripting/
- プレイヤー音声: https://creators.vrchat.com/worlds/udon/players/player-audio/
- 動画: https://creators.vrchat.com/worlds/udon/video-players/
- AudioLink: https://github.com/llealloo/audiolink

Git登録用の `.blend` は圧縮保存し、画像・フォントを相対パスで参照します。必ずフォルダー構造ごと取得してください。`Blender/prepare_repository_assets.py` で同じ整理を再実行できます。パッケージ整理時には形状とPNGの内容を保持します。

同梱DejaVuフォントのライセンスは `Documentation/DejaVu_Font_License.txt`。VRChat SDKとAudioLink本体は配布物に含めていません。


## v0.4.0追加更新（2026-10-07）

現在のmainは独立FPVフロア、PBR／Quest用軽量シェーダー、v0.6.1で強化したグロー、全時間帯の同期切替を含みます。仕様・モデル数・追加画像・検証範囲は [CHANGES_v0.4.0_JA.md](Documentation/CHANGES_v0.4.0_JA.md) を参照してください。[Release v0.4.0](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/tag/v0.4.0)にUnityパッケージと制作データ一式を収録しています。

## v0.6.0 屋内ネオンカート

**v0.7.0・v0.8.0で走路を改修しました。以下はv0.6.0時点の旧コースの説明です。** 建屋・ピットの構成・照明の考え方は継続しています。

**APEX / NEON SWITCHYARD** は148 × 160 m、総延長1,268.83 m、幅5.2 m、高さ0.35／4.55／8.75 mの3層コースです。34の円弧コーナー、連続する切り返し、橋下と4本の緩和勾配を組み合わせました。写真は室内の密度と青・紫の光の参考に用い、走路は独自設計です。従来の広い屋外型コースを置き換えています。

屋根・外壁・鉄骨トラスを持つ屋内モデル。低いラバーガードに青／シアンの上端・側面LED、ピンク／白のパネル、紫の壁面照明、黒い光沢路面を配置。室内の色・発光は外の時間帯に左右されない設定です。Unityではライトベイク後に走行目線の明るさを調整してください。

カフェとの往復ワープ、6台分の空の配置ガイド、ピット・屋根付き観戦席・時間パネルを含みます。CVS2本体・車両・車両操作・レース計測は含みません。`KART_ExternalVehicleAnchors/CVS2_Bay_01`〜`06` を目安に配置し、[導入メモ](Documentation/CVS2_INTEGRATION_JA.md)に従って旋回・車高・速度を実車両で調整してください。

[Release v0.6.0](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/tag/v0.6.0)に配布物と実モデル画像5枚を収録。画像はBlender 4.5.3 / Cyclesで、Unity／VRChat撮影ではありません。全景だけはレイアウトを見せるため屋根・手前2面の壁・トラスを非表示にしています。走行・橋下・ピット・上層の4枚は閉じた屋内モデルのままです。Unity／CVS2実走は未検証です。
