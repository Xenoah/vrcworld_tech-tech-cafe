# v0.10.0 — 体験レイヤー：上空デッキ・DATA STREAM・視界ジャック・KOMO・アダプティブ音楽

v0.9.0（c3a50c9）を基準に、「メタバースだからこそできる体験」を追加しました。**Blenderモデル・既存メッシュ記録・カートの走路は変更していません。** 追加物はすべて新しい `CommonsExperienceBuilder` がシーン生成時に作ります。ラップタイムはCVS2側で計測する前提のため、カートには手を入れていません。

- **ORBIT DECK**：入口のKARTの右にある新しいORBITリフトから、カフェの120 m上空に浮かぶデッキへ。中央の重力井戸は重力0.16倍で、ジャンプを押し続けると浮上。見えない壁と天井で落下を防止。
- **DATA STREAM**：デッキ発の2両×4席のライド（824 m・約112秒）。西側のヘリックスで街へ降り、**カフェの南面ガラスと屋根をすり抜けて吹抜けを1周**、タワーの間を抜けて戻ります。サーバー時計で動くため同期変数なし。いつでも降車でき、乗り場へ戻ります。REDUCED MOTIONでは自分の車両だけ水平を保ち、速度に応じたトンネルビネットで酔いを抑えます。
- **視界ジャック**：ワープ、すり抜けのグリッチ、データの雨、星空、暗転など10種類のローカル演出。新しいEXPERIENCEパネルでOFF/SOFT/FULLと種類を選択。点滅なし、REDUCED MOTIONで静止。既存のポータルもワープ演出付きに（WARP OFFで従来どおり即時移動）。
- **SIZE LAB**：×0.1／×0.5／×1／×4に変身（×4はデッキのみ）。移動速度・ジャンプを自動補正し、FPV/カート移動・ライド搭乗・リスポーン・アバター変更で元に戻ります。
- **KOMO**：浮遊するオリジナルのコンパニオンロボ。バー、DJブース、ステージ、テラスなどを毎日のスケジュールで巡り、4周期に1回ライドの先頭に乗ります。近づくと自分の方を向き、話しかけると英語・日本語で応答。「Claude」の名称・ロゴ・外観は商標のため使用していません。
- **アダプティブ音楽**：コードで合成したオリジナルの7ステム（96 BPM・Dメジャー）が、活動モード・照明・時刻・場所・ライドに応じて切り替わります。カフェ内は従来どおりHOUSE MUSIC（既定OFF）に従い、デッキとライドでは常に流れます。

## ダウンロード・適用

- `The_Commons_Compact_v0.10.0.unitypackage`：Unity向け資産。
- `The_Commons_Compact_v0.10.0_Full.zip`：Blender・ソース・設計資料・画像一式。
- `SHA256SUMS-v0.10.0.txt` / `release-validation-v0.10.0.json`：配布物の照合結果。

旧シーンを保存・複製し、アセット更新後に **The Commons → Build PC World / Build Quest World** で新しいシーンを生成してください。ライド経路は生成シーンで調整後 **The Commons → Experience → Rebake Ride** で再計算できます。

[詳細変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.10.0/Documentation/CHANGES_v0.10.0_JA.md) · [受入チェック](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.10.0/Documentation/ACCEPTANCE_JA.md) · [Unity MCP引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.10.0/UNITY_MCP_HANDOFF.md) · [README](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.10.0/README.md)

## 検証

ライド経路の幾何検査6項目（タワーとの離隔2.19 m、吹抜け内でDJブース・ホログラム・南橋に干渉しない、最大横加速度14.8 m/s²、勾配+35.7°/-30.7°、デッキ通行者の頭上2.49 m以上、デッキ床より下を通らない）、旧版との差分37項目、共通形状46項目、カート18項目、C#構文23ファイルを確認。実行時スクリプト19本と体験ビルダーは、Unity/VRChat/UdonSharp APIの最小スタブに対してmcsで型検査しエラー0（実SDKでのコンパイルの代わりではありません）。音楽7ステムは全て同じ長さでループの継ぎ目を確認。

**Unity/Udon/Shaderコンパイル、ライトベイク、複数人通信、VR/Quest実機、VRChatアップロードは未実施です。** ビルド済みワールドではなくシーン生成用の制作データです。確認項目は受入チェックのv0.10.0にまとめています。

## 画像

実モデル（`The_Commons_Compact.blend`）に、Unityビルダーが生成する体験レイヤーの形状を `experience_layout.json` と同じ寸法で再構築し、Blender 4.0.2 / Cyclesでレンダリング（Intel Open Image Denoise 2.3.3でノイズ除去、照明はWARM）。ライド車両はUnityと同じ焼き込み表の姿勢です。視界ジャックの画像はシェーダーの計算をPythonに移植して重ねたデザイン確認です。**Unity/VRChatの実機スクリーンショットではありません。**

### ORBIT DECK全景：力場・重力井戸・ホロ惑星・乗り場

![ORBIT DECK全景：力場・重力井戸・ホロ惑星・乗り場](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.10.0/35_Orbit_Deck.png)

### 吹抜けを通過するDATA STREAM（先頭にKOMO）

![吹抜けを通過するDATA STREAM（先頭にKOMO）](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.10.0/36_DataStream_Atrium.png)

### タワーの間を抜けるDATA STREAMの座席から

![タワーの間を抜けるDATA STREAMの座席から](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.10.0/37_DataStream_Skyline.png)

### ANCHOR BARでエスプレッソを持つKOMO

![ANCHOR BARでエスプレッソを持つKOMO](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.10.0/38_KOMO_Bar.png)

### 入口のORBITリフトとEXPERIENCEパネル

![入口のORBITリフトとEXPERIENCEパネル](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.10.0/39_Orbit_Lift.png)

### 視界ジャックのデザイン確認：WARP・GLITCH・DATA RAIN・STARS

![視界ジャックのデザイン確認：WARP・GLITCH・DATA RAIN・STARS](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.10.0/40_ViewJack_Effects.png)
