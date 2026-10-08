# v0.7.0 — APEX / NEON SWITCHYARD をテクニカルコースへ改修

- **カートの走路を全面改修**。90°・半径6 mの切り返し34か所の旧線形を、世界の実在サーキットにある代表的なコーナーの性格を取り入れた **33コーナー・3層** のテクニカルコースへ変更しました。
- **コーナーの種類を大幅に追加**。ヘアピン、半径が縮む連続右、バンク付き360°カルーセル、S字5連、曲がりながらの登坂、ダブルエイペックス、高速の大半径、二重シケイン、トリプルエイペックス、下りのシケイン、半径が広がる最終コーナー。
- **高低差をコーナーの中へ**。直線スロープ4本から、登りながら回るカルーセル、オー・ルージュ型の登坂、2層分を一気に下るコークスクリュー型の下りへ。
- **カフェ・FPV・街並み・カート建屋は変更していません**。Unity用メッシュのカート以外の記録がv0.6.1とバイト一致することを確認しています。

## コース

| 項目 | v0.6.1 | v0.7.0 |
| --- | --- | --- |
| 走路全長 | 1,268.83 m | 1,002.31 m |
| コーナー | 90°・r6 mの円弧34 | 33コーナー（46頂点）、中心半径6.0〜18 m、旋回角23.6〜360° |
| 路面高 | 0.35／4.55／8.75 m | 同じ |
| 層の接続 | 直線スロープ4本 | 3区間（カルーセル74.9 m、登坂59.6 m、下り127.4 m） |
| 最大勾配／バンク | 11.66%／なし | 10.60%／カルーセル最大8° |
| 立体交差の最小クリアランス | 3.80 m | 3.37 m（基準3.0 m以上） |
| 支柱 | 109本 | 98本 |

![v0.7.0の平面図と縦断図](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.7.0/Preview/Design/09_Kart_Plan_v07.png?raw=true)

### 主なコーナーと参考にした実在コーナー

| T | 名称 | 形 | 参考 |
| --- | --- | --- | --- |
| T1–T2 | セナS | 左117°・r7 → 右55°・r9 | インテルラゴス「S do Senna」 |
| T3 | ヘアピン | 左120°・r8 | 鈴鹿「ヘアピン」 |
| T4–T5 | デグナー1／2 | 右90°をr9 → r6で2回 | 鈴鹿「デグナー」 |
| T7 | カルーセル | 左360°・r12・バンク8°。0.35→4.55 mへ登り、自身の入口の上を越える | ニュルブルクリンク「カルッセル」、鈴鹿の立体交差 |
| T9–T13 | S字 | 左右交互の5連・r12 | 鈴鹿「S字」、シルバーストン「マゴッツ〜ベケッツ〜チャペル」 |
| T16 | 右ヘアピン | 右180°・r7 | スパ「ラ・スルス」 |
| T18–T20 | オー・ルージュ／ラディヨン | 左・右・左で4.55→8.75 mへ登る | スパ・フランコルシャン |
| T21 | スプーン | 左のダブルエイペックス | 鈴鹿「スプーン」、スパ「プーオン」 |
| T22 | 130R | 左90°・r18の高速コーナー | 鈴鹿「130R」 |
| T24 | グランドヘアピン | 右180°・r6.5（最小） | モナコ「フェアモント」（左右反転） |
| T27 | バスストップ | 右・左・左・右の二重シケイン | スパ「バスストップ」 |
| T28 | トリプルエイペックス | 右150°を3頂点。下り開始 | イスタンブール・パーク「ターン8」（左右反転） |
| T29–T30 | コークスクリュー | 下りながら左97° → 右28° | ラグナ・セカ「コークスクリュー」 |
| T31 | レズモ | 下りの右99° | モンツァ「レズモ」 |
| T32 | 最終シケイン | 右・左 | 鈴鹿「カシオトライアングル」 |
| T33 | パラボリカ | 左180°、半径8→14 m | モンツァ「パラボリカ」（左右反転） |

コーナーの向き・半径の比・連続性・高低差を屋内カート用に縮小して取り入れたもので、どのサーキットも再現していません。会場内の表示は路面のT1〜T33と区画名だけで、サーキット名・ロゴは使っていません。全33コーナーは [変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.7.0/Documentation/CHANGES_v0.7.0_JA.md) を参照してください。

### 走路まわり

- 各コーナーの5 m手前に金色のT番号を路面ペイント（勾配・バンクに合わせて傾斜）。
- 進行矢印をスロープ・バンクの面に沿わせました。タイヤは下層コーナー内側の床に置いています。
- ピット・観戦席・6台分のCVS2配置ガイド・帰還ポータル・時間パネルは、新しいメインストレートの南側へ移動。構成と寸法は従来どおりです。

## スクリーンショット

**この版の実モデルをBlender 4.5.14 / Cyclesでレンダリングしています。Unity／VRChatで撮影した画像ではありません。** 全景のみ屋根・手前2面の壁・トラスを非表示にしたカットアウェイです。カフェ・FPV・街並みは変更がないため、v0.6.1の画像を参照してください。

### 全景 — 3層・33コーナー

![カート全景](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/16_Kart_Overview.png)

### T7 カルーセル — バンク8°で360°登り、自身の入口を越える

![カルーセル](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/24_Kart_Carousel.png)

### カルーセル進入 — 頭上を出口の路面が通る運転視点

![カルーセル進入](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/18_Kart_Driver.png)

### 中層 T9〜T13 — S字5連

![S字](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/25_Kart_Esses.png)

### T17〜T20 — オー・ルージュ型の登坂

![登坂](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/26_Kart_Climb.png)

### 上層 T27 — バスストップ型の二重シケイン

![バスストップ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/20_Kart_UpperTechnical.png)

### T29〜T31 — 下り橋と下層のデグナー型ヘアピン

![下り橋](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/27_Kart_Corkscrew.png)

### 下り橋の下を走る下層

![高架下](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/17_Kart_Overpass.png)

### スタートゲート・ピット・観戦席

![ピット](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.7.0/19_Kart_Pits.png)

## ダウンロード・導入

| 添付ファイル | 内容 |
| --- | --- |
| `The_Commons_Compact_v0.7.0.unitypackage` | Unity導入用。PC／Questモデル・素材・シーン生成Editor・UdonSharp・シェーダー |
| `The_Commons_Compact_v0.7.0_Full.zip` | 編集用Blender・FBX・glTF・CAD・設計資料・全ソース・プレビュー画像 |
| PNG 9枚 | 上記のカート実モデル画像を原寸で添付 |
| `SHA256SUMS-v0.7.0.txt` | 2種類の配布物・検証JSON・PNG 9枚のSHA-256 |
| `release-validation-v0.7.0.json` | 公開元コミット、配布内容の照合結果、画像・配布物のサイズとハッシュ |

1. VCCのWorldsプロジェクトへUnityパッケージをインポート。SDK／UdonSharpはVCC側で導入します。
2. **The Commons → Build PC World / Build Quest World** で新しいシーンを生成。
3. **The Commons → Bake lighting** で再ベイク。
4. CVS2車両を移動後の配置ガイド（Unity Y=0.47、Z=25.60、X=231.20〜270.78）へ置き直します。カフェからの着地点は `(231.31, 0.42, 15.00)`。
5. VRChat SDKのBuild & Testで、全周走行・カルーセル・登坂・下り・ヘアピンをPC／Questそれぞれ確認してください。

**既存の生成シーンには自動適用されません。** CVS2等を追加した古いシーンは残し、新しい生成シーンへ必要な設定を移してください。制作基準はUnity 2022.3.22f1／SDK 3.10.5／Built-in Render Pipelineで、現在の対応版はVCC・公式指定に従ってください。

## 検証範囲

**共通形状46項目＋カート17項目、計63項目すべて合格。** カート検査に、路面デッキの実形状から測るバンク角と、コーナー台帳と走路の一致を追加しました。連続デッキの閉じた形状、上向き路面、勾配・旋回半径、立体交差の高さ、支柱98本の路面干渉、ピット、6配置ガイド、ワープ着地の空間を検査しています。C#12ファイルの構文検査、配布物と公開ソースの全バイト一致、画像・チェックサムも確認しています。

| 書き出し形状 | PC | Quest |
| --- | ---: | ---: |
| ワールド全体 | 288,809 tris／194メッシュ | 237,607 tris／186メッシュ |
| うちカート | 105,941 tris／36メッシュ | 97,111 tris／36メッシュ |
| カートの上限設定 | 170,000 tris | 140,000 tris |

カフェ・FPV・街並みは、Unity用メッシュのカート以外の記録（PC 158件・Quest 150件）、Unity生成用マニフェストのカート以外の項目、Blender原本のカート以外の7,132オブジェクトがv0.6.1と一致することを確認しました。参照用のFBX・glTFは全体を書き出し直しており、Blenderのパッチ版差による1e-6程度の丸め差があります。

**CVS2車両での全周走行、Unity/Udon・シェーダーコンパイル、ライトベイク、VRChat実機／両眼表示／FPSは未検証。** 制作データの公開であり、VRChatへのアップロードではありません。CVS2車両・VRC+ドローンのシステムは同梱しません。v0.6.0図面集のカート図面・デザインシートは旧コースの過去資料です。

[変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.7.0/Documentation/CHANGES_v0.7.0_JA.md) / [現在の詳細仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.7.0/README.md) / [Unityへの引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.7.0/UNITY_MCP_HANDOFF.md) / [設計正本](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.7.0/SourceDesign/kart_circuit.json)
