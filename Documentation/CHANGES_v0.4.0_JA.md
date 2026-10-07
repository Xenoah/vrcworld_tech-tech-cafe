# v0.4.0 — VECTOR FPV・時間帯・質感

2026-10-07。制作データ向け更新です。Release v0.4.0にUnityパッケージと制作データ一式を収録しています。

![VECTORの飛行エリア](../Preview/11_FPV_Course.png)

## 独立した屋内FPVフロア

カフェの西、Blender座標の原点 `(-64, 0, 0)` に36 × 26 m、天井高8 mの独立フロアを配置。飛行エリアは34 × 18.8 m（639.2 m²）。操縦席4席、観戦席3席を南側に分け、境界の柵と2 mの人用通路を設けています。カフェ入口のVECTORボタンとフィールドのRETURNボタンで往復できます。

8基のゲートは内寸3.2 × 3.0 m。シアン・アンバー・ライムの区間色、番号、床の立体矢印で順路を示します。ゲートの穴を塞ぐコライダーは使わず、枠・支持材に個別のコライダーを設定。床矢印は床面から離して配置しました。中央には低い練習用着地台があります。

VRC+ Camera Droneを使う前提です。独自ドローン、操縦物理、レース計時は追加していません。ワールド・インスタンス側でDronesを許可して、クライアントで確認してください。

広さと密度は余裕のある初期案です。半径0.16 mの仮想球によるゲート開口と中心経路の検査は通過していますが、実際のドローン形状・操縦感を保証する検査ではありません。操縦感とPC／Quest実機のフレーム時間を見て調整します。

| 対象 | PC 三角形／メッシュ | Quest 三角形／メッシュ |
|---|---:|---:|
| ワールド全体 | 159,884 / 151 | 122,104 / 141 |
| FPV部分 | 19,944 / 22 | 14,331 / 21 |

エリア移動に合わせて遠い側のRendererをローカルで非表示にします。コライダーとUdonは保持するので、着地点の床は常に存在します。両エリアのアセットはメモリに残ります。音楽・動画音声もフィールドでは抑制します。

## シェーダーと控えめなグロー

| 項目 | PC | Quest |
|---|---|---|
| 建築・家具 | StandardベースのPBR。粗さ、金属度、建築テクスチャの弱い微細法線 | 軽量な明暗・ハイライト、ベイク光 |
| ガラス | Fresnelとベイク済みReflection Probe | ガラスの描画を省略。コライダーは保持 |
| 空間の発光 | 少数の器具グローカード＋任意の弱いBloom | 少数の器具グローカード |
| 太陽 | 1灯のRealtime Directional Light | シェーダー側の色・方向による表現 |

PPS v2が導入済みならシーン生成時にPC用Bloom Volume、初期化済みPostProcessLayer付きReference Cameraを作成してScene Descriptorへ接続します（強度0.16、閾値1.15、Fast Mode）。未導入なら警告を出し、器具グローだけで生成できます。QuestではPost Processingを使用しません。[VRChat公式の制限](https://creators.vrchat.com/platforms/android/quest-content-limitations/)。SOFT GLOWはローカル操作で切替可能。LOW EMISSIONでもグローを停止します。

木、左官、テラゾー、鋼、真鍮、織布と、DJ・酒ラベル・小物の既存9画像を再利用しています。新しい高解像度画像やGrabPassは追加していません。

## 全時間帯

カフェ入口とFPV側のパネルからDAWN / DAY / DUSK / NIGHT、±1時間、CYCLE / HOLDを操作できます。連続サイクルは24分で1日。空、太陽、霧、環境色、素材の補助光と発光量を0〜24時で補間します。時刻と起点をネットワーク同期し、既存のホスト操作権限を使います。活動モード4種とは独立しています。

ライトマップ・Reflection Probeは1組の静的ベイクです。時刻別のベイク切り替えやRealtime GIではありません。時間帯の見た目とベイクのバランスはUnityで確認してください。

Preview/12_Dawn.png〜15_Night.pngはBlenderによる設計プレビューです。UnityシェーダーやVRChatクライアントの実測画像ではありません。ブラウザ版もThree.jsによる近似表示です。

## 編集・検証

編集用のBlenderシーン、独立したFPVのメッシュ・UV・文字・ライトを保持する `Blender/FPV_Field_Module.json`、配置基準 `SourceDesign/fpv_field.json` を収録。`build_world.py` はこのモジュールからFPVを復元します。レイアウト変更時はモジュール内の形状・コライダー・配置基準を合わせて更新してください。仕様だけ変更した場合は再生成を停止して不一致を知らせます。

形状検査35項目とC#構文12ファイルを確認。別管理のブラウザ側では前工程に10項目を確認しました。実機FPS、Unity/Udon・シェーダーのコンパイル、ベイク、VRChat両眼表示、途中参加・複数人同期、VRC+ドローンでの飛行は未検証です。受入手順は[ACCEPTANCE_JA.md](ACCEPTANCE_JA.md)にまとめています。

## 中断作業からの最終修正

- PC用BloomをReference Cameraへ接続し、HDRとVolume用レイヤーを設定。参照カメラ自身の描画は無効にし、余分なカメラ描画を発生させません。PPS未導入時の器具グローは維持します。
- PC・Quest双方で素材の発光値を上限3に制限。
- FPV・時間帯シェーダーの必須ファイルを配布検査へ追加。ソースとUnityパッケージ・ZIPの全ファイル一致を検査してからリリースします。

参照: [VRChat Scene Descriptor](https://creators.vrchat.com/worlds/components/vrc_scenedescriptor/) / [Unity PostProcessLayer](https://github.com/Unity-Technologies/PostProcessing/blob/v2/PostProcessing/Runtime/PostProcessLayer.cs)
