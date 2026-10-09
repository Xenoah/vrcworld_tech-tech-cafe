# v0.9.0 — ポータル案内と照明、iwaSync用ステージ

## 基準と維持範囲

2026-10-08にClaudeが更新したv0.8.0 / `65c185ad0158e93db5023b1ae793313393ac2017`を基準にしています。いろは坂型の複合7連ヘアピン、26コーナー、3層、2か所のジャンプ、バンク付きカルーセルを継承。

`verify_cafe_source.py`で旧版と更新版の既存オブジェクトの座標・メッシュ・UV・材質割当・モディファイア・ライトを比較します。変更対象のプレゼン機材を除いて一致を要求します。その証明と.blendのハッシュを確認してから、未変更のUnityメッシュ記録を旧版から再利用し、Questの再デシメーションによる不要な差分も防いでいます。走路・FPV・建築・家具・街並みのUnityメッシュはバイト比較で検証します。

## ポータル

| 対象 | Unity位置 m | 色 | ボタン |
| --- | --- | --- | --- |
| カフェ → FPV | (11, 1.3, 3.45) | シアン | GO TO FPV |
| カフェ → KART | (17, 1.3, 3.45) | ピンク | GO TO KART |
| FPV/カート → カフェ | 元の帰路位置を維持 | 各エリアと同色 | RETURN TO CAFE |

フレーム幅2.94 m、行き先文字は0.58 mのフォントサイズ。選択領域は2.1 × 0.72 m、近接距離2.5 m。頭上のACTIVITY PORTALS、足元の左右矢印と色付きパッドを追加。中央に約3 mの通路を残します。移動はInteract式で、接触や通過だけではワープしません。コース側着地点・向きは旧版を継承し、カフェ戻り先はFPV (11, 0.12, 2)、KART (17, 0.12, 2)です。

## 照明

| モード | 配色と演出 |
| --- | --- |
| WARM（初期） | アンバーと淡い暖色。会話向け |
| CYBER | シアンと紫 |
| DISCO + LASERS | 青・マゼンタ・緑のゆっくりした変化とレーザー |

- ホスト/インスタンスMasterが入口・AV側で選択。Manual Syncで選択を保持し、途中参加時に適用。
- 家具モード・昼夜とは独立。カフェ専用の材質複製にRoomTint/RoomFillと発光色を適用。固定ライトマップに色と補助光を重ねる方式で、複数ライトマップを切り替える方式ではありません。
- PCは追加の影なしポイントライト4灯。Questは追加リアルタイム灯なし。
- レーザーはPC 12本、Quest 6本、各4三角形の有限長交差リボン。奥行き判定あり、中央アトリウム内に収まる対象点を向きます。
- サーバー時計からゆっくり走査、色は20秒周期。高速点滅・ストロボなし。照明はAudioLink連動ではありません。
- REDUCED MOTIONは既存の初期ONを維持。ONでは色・走査を静止。LASERS (LOCAL)は自分だけ非表示、LOW EMISSIONは減光。FPV/カート滞在中はカフェの追加灯とレーザーを停止。
- 床矢印・行き先のシアン/ピンクはモードで変更しません。

## メインステージ

内蔵スライド・発表タイマー・Q&A・固定ポインター・独自動画同期・URL入力を撤去。演台、マイク、発表者マーク、スクリーンの旧文字を除去。ステージ・斜面・画面枠・座席切替を維持し、Audienceは24席の配置だけに変更。旧 `CommonsVideoSync` は上書き更新時のコンパイル互換性のため無処理の型に置換しています。

iwaSync本体は別途導入。主画面・補助画面と配置アンカーを生成します。内蔵BGM/DJは既定OFF、HOUSE MUSICで選択。詳細は[IWASYNC_INTEGRATION_JA.md](IWASYNC_INTEGRATION_JA.md)。

## 再現と検証

Blender 4.5.14 LTSを使用。最新v0.8.0の.blendから対象オブジェクトだけを更新します。

```sh
blender --background --python-exit-code 1 --python Blender/apply_cafe_experience.py
blender --background --python-exit-code 1 --python Blender/export_world.py
blender --background --python-exit-code 1 --python Blender/verify_cafe_source.py
python Blender/preserve_base_meshes.py
python Blender/validate_cafe_experience.py
blender --background --python-exit-code 1 --python Blender/validate_world.py
blender --background --python-exit-code 1 --python Blender/validate_kart.py
python Blender/validate_csharp.py
```

旧版比較には基準コミットを持つGitチェックアウトが必要です。通常の全体再生成 `build_world.py` も最後に同じカフェ更新処理を実行します。

- [既存オブジェクトと入口の見通し](cafe_source_preservation.json)
- [Unity用メッシュ・コース仕様の差分](cafe_update_validation.json)
- [世界形状](validation_report.json) / [カート形状](kart_validation.json) / [C#構文](csharp_syntax_report.json)
- 画像：更新モデルのBlender Cyclesレンダー。Unityシェーダーの配色・レーザー配置を参考にした照明プレビューです。
- Unity/Udon/Shaderコンパイル、ベイク、複数人同期、VR/Quest実機、iwaSync導入、VRChatアップロードは未実施。
