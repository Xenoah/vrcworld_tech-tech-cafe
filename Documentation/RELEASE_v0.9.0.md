# v0.9.0 — ポータル案内・照明3モード・iwaSync用ステージ

昨日のClaude更新 **v0.8.0 / 65c185a** を基準に更新。26コーナー・3層のカート、ジャンプ、バンク、FPV飛行エリアを保持しました。

- 入口正面の左にシアンのFPV、右にピンクのKART。大きな看板、床矢印、2.1 × 0.72 mの選択ボタン。帰りのCAFE表示も拡大。
- スライド・タイマー・Q&A・ポインター・独自動画再生とURL UIを撤去。演台・マイク・スクリーンの旧文字も除去。
- 暖色／サイバー／ディスコ＋レーザーの照明を選択。ホスト操作・途中参加同期用の状態を実装。昼夜・家具モードとは独立。
- レーザーはPC 12本／Quest 6本。REDUCED MOTION（既定ON）で静止、LASERS (LOCAL)で自分だけ非表示、LOW EMISSIONで減光。

**iwaSync本体の導入・接続は別途必要です。** この版は撤去と配置準備まで。主画面・上階画面とアンカーを用意し、内蔵BGM/DJは初期OFFにしています。

## ダウンロード・適用

- `The_Commons_Compact_v0.9.0.unitypackage`：Unity向け資産。
- `The_Commons_Compact_v0.9.0_Full.zip`：Blender・ソース・設計資料・画像一式。
- `SHA256SUMS-v0.9.0.txt` / `release-validation-v0.9.0.json`：配布物の照合結果。

旧シーンを保存・複製し、アセット更新後に **The Commons → Build PC World / Build Quest World** で新しいシーンを生成してください。旧シーンへのアセット上書きだけでは旧オブジェクトは消えません。互換用の旧VideoSync型は無処理化しています。

[iwaSync接続手順](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.9.0/Documentation/IWASYNC_INTEGRATION_JA.md) · [詳細変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.9.0/Documentation/CHANGES_v0.9.0_JA.md) · [README](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.9.0/README.md)

## 検証

既存7,911オブジェクト保持・両ポータルの見通し、旧版との差分37項目、共通形状46項目、カート18項目、C#構文14ファイルを確認。未変更のPC 188 / Quest 180メッシュ記録を再利用して旧版の形状を保持しています。

**Unity/Udon/Shaderコンパイル、ライトベイク、複数人通信、VR/Quest実機、iwaSync再生、VRChatアップロードは未実施です。** ビルド済みワールドではなくシーン生成用の制作データです。

## 画像

Blender 4.5.14 LTS / Cyclesで更新モデルをレンダリング。照明とレーザーはUnityの配色・配置を使ったデザイン確認です。Unity/VRChatの実機スクリーンショットではありません。

### 入口正面のFPVとKART：大型案内・色分け・選択パネル

![入口正面のFPVとKART：大型案内・色分け・選択パネル](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.9.0/30_Activity_Portals.png)

### 暖色照明のカフェ全景

![暖色照明のカフェ全景](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.9.0/31_Cafe_Warm.png)

### シアンと紫のサイバー照明

![シアンと紫のサイバー照明](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.9.0/32_Cafe_Cyber.png)

### ディスコ照明と有限長のレーザー

![ディスコ照明と有限長のレーザー](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.9.0/33_Cafe_Disco.png)

### 旧プレゼンを撤去したメインステージ・空画面

![旧プレゼンを撤去したメインステージ・空画面](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.9.0/34_Stage_iwaSync.png)

