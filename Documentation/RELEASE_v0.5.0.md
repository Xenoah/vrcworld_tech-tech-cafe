# v0.5.0 — APEX 3層カートコース

技術者カフェ **The Commons — Compact Edition** に、独立したレーシングカートフロアを追加しました。

- **320 × 300 m／約1.40 km**。高さ0.35・3.95・7.55 mの3レイヤーを橋と連続スロープで接続。
- 走行幅8 m、3か所の立体交差、5か所のS字。高さ別の色、縁石、矢印、スタートラインでコースを表示。
- カフェとの往復ワープ。6台分の空の配置ガイド、ピット、屋根付き観戦席。
- **CVS2を別途利用**。車両モデル・操縦・車両同期・レース管理の実装は含みません。
- 観戦側にも全時間帯の操作パネル。3エリアの建築描画・音声を切替え、広域用に霧と遠方クリップを調整。
- **今後は毎回スクリーンショットを添付**。今回の4枚をRelease Assetsとチェックサム検査の対象にしています。

## スクリーンショット

このリリースの実モデルを **Blender 4.5.3 / Cycles** でレンダリングしたプレビューです。Unity／VRChat内の実機撮影ではありません。車両は含まれません。

![3層コース全景](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.5.0/16_Kart_Overview.png)

![橋と立体交差](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.5.0/17_Kart_Overpass.png)

![低層のドライバー視点](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.5.0/18_Kart_Driver.png)

![ピットと観戦席](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.5.0/19_Kart_Pits.png)

## ダウンロード

| ファイル | 内容 |
| --- | --- |
| `The_Commons_Compact_v0.5.0.unitypackage` | PC／Questモデル・素材・Editor・UdonSharp・シェーダー |
| `The_Commons_Compact_v0.5.0_Full.zip` | Unityデータ、編集用Blender、CAD、仕様、画像19枚、再生成ソース |
| `16_Kart_Overview.png`〜`19_Kart_Pits.png` | 今回のスクリーンショット4枚 |
| `SHA256SUMS-v0.5.0.txt` | 配布物・画像のSHA-256 |
| `release-validation-v0.5.0.json` | ソースと配布物の一致検査、画像一覧、対象コミット |

VCCのWorlds / Built-inプロジェクトにUnityパッケージを導入し、**The Commons → Build PC World** または **Build Quest World** で新シーンを生成。CVS2車両はその後、`KART_ExternalVehicleAnchors/CVS2_Bay_01`〜`06` を目安に配置します。ライトベイクとVRChat SDKのBuild & Testを行ってください。Blender編集時はFull.zip全体を展開します。

## 検証範囲

従来形状35項目＋カート15項目、C#構文12ファイル、メタデータ、配布物の全バイト一致と画像添付を確認。橋下最小6.75 m、最大勾配8.95%、最小中心旋回半径14.73 m。全体はPC 231,297 tris／Quest 193,517 tris、カート部分は共通71,413 trisです。

**Unity/Udon・シェーダーのコンパイル、ライトベイク、CVS2走行・同期、VRChat内の表示、PC／Quest実機FPSは未検証です。** 制作データのリリースであり、生成済みシーン・ビルド済みワールドは含みません。車両の調整とワールドのアップロードは所有者側で行ってください。

[変更詳細](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.5.0/Documentation/CHANGES_v0.5.0_JA.md) / [CVS2導入](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.5.0/Documentation/CVS2_INTEGRATION_JA.md) / [Unity MCP引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.5.0/UNITY_MCP_HANDOFF.md)
