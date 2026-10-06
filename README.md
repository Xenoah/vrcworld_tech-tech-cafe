# vrcworld_tech-tech-cafe

VRChat用の技術者カフェ／交流ワールド制作データ。内部プロジェクト名は **The Commons — Compact Edition**、収録モデルは **v0.3.0** です。

![ワールドの入口からのプレビュー](Preview/01_Entrance_160cm.png)

28 × 18 m、2階床高 4.8 m。バーカウンター、カフェ、発表ステージ、吊り下げDJブース、展示ギャラリー、静かなアーカイブルームを配置しています。

v0.3.0ではDJ機材・酒ラベル・カフェ小物を作り込み、床・ステージ・階段の同一面重複を修正しました。[変更内容](Documentation/CHANGES_v0.3.0_JA.md) / [Unity MCP引き継ぎ](UNITY_MCP_HANDOFF.md)

## Unityへ導入

1. VRChat Creator Companionで **Worlds / Built-in Render Pipeline** のプロジェクトを作成します。制作時の基準は **Unity 2022.3.22f1 / VRChat SDK 3.10.5** です。SDKとUdonSharpはVCC側で導入してください。
2. このリポジトリの `Unity/Assets/TheCommons` を、VCCで作成したプロジェクトの `Assets` にコピーします。`.meta` も一緒にコピーしてください。
3. Unity上部メニューの **The Commons → Build PC World** を実行します。
4. **The Commons → Bake lighting** でライトベイクし、VRChat SDKの **Build & Test** で確認します。
5. Quest版は **Build Quest World** で別シーンを生成し、Android向けにテストします。

生成シーンは `Assets/TheCommons/Generated/PC_日時/TheCommons.unity` またはQuest用ディレクトリに保存されます。詳しい操作・差し替え・再生成方法は [README_JA.md](README_JA.md) を参照してください。

**これはワールド制作データです。Unity/Udonのコンパイル、ライトベイク、VRChat内の動作、複数人同期、Quest実機の確認は未実施です。ビルド済みのワールドではありません。**

## 収録内容

| ディレクトリ | 内容 |
| --- | --- |
| [Blender/](Blender/) | 編集用 `.blend`、モデル再生成・書き出しスクリプト、使用フォント |
| [Unity/Assets/TheCommons/](Unity/Assets/TheCommons/) | PC/Quest用FBX、Unity用メッシュ、シーン生成Editor、UdonSharp、シェーダー |
| [Unity/Assets/TheCommons/Textures/](Unity/Assets/TheCommons/Textures/) | 木・左官・テラゾー・黒皮鋼・真鍮・織布の建築素材6種＋DJ・酒ラベル・小物用アトラス3種 |
| [Unity/Assets/TheCommons/Media/](Unity/Assets/TheCommons/Media/) | 発表スライド・展示ポスター |
| [Unity/Assets/TheCommons/Audio/](Unity/Assets/TheCommons/Audio/) | 環境音・アンビエント・DJ用のオリジナル音源 |
| [CAD/](CAD/) / [SourceDesign/](SourceDesign/) | 実装差分図、元図面、設計資料 |
| [Documentation/](Documentation/) | 寸法検査・構文検査・受入確認・素材生成記録 |
| [Preview/](Preview/) | 制作モデルの静止画8枚とglTF（外部参照形式） |

### ワールド内の機能

- Lounge / Academic / DJ / Quiet Nightの4モード。
- 発表スライド、15分/5分タイマー、Q&A、画面ポインター。
- URL動画の再生と同期、主画面と上階補助画面。
- 明示的な操作による着席、上下階の移動ポータル。
- 動き・発光・DJ演出のローカル設定、音量ゾーン。

これらはUdonSharpソースとして収録しています。実機での確認項目は [ACCEPTANCE_JA.md](Documentation/ACCEPTANCE_JA.md) に記載しています。

## モデルと素材

| 書き出しモデル | 三角形数 | メッシュ数 |
| --- | ---: | ---: |
| PC | 139,940 | 129 |
| Quest | 107,773 | 120 |

数値は書き出した全景の形状検査結果です。実機FPSや描画負荷の実測値ではありません。

建築素材6種は **Mirror（鏡像反復）**、印刷用アトラス3種は **Clamp** を使用します。通常のRepeatで画像端が完全一致することは保証していません。元CADから補完した箇所は [CAD_CHANGES_JA.md](Documentation/CAD_CHANGES_JA.md) で追跡できます。

## 制作・管理

- `.blend` と全アセットを通常のGitファイルとして管理します。Git LFSは使用していません。
- `.blend` は圧縮保存し、画像とフォントをリポジトリ内の相対パスで参照します。Blenderファイル単体ではなく、リポジトリ全体を取得してください。
- プレビューモデルは `Preview/The_Commons_Compact.gltf` と `.bin` に分離し、同じテクスチャを参照します。パッケージ整理による形状・PNGの変更はありません。
- 再生成後のGit用整理は `Blender/prepare_repository_assets.py` をBlenderのPython環境で実行します。元のGLBは生成できますがGit対象外です。
- Unityの `Library`、キャッシュ、ビルド出力、生成シーンはGit対象外です。
- SDK本体とAudioLink本体は同梱していません。
- フォントの権利表記は [DejaVu_Font_License.txt](Documentation/DejaVu_Font_License.txt) を参照してください。
- ブラウザ歩行ビューアは別プロジェクトとして管理します。

制作データの内容と検証区分は [README_JA.md](README_JA.md)、GitHub登録用の整理記録は [repository_import.json](Documentation/repository_import.json) に記載しています。
