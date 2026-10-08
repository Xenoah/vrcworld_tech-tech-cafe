# v0.8.0 — いろは坂型の複合7連ヘアピン・カルーセル・ジャンプ

- **カートの走路を作り直し**。v0.7.0のS字が続く「うねり」を減らし、直線と性格のはっきりしたコーナーで組んだ **全長1,141.23 m・26コーナー・3層** のコースにしました。
- **いろは坂型の7連ヘアピンを、すべて複合ヘアピンに**。平底の2頂点、涙滴形、半径が縮む、S字進入、2段、半径が広がる、2段のV字の7種類を、斜めに走る長さの違う脚でつなぎ、4.55→0.35 mを階段状に下ります。
- **注文のコーナーを追加**。クッパ城のような直角、モンツァのシケイン、ラグナ・セカのような下りのコークスクリュー、スパのようなヘアピン、鈴鹿のような立体交差、高速コーナー、ノルトシュライフェのような複合区間、ジャンプ2か所、前版の360°カルーセル。
- **カフェ・FPV・街並み・カート建屋は変更していません**。Unity用メッシュのカート以外の記録がv0.7.0とバイト一致することを確認しています。

## コース

| 項目 | v0.7.0 | v0.8.0 |
| --- | --- | --- |
| 走路全長 | 1,002.31 m | 1,141.23 m |
| コーナー | 33コーナー（46頂点） | 26コーナー（44頂点）、中心半径6.0〜20 m |
| 層の接続 | 3区間 | 4区間（カルーセル74.9 m、登坂56.9 m、コークスクリュー52.4 m、いろは坂494.8 m） |
| 最大勾配／バンク | 10.60%／カルーセル最大8° | 11.92%（コークスクリュー）／カルーセル最大8° |
| 立体交差／ジャンプ | 最小3.37 m／なし | 3か所・最小3.37 m／2か所 |
| 支柱 | 98本 | 129本 |

![v0.8.0の平面図と縦断図](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.8.0/Preview/Design/09_Kart_Plan_v08.png?raw=true)

### 注文と対応

| 注文 | 実装 |
| --- | --- |
| クッパ城のような直角コーナー | 上層T12〜T14、中層T17〜T18。半径6〜7 mの直角を長めの直線でつなぐ |
| モンツァのシケイン | T1〜T2。メインストレートの先で右・左 |
| ラグナ・セカのような下りのコークスクリュー | T14の頂上から路面が落ち、左T15・右T16で52 mの間に4.2 m下る |
| スパのようなヘアピン | T10。左183°・半径8 m。頂点から上層へ登る |
| 鈴鹿の立体交差 | 上層の城が峠の入口の脚とT19の上を渡る。T10後の登坂はT21の上、カルーセルは自身の入口の上を通る |
| 高速コーナー | T3（半径16 m）、T6〜T7（20 m）、T26（14 m）、バンク付きのT4カルーセル（12 m） |
| 下りの7連ヘアピン（いろは坂のように複雑に、複合ヘアピンで） | T19〜T25。7つすべて形の違う複合ヘアピン（下表） |
| ノルトシュライフェのような複雑なコーナー | T6〜T9。高速キンク、コンプレッション、右・左のフリック、ブラインドクレスト |
| ジャンプポイント | J1（T3後の下層、高さ0.75 m）、J2（T11後の上層、0.5 m）。路面に「JUMP」と踏切線 |
| 前版の「ぐるっと回る」カーブ | T4。バンク3°→8°→5°で360°登り、自身の入口の上を越える |

### いろは坂型の7連ヘアピン（T19〜T25）

| T | 形 | 高さ |
| --- | --- | --- |
| T19 | 平底の2頂点：左90°→直線5 m→左89°（r6）。城の下をくぐる | 4.10 m |
| T20 | 涙滴形：左35°で外へ振り、右250°（r8）で回り込み、左35°で戻す | 3.60 m |
| T21 | 左19°の高速キンクから、半径が縮むヘアピン：左60°（r10）→左121°（r6） | 3.00 m |
| T22 | S字進入：左25°（r8）で振ってから右192°（r6.5） | 2.40 m |
| T23 | 2段：左95°（r6）→直線5 m→左97°（r7） | 1.90 m |
| T24 | 半径が広がる：右95°（r6）→右111°（r12） | 1.30 m |
| T25 | 2段のV字：左95°→直線4 m→左106°（r7）。最終区間へ斜めに下る | 0.80 m |

T19〜T20は縦の脚、T21以降は長さ12〜39 mの斜めの脚で南西へ折り返しながら、ヘアピンごとに0.45〜0.6 mずつ下ります。

コーナーの向き・半径の比・連続性・高低差を屋内カート用に縮小して取り入れたもので、どのサーキット・道路・ゲームのコースも再現していません。会場内の表示は路面のT1〜T26・JUMPと区画名だけで、サーキット名・ゲーム名・ロゴは使っていません。全26コーナーは [変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.8.0/Documentation/CHANGES_v0.8.0_JA.md) を参照してください。

## スクリーンショット

**この版の実モデルをBlender 4.5.14 / Cyclesでレンダリングしています。Unity／VRChatで撮影した画像ではありません。** 全景のみ屋根・手前2面の壁・トラスを非表示にしたカットアウェイです。カフェ・FPV・街並みは変更がないため、v0.6.1の画像を参照してください。

### 全景 — 3層・26コーナー

![全景](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/16_Kart_Overview.png)

### T19〜T25 — いろは坂型の複合7連ヘアピン

![T19〜T25](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/25_Kart_Hairpins.png)

### T4 カルーセル — バンク8°で360°登り、自身の入口を越える

![T4 カルーセル](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/24_Kart_Carousel.png)

### 上層T12〜T14 — クッパ城のような直角

![上層T12〜T14](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/20_Kart_Castle.png)

### T14〜T16 — 頂上から落ちるコークスクリュー

![T14〜T16](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/27_Kart_Corkscrew.png)

### T10 — スパ型ヘアピンから上層へ

![T10](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/26_Kart_SpaHairpin.png)

### T6〜T9 — ノルトシュライフェ型の高速キンクとフリック

![T6〜T9](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/28_Kart_Nordschleife.png)

### J1 — 下層直線のジャンプ

![J1](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/29_Kart_Jump.png)

### 峠の入口から見上げる上層の城（立体交差）

![峠の入口から見上げる上層の城（立体交差）](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/17_Kart_Overpass.png)

### メインストレートからT1シケインへ（運転視点）

![メインストレートからT1シケインへ（運転視点）](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/18_Kart_Driver.png)

### スタートゲート・ピット・観戦席

![スタートゲート・ピット・観戦席](https://github.com/Xenoah/vrcworld_tech-tech-cafe/releases/download/v0.8.0/19_Kart_Pits.png)

## ダウンロード・導入

| 添付ファイル | 内容 |
| --- | --- |
| `The_Commons_Compact_v0.8.0.unitypackage` | Unity導入用。PC／Questモデル・素材・シーン生成Editor・UdonSharp・シェーダー |
| `The_Commons_Compact_v0.8.0_Full.zip` | 編集用Blender・FBX・glTF・CAD・設計資料・全ソース・プレビュー画像 |
| PNG 11枚 | 上記のカート実モデル画像を原寸で添付 |
| `SHA256SUMS-v0.8.0.txt` | 2種類の配布物・検証JSON・PNG 11枚のSHA-256 |
| `release-validation-v0.8.0.json` | 公開元コミット、配布内容の照合結果、画像・配布物のサイズとハッシュ |

1. VCCのWorldsプロジェクトへUnityパッケージをインポート。SDK／UdonSharpはVCC側で導入します。
2. **The Commons → Build PC World / Build Quest World** で新しいシーンを生成。
3. **The Commons → Bake lighting** で再ベイク。
4. CVS2車両を配置ガイド（Unity Y=0.47、Z=25.60、X=230.775〜271.395）へ置き直します。カフェからの着地点は `(231.41, 0.42, 15.00)`。
5. VRChat SDKのBuild & Testで、全周走行・ジャンプ・カルーセル・コークスクリュー・7連ヘアピンをPC／Questそれぞれ確認してください。

**既存の生成シーンには自動適用されません。** CVS2等を追加した古いシーンは残し、新しい生成シーンへ必要な設定を移してください。制作基準はUnity 2022.3.22f1／SDK 3.10.5／Built-in Render Pipelineで、現在の対応版はVCC・公式指定に従ってください。

## 検証範囲

**共通形状46項目＋カート18項目、計64項目すべて合格。** カート検査に、ジャンプ頂部の真上に他の路面がないことの確認を追加しました。連続デッキの閉じた形状、上向き路面、勾配・旋回半径、路面デッキから測るバンク角、コーナー台帳と走路の一致、立体交差の高さ、支柱129本の路面干渉、ピット、6配置ガイド、ワープ着地の空間を検査しています。C#12ファイルの構文検査、配布物と公開ソースの全バイト一致、画像・チェックサムも確認しています。

| 書き出し形状 | PC | Quest |
| --- | ---: | ---: |
| ワールド全体 | 294,325 tris／194メッシュ | 246,524 tris／186メッシュ |
| うちカート | 111,457 tris／36メッシュ | 106,028 tris／36メッシュ |
| カートの上限設定 | 170,000 tris | 140,000 tris |

カフェ・FPV・街並みは、Unity用メッシュのカート以外の記録（PC 158件・Quest 150件）、Unity生成用マニフェストのカート以外の項目、Blender原本のカート以外のオブジェクトがv0.7.0と一致することを確認しました。

**CVS2車両での全周走行、Unity/Udon・シェーダーコンパイル、ライトベイク、VRChat実機／両眼表示／FPSは未検証。** 制作データの公開であり、VRChatへのアップロードではありません。CVS2車両・VRC+ドローンのシステムは同梱しません。

[変更仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.8.0/Documentation/CHANGES_v0.8.0_JA.md) / [現在の詳細仕様](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.8.0/README.md) / [Unityへの引き継ぎ](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.8.0/UNITY_MCP_HANDOFF.md) / [設計正本](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.8.0/SourceDesign/kart_circuit.json)
