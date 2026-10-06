# Unity MCPへの引き継ぎ — v0.3.0

取得元: https://github.com/Xenoah/vrcworld_tech-tech-cafe

これはUnityの `Assets` 導入用リポジトリです。Unityプロジェクト本体、VRChat SDK、UdonSharp、生成済みシーンは同梱していません。ブラウザ歩行ビューアは別管理です。

## 取得からシーン生成まで

1. リポジトリを `git clone` / `git pull --ff-only` で取得する。ローカル変更がある場合は上書きせず差分を確認する。
2. VCCで作成したWorlds / Built-inプロジェクトをUnityで開く。SDKとUdonSharpの導入・コンパイル完了を待つ。制作基準はUnity 2022.3.22f1 / SDK 3.10.5。実際の対応版はVCCとVRChat公式の指定に従う。
3. `Unity/Assets/TheCommons` と同階層の `TheCommons.meta` を、対象プロジェクトの `Assets` にコピーする。子ファイルの `.meta` も保持する。既存の `Generated` シーンを削除しない。
4. Unity MCPからAssetDatabaseのRefresh / 再インポートを行い、ConsoleのC#・UdonSharpエラーを確認する。接続しているMCPの実際のツール名・引数を使う。
5. 現在のシーンを保存してから、メニュー **`The Commons/MCP/Build PC World (no dialogs)`** を実行する。C#実行に対応するMCPなら `CommonsWorldBuilder.BuildPCForMCP();` でも同じ。未保存のシーンがあると停止する。
6. Consoleの `THE COMMONS scene created:` を読む。生成先は `Assets/TheCommons/Generated/PC_yyyyMMdd_HHmmss_fff/TheCommons.unity`。完了ダイアログは出ない。既存シーンへモデルを追加するのではなく、新しいシーンを生成する。
7. `The Commons/Bake lighting` を実行してベイク完了を待ち、VRChat SDKのBuild & Testを行う。
8. Questは `The Commons/MCP/Build Quest World (no dialogs)`、または `CommonsWorldBuilder.BuildQuestForMCP();` で別生成。Android向けにテストする。

自動生成はVRChatへのアップロードを行いません。既存のBlueprint IDは所有者側で管理してください。

## この更新で確認する場所

| 場所 | 確認 |
|---|---|
| ステージ | 木の天板が点滅しない。床高0.25 m |
| 北橋の西階段側、テラス側 | 歩行・視点回転で床がちらつかない。床高4.8 m |
| 東西階段 | 踏み板と蹴込み板が競合しない。上端に隙間がない |
| RELAY DJブース | パネルに波形・目盛り・操作名、ジョグとノブの印刷位置が一致 |
| バックバー | 93本に6種類のラベル。反転・隣のラベル混入がない |
| カフェ・アーカイブ・AV室 | 圧力計、コーヒー袋、本の背表紙、ラックの印刷 |

印刷用の3画像はClamp、建築の6素材はMirror。インポート上限はPC 1024、Android 512、ミップマップ有効。ファイル名を変更する場合は `CommonsAssetImporter` とマニフェストの対応も更新してください。

DJの操作面・ノブ・フェーダーは装飾モデルです。ライブミキサーや個々の音声操作は実装していません。既存のDJモード・演出は従来のUdonSharpで制御します。

## 検証の現在地

Blender実モデルの近接レンダー、PC/Questバイナリの向き・UV・材質、床・ステージ・階段上面の重複検査、上階の回遊検査を実施。結果は `Documentation/validation_report.json`。全項目の受入表は `Documentation/ACCEPTANCE_JA.md`。

Unity EditorへのMCP接続はこの制作環境にはありません。Unity/Udonコンパイル、シェーダー、ベイク、VRChat両眼表示、同期、Quest実機は引き継ぎ先で確認してください。
