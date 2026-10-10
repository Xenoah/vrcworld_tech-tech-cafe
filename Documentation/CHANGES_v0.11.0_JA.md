# v0.11.0 — BGM同期のパーティクルレーザー・カートのネオトーキョー装飾

**Unity/UdonSharp/シェーダーのコンパイル、ライトベイク、VRChat Build & Test、Quest実機は未検証です。** シーン生成用の制作データで、ビルド済みワールドではありません。

基準はv0.10.0（`376c334`）。**Blenderモデル・tcmesh・カートの走路メッシュと当たり判定・コースのソースは変更していません。** ラップタイムはCVS2側の担当のため触っていません。追加物はすべてシーン生成時にビルダーが作ります。

| 変更 | ひとことで |
| --- | --- |
| DISCOレーザー | メッシュの光線をやめ、**パーティクル**で描画。小節・拍・キック・コードに合わせて図形・密度・明るさ・色が変わる |
| カートのネオン装飾 | APEX（NEON SWITCHYARD）の館内に、鳥居のトンネル、七曲峠ゲート、提灯、電波塔、ネオン看板、自販機を配置 |
| ネオンの樹木 | 7連ヘアピン（T19〜T25）の周囲にネオンの木54本。ヘアピンの内側にはシンボルツリー |

**樹木について:** v0.10.0までのカート館内には樹木がありませんでした（7連ヘアピンの周囲も床のみ）。そのため「7連ヘアピンの樹木をネオンに」というご要望は、**ヘアピンの周囲にネオンの木を新しく植える**形で実装しています。

## 1. パーティクルレーザー（DISCO）

| 項目 | 仕様 |
| --- | --- |
| 発射位置 | 従来と同じ (10.2 / 17.8, 4.3, 5.3)。PC 12本・Quest 6本 |
| 粒子 | Udonが毎フレーム `ParticleSystem.Emit()` で発射（モジュールの発生数は0）。寿命0.28秒、秒速26 m（到達7.3 m、狙いの範囲まで約6.2 m）、太さ0.045 m、ストレッチビルボード（長さ約0.51 m）、ワールド空間 |
| 見え方 | 拍の間は**破線状の光線**、キックのたびに**密で明るい塊**が発射位置から光線に沿って飛んでいく。光線を振るとワールド空間の粒子が弧を描いて残る |
| シェーダー | `The Commons/Laser Particle`（加算合成・芯の柔らかい光・深度テストあり・フォグ対応、Quest可） |
| 上限 | 1本あたり最大64粒子（Quest 40）。影なし |

| 音楽 | 光 |
| --- | --- |
| 小節（16小節ループ） | 4種類の図形（扇・交差・トンネル・流し）を小節ごとに切り替え。1拍目の間にブレンド |
| 拍 | 図形の中の動き（掃引・回転）が拍に同期 |
| キック | 粒子の密度0.45倍→最大2.25倍、明るさ0.55→0.95、アクセントライト＋35%。約0.3秒で減衰し、点滅にはならない |
| コード | 各小節のコードに対応した2色（Dmaj9＝シアン／ピンク、Bm9＝紫／水色、Gmaj9＝緑／青、A6/9＝ピンク／琥珀など）。1拍かけてクロスフェード |

**同期のしくみ:** `Blender/build_experience_audio.py` が、BGMのステムと同じパターンから16分音符単位の譜面 `Data/music_score.json` を書き出します（キック・スネア・ハット・ベース・コード）。`CommonsAdaptiveMusic` は**実際に鳴っているステムの再生位置**（`AudioSource.time`）でこの譜面を読むため、音声解析なしで聞こえる音とぴったり合い、Questでも軽量です。再生位置はサーバー時計に揃えてあるため、全員に同じ光が見えます。

- **HOUSE MUSIC OFF（既定）のとき:** 譜面はサーバー時計で進み、キックは弱め（0.45倍）。音が無くても全員同じテンポで動きます。
- **iwaSyncの音は解析しません**（AudioLink非対応）。動画・配信の曲には合いません。
- **酔い・光への配慮:** REDUCED MOTIONでは扇形のまま静止し、粒子は一定量で脈動しません。LASERS (LOCAL) OFFで非表示、LOW EMISSIONで0.35倍。ストロボ・点滅はありません。
- 旧 `CommonsLaser.shader` は過去のシーンのために残しています（新しいシーンでは未使用）。

## 2. カートのネオトーキョー装飾（APEX館内）

配置は `Blender/build_kart_neon_layout.py` がカートのマニフェスト（中心線・3層のデッキ・ピット・タイヤ・壁）から計算して検査し、`Data/kart_neon_layout.json` に書き出します。`CommonsKartNeonBuilder`（`CommonsExperienceBuilder` の一部）が `ATTR_KartNeon` として生成します。

| 要素 | 位置・仕様 |
| --- | --- |
| 鳥居トンネル | 6基。下層のJ1ジャンプの直線（station 44.9〜77.4 m、間隔6.5 m）。笠木は路面から5 m、柱は路面の端から0.35 m外。鳥居は路面の起伏に合わせて上下し、**ジャンプ頂点（66.3 m）でも貫の下端まで3.6 m** |
| 七曲峠ゲート | station 578.3 m（7連ヘアピン入口の直線、上層4.51 m）。両面のバナー「七曲峠 / NANAMAGARI PASS · 7 HAIRPINS」と琥珀色のネオン管。登りから来るカートが正面を読める向き |
| ネオンの樹木 | 54本（モミジ27・サクラ10・スギ17）。**T20・T22・T23・T24・T25のヘアピン内側にシンボルツリー**（T19・T21は内側に植える余地がないため無し）、残りは峠の周囲の床 |
| 提灯 | 4列（赤・白の提灯、3.4 mのポールの間に吊る） |
| 電波塔 | 南西角 (186.3, 0, 6.3)。高さ12.4 m＋アンテナ、赤白の枠・筋交い・展望部。デッキから38 m離れた位置 |
| 壁の看板 | 10枚。縦看板「東京」「電脳」「加速」「夜走」「峠」「未来」、横看板「ネオ東京」「ネオン操車場」「安全運転」 |
| 吊り看板 | 3枚（「頂点 APEX」「ネオ東京」「ネオン操車場」）。高さ12.75 m、両面、最上層から3 m以上上 |
| 自販機 | 4台、南側の通路。ブランドのない汎用デザイン |

**ネオンの木:** 暗い幹と暗く発光する樹冠に、ホログラムの格子殻（12×6本の線がネオン管のように光る）と明るいネオンの輪を重ねています。スギ＝ミント、モミジ＝朱、サクラ＝ピンク。

**干渉と走行への影響:** 床に置く物はすべて、3層すべてのデッキの端から0.8 m＋自身の半径以上、ピット・タイヤ・壁から離しています（樹冠とデッキ端の最小距離0.92 m）。装飾は**当たり判定なし**（自販機だけ当たり判定あり、南側通路）。カートのメッシュ・当たり判定・コースは変更しておらず、CVS2の車両・計測には影響しません。

**ライティング:** 発光部はBaked Emissive（Contribute GI、Scale in Lightmap 0）。ベイクで床を照らし、自身はライトプローブで照らされます。

**Quest:** シンボルツリーは全て残し、その他の木は半分（計29本）。電波塔の筋交いは省略。シェーダーはFlat Light。

**文字:** 看板の文字はNoto Sans CJK JP（SIL OFL 1.1）でPNGテクスチャに描画しました（フォント自体は同梱しません）。文言はオリジナルで、ブランド名は使っていません。テクスチャは `Media/Neon/`、生成は `Blender/build_kart_neon_signs.py`。

## 3. 追加・変更したファイル

| 種類 | ファイル |
| --- | --- |
| UdonSharp（変更） | CommonsLightingModes（パーティクル発射、小節ごとの図形、コード色、キック連動）、CommonsAdaptiveMusic（譜面の読み込みと `Bar` / `BeatInBar` / `KickPulse` / `ChordColor` など） |
| シェーダー（追加） | Laser Particle |
| Editor | CommonsLightingBuilder（光線メッシュ→パーティクル発射器）、CommonsExperienceBuilder（譜面の接続、カート装飾の呼び出し、`partial`化）、CommonsKartNeonBuilder（追加） |
| データ | `Data/music_score.json`、`Data/kart_neon_layout.json` |
| テクスチャ | `Media/Neon/*.png`（看板11枚、自販機2枚） |
| 生成・検査 | `Blender/build_experience_audio.py`（`--score-only`）、`Blender/build_kart_neon_layout.py`、`Blender/build_kart_neon_signs.py`、`Blender/render_neon_views.py` |
| 記録 | `kart_neon_validation.json`、`kart_neon_signs.json`、`csharp_syntax_report.json` |

## 4. プレビュー画像

`Blender/render_neon_views.py` で、**実モデル（`The_Commons_Compact.blend`）を開き、ビルダーが生成する装飾を `kart_neon_layout.json` と同じ寸法・同じプリミティブで再構築**してレンダリングしました（Blender 4.0.2 / Cycles 40サンプル、Intel Open Image Denoise 2.3.3）。レーザーは、`CommonsLightingModes` と同じ手順（毎フレームの発射数、速度、寿命、小節の図形、コード色）で**ある瞬間に飛んでいる粒子を計算**し、カメラに向いたストレッチビルボードとして描いています。**Unity/VRChatの実機スクリーンショットではありません。**

- カートの画像はトーンマッピングなし（Standard）で表示しています。Unityがトーンマッパーなしで描くのに近く、AgXではネオンの色が白っぽく抜けるためです。カフェの画像は31〜33と比べられるよう、ファイル既定のAgXのままです。
- 色の値は過去のプレビューと同じくそのまま（リニア）使っています。Linear色空間のUnityではColorプロパティがsRGBとして変換されるため、実機では色がやや濃く、発光が強めに出ます。

| 画像 | 内容 |
| --- | --- |
| `Preview/41_Cafe_Particle_Lasers.png` | DISCO（Dmaj9の小節、扇の図形、3拍目のキック直後）。発射位置から飛び出すキックの粒子の塊と、その先の破線状の光線。v0.9.0の `33_Cafe_Disco.png` と同じカメラ |
| `Preview/42_Kart_Neon_Pass.png` | 7連ヘアピンとネオンの樹木（25_Kart_Hairpinsと同じカメラ） |
| `Preview/43_Kart_Torii_Tunnel.png` | J1ジャンプの直線、鳥居のトンネル（ドライバー目線） |
| `Preview/44_Kart_Pass_Gate.png` | 七曲峠ゲートへの登り（ドライバー目線） |
| `Preview/45_Kart_Neon_Overview.png` | 館内全景（屋根・南壁・東壁を外した断面）。樹木・鳥居・電波塔・看板の配置 |

## 5. 検証

| 実施 | 結果 |
| --- | --- |
| C#構文（tree-sitter） | 合格（`csharp_syntax_report.json`） |
| 型検査（mcs、Unity/VRChat/UdonSharp APIの最小スタブに対して実行時スクリプト全19本＋体験・照明・カート装飾ビルダー） | エラー0。スタブは手書きのため、実SDKでのコンパイルの代わりにはなりません |
| カフェ・カートの回帰検査（`validate_cafe_experience.py`） | 合格。カートのメッシュとコースのソースがv0.8.0から変わっていないこと、照明の同期変数が維持されていることを含む |
| カート装飾の配置検査 | 4項目合格（`kart_neon_validation.json`） |

| 未実施 | 確認先 |
| --- | --- |
| Unity / UdonSharp / シェーダーのコンパイル、シーン生成、ライトベイク | 受入表（ACCEPTANCE_JA.md）の v0.11.0 |
| CVS2車両での全周走行（鳥居・ゲートの見え方、ジャンプ）、Quest性能 | 同上 |

## 6. 調整のポイント

- **レーザー:** `CommonsLightingModes` の `beamRate`（静止時の1秒あたりの粒子数）、`targetCenter` / `targetRadius`（狙いの範囲）。粒子の速度・寿命・太さは生成シーンの `LGT_DiscoLasers/LaserEmitter_*`。
- **譜面:** BGMを作り直したら `python3 Blender/build_experience_audio.py --score-only` で譜面だけ再生成できます。
- **カートの装飾:** 配置を変えるときは `Blender/build_kart_neon_layout.py` を編集して再生成（干渉検査に失敗すると書き出しません）。色・明るさは `CommonsKartNeonBuilder` の `NeonMat` / `ShellMat` の呼び出し。看板の文言は `Blender/build_kart_neon_signs.py`。
