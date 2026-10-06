# v0.3.0 — 詳細テクスチャ・干渉修正

技術者カフェ／交流ワールド **The Commons — Compact Edition** の制作データを公開します。28 × 18 m、2階床高4.8 m。PC版・Quest版のモデルと、Unityでシーンを生成するEditor・UdonSharpソースを収録しています。

## ダウンロード

| ファイル | 用途 |
| --- | --- |
| `The_Commons_Compact_v0.3.0.unitypackage` | Unity導入用。PC/Quest用FBX・メッシュ、9種類のテクスチャ、音源、シーン生成Editor、UdonSharpを収録 |
| `The_Commons_Compact_v0.3.0_Full.zip` | 制作データ一式。Unity用アセットに加え、編集用Blenderファイル、フォント、CAD、設計資料、プレビュー、再生成スクリプトを収録 |
| `SHA256SUMS-v0.3.0.txt` | 上記アーカイブと配布検査レポートのSHA-256 |
| `release-validation-v0.3.0.json` | 配布ファイルとソースの一致検査結果、対象コミット |

Blenderファイルは相対パスで素材とフォントを参照します。編集する場合はFull.zip全体を展開してください。

## 今回の変更

- RELAY R2 DJコントローラーに、波形表示・目盛り・操作名を描いた専用テクスチャを追加。ジョグ、ノブ、フェーダー周辺も作り込み。
- 酒瓶93本に6種類のオリジナルラベルを配置。
- エスプレッソマシンの圧力計、コーヒー袋、本の背表紙、AVラックの印刷を追加。
- 床、ステージ、階段の重複面を整理し、ちらつきの原因になる同一平面の重なりを修正。壁の接合、カウンター、手すりの重複も整理。
- 印刷用アトラスはClamp、建築素材はMirror。インポート上限をPC 1024 / Android 512に設定。
- Unity MCP向けのダイアログなしシーン生成メニューと引き継ぎ手順を追加。

PCモデルは139,940三角形・129メッシュ、Questモデルは107,773三角形・120メッシュです。

## Unityへの導入

1. VRChat Creator CompanionでWorlds / Built-in Render Pipelineのプロジェクトを作り、SDKとUdonSharpを導入します。
2. `.unitypackage` をインポートします。リポジトリから取得する場合は `Unity/Assets/TheCommons` と `.meta` をコピーしてください。
3. Unityの **The Commons → Build PC World** を実行します。Questは **Build Quest World** で別シーンを生成します。
4. ライトベイク後、VRChat SDKのBuild & Testで確認します。

Unity MCPの場合は **The Commons/MCP/Build PC World (no dialogs)** を使用できます。詳細は [UNITY_MCP_HANDOFF.md](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.3.0/UNITY_MCP_HANDOFF.md) を参照してください。

## 検証状況

Blenderでの近接レンダー、形状・UV・材質・床の重なりなど28項目、C#ソース9ファイルの構文検査を実施しました。配布アーカイブはソースとのバイト単位の一致を検査しています。

**Unity/Udonのコンパイル、シェーダー、ライトベイク、VRChat内の動作・両眼表示・複数人同期、Quest実機での検証は未実施です。** 本リリースは制作データで、生成済みシーン・ビルド済みワールド・VRChat SDK本体は含みません。VRChatへのアップロードは所有者側で行ってください。

DJコントローラーの操作面は装飾モデルです。各ノブやフェーダーを操作する音声ミキサー機能は実装していません。ブラウザ歩行ビューアは別プロジェクトとして管理しています。

詳細: [変更記録](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.3.0/Documentation/CHANGES_v0.3.0_JA.md) / [受入確認項目](https://github.com/Xenoah/vrcworld_tech-tech-cafe/blob/v0.3.0/Documentation/ACCEPTANCE_JA.md)
