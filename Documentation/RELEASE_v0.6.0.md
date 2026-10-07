# v0.6.0 — NEON SWITCHYARD 屋内テクニカルコース

カートフロアを、密度の高いネオンの屋内コースへ全面改修しました。参考写真の青・紫の光と低い壁を取り入れ、**レイアウトはオリジナル**で設計しています。

- **148 × 160 m／約1.27 km／34コーナー**。幅5.2 m、最小中心半径6.00 mの連続する切り返し。
- **3層の立体交差**。路面高0.35・4.55・8.75 m。4本の滑らかなスロープと橋下区間。
- 全面屋根と鉄骨トラス、青・シアンの上端／側面LED、紫の壁面照明、黒い光沢路面、ピンク／白のガード。
- カフェとの往復ワープ、6台分の空の配置ガイド、ピット、屋根付き観戦席。
- 屋内の光は外の時間帯に依存しない設定。PCのベイク反射プローブを追加。
- **CVS2は所有者が別途導入**。車両や独自車両システム・レース計測は同梱していません。

## 実モデル画像

この版の実モデルを **Blender 4.5.3 / Cycles** でレンダリングしています。Unity／VRChat内の撮影ではありません。車両は含まれません。全景のみ屋根・手前2面の壁・トラスを非表示にしたカットアウェイで、他の4枚は閉じた屋内モデルのままです。

![低いネオン壁とタイトな旋回](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.0/18_Kart_Driver.png)

![3層オリジナルレイアウト・カットアウェイ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.0/16_Kart_Overview.png)

![橋下の走行視点](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.0/17_Kart_Overpass.png)

![ピットと観戦席](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.0/19_Kart_Pits.png)

![上層のテクニカルセクション](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.6.0/20_Kart_UpperTechnical.png)

## ダウンロード

| ファイル | 内容 |
| --- | --- |
| `The_Commons_Compact_v0.6.0.unitypackage` | PC／Questモデル・素材・Editor・UdonSharp・シェーダー |
| `The_Commons_Compact_v0.6.0_Full.zip` | Unityデータ、編集用Blender、CAD、仕様、画像20枚、再生成ソース |
| `16_Kart_Overview.png`〜`20_Kart_UpperTechnical.png` | 今回の実モデル画像5枚 |
| `SHA256SUMS-v0.6.0.txt` | 配布物・画像のSHA-256 |
| `release-validation-v0.6.0.json` | ソースと配布物の内容一致検査、画像一覧、対象コミット |

VCCのWorlds / Built-inプロジェクトにUnityパッケージを導入し、**The Commons → Build PC World** または **Build Quest World** で新シーンを生成。CVS2車両はその後、`KART_ExternalVehicleAnchors/CVS2_Bay_01`〜`06` を目安に配置します。ライトベイクとVRChat SDKのBuild & Testを行ってください。Blender編集時はFull.zip全体を展開します。

## 検証範囲

共通形状36項目＋カート15項目、C#構文12ファイル、メタデータ、配布物の内容一致と画像添付を検査。橋下最小3.80 m、最大勾配11.66%、最小中心旋回半径6.00 m。全体はPC 295,797 tris／Quest 245,507 tris。カート部分はPC 135,913 tris／Quest 123,403 trisです。

**Unity/Udon・シェーダーのコンパイル、ライトベイク、CVS2走行・同期、VRChat内の表示、PC／Quest実機FPSは未検証です。** 使用車両で旋回・車体幅・車高・速度を調整してください。制作データのリリースであり、生成済みシーン・ビルド済みワールドは含みません。

[変更詳細](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.6.0/Documentation/CHANGES_v0.6.0_JA.md) / [CVS2導入](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.6.0/Documentation/CVS2_INTEGRATION_JA.md) / [Unity MCP引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.6.0/UNITY_MCP_HANDOFF.md)
