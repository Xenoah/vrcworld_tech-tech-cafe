# v0.11.0 — BGM同期のパーティクルレーザー・カートのネオトーキョー装飾

v0.10.0（376c334）を基準に、DISCOのレーザーとカート館内を更新しました。**Blenderモデル・既存メッシュ記録・カートの走路メッシュと当たり判定・コースのソースは変更していません。** ラップタイムはCVS2側で計測する前提のため触っていません。

- **パーティクルレーザー**：DISCOのレーザーをメッシュからパーティクル（PC 12本／Quest 6本）に変更。拍の間は破線状の光線、**キックのたびに明るく密な粒の塊**が光線に沿って飛びます。図形（扇・交差・トンネル・流し）は小節ごと、色は小節のコードごとに切り替わります。BGMを作るスクリプトが書き出した16分音符単位の譜面を、実際に鳴っているステムの再生位置で読むため、音声解析なしで聞こえる音と一致し、全員に同じ光が見えます。HOUSE MUSIC OFFでもサーバー時計のテンポで動作。REDUCED MOTIONでは静止し脈動しません。iwaSyncの音は解析しません（AudioLink非対応）。
- **カートのネオトーキョー装飾**：J1ジャンプの直線に**鳥居のトンネル**（6基、路面の起伏に合わせて上下し、ジャンプ頂点でも頭上3.6 m）、7連ヘアピン入口に両面バナーの**七曲峠ゲート**、提灯4列、電波塔、看板13枚、自販機4台。すべてデッキ・ピット・タイヤ・壁から離して配置し、当たり判定は自販機のみ。CVS2の車両・計測には影響しません。
- **ネオンの樹木**：これまで館内に樹木はなかったため、7連ヘアピンの周囲にネオンの木を54本新設（モミジ・サクラ・スギ、Quest 29本）。T20・T22〜T25のヘアピン内側にシンボルツリー（T19・T21は内側に余地がないため無し）。暗い樹冠に光る格子とネオンの輪を重ねたデザインです。

## ダウンロード・適用

- `The_Commons_Compact_v0.11.0.unitypackage`：Unity向け資産。
- `The_Commons_Compact_v0.11.0_Full.zip`：Blender・ソース・設計資料・画像一式。
- `SHA256SUMS-v0.11.0.txt` / `release-validation-v0.11.0.json`：配布物の照合結果。

旧シーンを保存・複製し、アセット更新後に **The Commons → Build PC World / Build Quest World** で新しいシーンを生成してください。Consoleに `THE COMMONS kart neon: 54 trees, 6 torii, 10 wall signs`（Questは29 trees）が出ます。

[詳細変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.11.0/Documentation/CHANGES_v0.11.0_JA.md) · [受入チェック](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.11.0/Documentation/ACCEPTANCE_JA.md) · [Unity MCP引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.11.0/UNITY_MCP_HANDOFF.md) · [README](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.11.0/README.md)

## 検証

カート装飾の配置検査4項目（全デッキ・ピット・タイヤ・壁との離隔、樹冠とデッキ端の最小距離0.92 m、吊り看板は最上層から3 m以上上、全ヘアピンへのシンボルツリーの配置可否）、旧版との差分37項目（カートのメッシュとコースのソースがv0.8.0から不変、照明の同期変数の維持を含む）、C#構文24ファイルを確認。実行時スクリプト19本と体験・照明・カート装飾ビルダーは、Unity/VRChat/UdonSharp APIの最小スタブに対してmcsで型検査しエラー0（実SDKでのコンパイルの代わりではありません）。

**Unity/Udon/Shaderコンパイル、ライトベイク、複数人通信、VR/Quest実機、CVS2車両での走行、VRChatアップロードは未実施です。** ビルド済みワールドではなくシーン生成用の制作データです。確認項目は受入チェックのv0.11.0にまとめています。

## 画像

実モデル（`The_Commons_Compact.blend`）に、ビルダーが生成する装飾を `kart_neon_layout.json` と同じ寸法・同じプリミティブで再構築し、Blender 4.0.2 / Cyclesでレンダリング（Intel Open Image Denoise 2.3.3でノイズ除去）。レーザーは `CommonsLightingModes` と同じ手順で、ある瞬間に飛んでいる粒子を計算して描いています。カートの画像はトーンマッピングなし（Unityがトーンマッパーなしで描くのに近い表示）、カフェはv0.9.0の31〜33と同じAgXです。**Unity/VRChatの実機スクリーンショットではありません。**

### DISCOのパーティクルレーザー（Dmaj9の小節・扇の図形・3拍目のキック直後）

![DISCOのパーティクルレーザー](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.11.0/41_Cafe_Particle_Lasers.png)

### 7連ヘアピンとネオンの樹木

![7連ヘアピンとネオンの樹木](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.11.0/42_Kart_Neon_Pass.png)

### J1ジャンプの直線、鳥居のトンネル（ドライバー目線）

![鳥居のトンネル](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.11.0/43_Kart_Torii_Tunnel.png)

### 七曲峠ゲートへの登り（ドライバー目線）

![七曲峠ゲート](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.11.0/44_Kart_Pass_Gate.png)

### カート館内のネオン装飾の全景（屋根・南壁・東壁を外した断面）

![カート館内の全景](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.11.0/45_Kart_Neon_Overview.png)
