# Unity MCPへの引き継ぎ — v0.5.0

取得元: https://github.com/Xenoah/vrcworld_tech-tech-cafe

これはUnityの `Assets` 導入用リポジトリです。Unityプロジェクト本体、VRChat SDK、UdonSharp、生成済みシーンは同梱していません。ブラウザ歩行ビューアは別管理です。

## 取得からシーン生成まで

1. **mainブランチ**のリポジトリを `git clone` / `git pull --ff-only` で取得する。ローカル変更がある場合は上書きせず差分を確認する。
2. VCCで作成したWorlds / Built-inプロジェクトをUnityで開く。SDKとUdonSharpの導入・コンパイル完了を待つ。制作基準はUnity 2022.3.22f1 / SDK 3.10.5。実際の対応版はVCCとVRChat公式の指定に従う。
3. `Unity/Assets/TheCommons` と同階層の `TheCommons.meta` を、対象プロジェクトの `Assets` にコピーする。子ファイルの `.meta` も保持する。既存の `Generated` シーンを削除しない。
4. PCのBloomも生成する場合は、Package Managerで `com.unity.postprocessing@3.4.0` を導入する。C#実行対応MCPなら `UnityEditor.PackageManager.Client.Add("com.unity.postprocessing@3.4.0");` を使用し、導入と再コンパイルを待つ。未導入では器具グローのみ生成される。Unity MCPからAssetDatabaseのRefresh / 再インポートを行い、ConsoleのC#・UdonSharpエラーを確認する。接続しているMCPの実際のツール名・引数を使う。
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

## v0.4.0で追加した確認

- カフェ入口のVECTORからFPVへ、RETURNからカフェへ往復。Unity座標でFPV着地点 `(-42.5, 0.12, 2)`、カフェ着地点 `(19.3, 0.12, 2.5)`。
- 開口3.2 × 3.0 mの8ゲートをVRC+ Camera Droneで飛行。ワールド／インスタンスのDrones許可を確認。独自ドローンギミックは不要。
- 操縦席4席、観戦席3席、柵と出入口、色・番号・床矢印を確認。Quest実機のフレーム時間と操縦感を測り、密度を調整。
- 両側の時間パネルで朝昼夕夜・±1時間・CYCLE / HOLDを確認。ホスト以外の操作制限、途中参加、所有者退出後を確認。
- PCのPBR・ベイク済み反射・弱いBloom、Questの軽量な補助光・器具グローを確認。SOFT GLOW / LOW EMISSIONで眩しさを落とせること。
- 遠い側のRendererを非表示にしてもワープ先の床・Udonが維持されること。

時間帯は空・霧・環境色・補助光の連続補間。ライトマップ／反射は静的1組です。新シーンを生成して再ベイクしてください。Release v0.4.0のパッケージにこの追加更新を収録しています。

PCでPPSを導入した場合は、`VRCWorld` のReference Cameraに `LGT_PC_ReferenceCamera` が入り、PostProcessLayerのVolume LayerがWater、`LGT_PC_BloomVolume` もWaterに設定されていることを確認してください。参照カメラのCameraは無効、HDRは有効です。SOFT GLOWはVolumeと器具グローをまとめて切り替えます。

## v0.5.0 カート・CVS2

- カフェ入口のAPEX / KARTから移動し、観戦側RETURN / CAFEで戻る。Unity座標X=180〜500、Z=0〜300。路面Y=0.35／3.95／7.55 m。
- 8 m幅の連続MeshCollider。橋下6.75 m、最大勾配8.95%、最小中心旋回半径14.73 m。PC／Questで走行形状を共通化。
- シーン生成後、所有者のCVS2車両を6つの空Transform `KART_ExternalVehicleAnchors/CVS2_Bay_01`〜`06` を目安に配置。車高・タイヤ・所有権・復帰設定はCVS2説明書に従う。詳細は `Documentation/CVS2_INTEGRATION_JA.md`。
- 観戦側時間パネル、朝昼夕夜、エリア切替時の霧・音声を確認。Reference CameraはPC／Questともfar clip 900 m、Camera無効、HDRはPCのみ。
- 外部CVS2車両を建築Renderer配列へ登録しない。建築が非表示でも物理とUdonを維持する。
- 大面積のライトマップ・メモリ・実機フレーム時間を確認。Unity／CVS2実走は未検証。
- Release画像4枚はBlender実モデル。今後も撮影元を明記し、PNGをRelease Assetsへ添付する。
