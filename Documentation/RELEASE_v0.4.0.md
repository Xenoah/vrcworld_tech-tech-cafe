# v0.4.0 — VECTOR FPV・時間帯・質感

技術者カフェ **The Commons — Compact Edition** に、独立した屋内FPVフロアと全時間帯の切替を追加しました。

## 今回の変更

- **VECTOR / Indoor FPV**：カフェから離れた36 × 26 × 8 mの専用フロア。カフェ入口のVECTOR、フィールドのRETURNで往復。
- 飛行エリア・操縦席4席・観戦席3席を分離。内寸3.2 × 3.0 mの8ゲート、3色の区間、番号、床矢印で順路を表示。
- **VRC+ Camera Droneを利用**。ワールド独自のドローンや操縦ギミックは追加していません。
- PCはPBR・金属感・弱い微細法線・ベイク反射、Questは軽量シェーダーを採用。移動時に遠い側の描画とカフェ音声を抑制。
- 控えめな器具グロー。PCはPost Processing導入時に弱いBloomを追加し、Reference Cameraへ接続。SOFT GLOW／LOW EMISSIONでローカル調整。
- **朝・昼・夕・夜、±1時間、CYCLE / HOLD**。24分で1日の連続変化、ホスト操作、時刻同期。既存の4活動モードと独立。

## ダウンロード

| ファイル | 内容 |
| --- | --- |
| `The_Commons_Compact_v0.4.0.unitypackage` | Unity導入用。PC/Questモデル・素材・音源・Editor・UdonSharp・シェーダー |
| `The_Commons_Compact_v0.4.0_Full.zip` | 制作データ一式。Unity用データ、編集可能なBlender、CAD、FPV仕様、プレビュー15枚、再生成ソース |
| `SHA256SUMS-v0.4.0.txt` | 配布ファイルのSHA-256 |
| `release-validation-v0.4.0.json` | ソースとアーカイブの一致検査結果と対象コミット |

Blenderを編集する場合はFull.zip全体を展開してください。

## Unityでの導入

1. VCCのWorlds / Built-inプロジェクトへUnityパッケージをインポート。制作基準はUnity 2022.3.22f1 / SDK 3.10.5です。実際の対応版はVCCの指定に従ってください。
2. PC用Bloomを使う場合はPackage Managerで `com.unity.postprocessing@3.4.0` を導入。未導入でも器具グローを使用できます。
3. **The Commons → Build PC World** または **Build Quest World** で新シーンを生成。
4. **Bake lighting**、VRChat SDKの **Build & Test** を実行。

## 検証範囲

形状35項目（8ゲートの開口・経路・往復ワープ着地点・ゾーン分離など）、C#構文12ファイル、Unityメタデータ、配布物の全ファイル一致を確認しています。ワールド全体はPC 159,884 tris、Quest 122,104 tris。FPV部分はPC 19,944 tris、Quest 14,331 trisです。

**Unity/Udon・シェーダーのコンパイル、ライトベイク、VRChat内の飛行・同期・両眼表示、PC/Quest実機FPSは未検証です。** 広さとゲート密度は余裕を持たせた初期設計です。実際の操縦感と実機のフレーム時間による最終調整が必要です。ライトマップと反射は静的1組で、時間帯ごとの再ベイクではありません。

本リリースは制作データです。生成済みUnityシーン・ビルド済みワールド・VRChat SDK本体は含みません。ワールドのアップロードとDronesの許可は所有者側で行ってください。

[変更の詳細](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.4.0/Documentation/CHANGES_v0.4.0_JA.md) / [Unity MCP引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.4.0/UNITY_MCP_HANDOFF.md) / [受入確認](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.4.0/Documentation/ACCEPTANCE_JA.md)
