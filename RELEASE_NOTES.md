# v1.7.0-jp.1

Based on [StarResonanceAutoMod v1.7.0](https://github.com/fudiyangjin/StarResonanceAutoMod/releases/tag/v1.7.0).

## 変更内容 / Changes

- S4 のモジュールパケット解析に対応。`Item.ModPartLevel.Levels`（field 21）を属性 ID で読み込み、空または未設定の場合は旧形式の `InitLinkNums` を利用します。
- 通常アイテム混在時の解析打ち切りと、旧形式データ欠落時の例外を修正。値のない属性・モジュールをスキップします。
- 表示言語の既定値を英語に変更。`--lang ja` で日本語のヘルプ、操作案内、結果と Python ログを利用できます。中国語は `--lang zh` で利用できます。
- 日本語のモジュール名・パワーコア名は [スタレゾ Wiki（版 8447）](https://bpsr-wiki.regnas.blue/wiki/戦闘系育成要素/モジュール?oldid=8447) を参考に対応。数値 ID は既存の意味・効果から対応づけています。
- 精選系はユーザー確認に基づき「EXC攻撃型モジュール・精選」「EXC支援型モジュール・精選」「EXC防御型モジュール・精選」に修正。
- 日本語属性名入力は中点 `・` の省略を許容。極系では `極・` も省略でき、`極・HP吸収` / `極HP吸収` / `HP吸収` は同じ属性として扱います。`-attr` / `-exattr` / `-mas` すべてに適用されます。以前の日本語名も別名として利用できます。
- Windows の CPU / CUDA 版 exe をビルドするリリースワークフローを追加。日本語翻訳、ネイティブ拡張を同梱し、パッケージ化した exe でも三言語ヘルプと新形式データのオフライン計算を検証します。
- リポジトリを **StarResonanceAutoMod_JP** に改名。

English: supports S4 module values with legacy fallback; defaults to English;
adds Japanese CLI inputs, prompts, logs and results, Wiki-aligned terminology,
EXC preferred-module names, and optional middle dots / extreme-core prefixes.
Earlier Japanese input names remain accepted. Ships freshly built Windows CPU
and CUDA executables in the upstream-style folder layout.

## 配布構成 / Package layout

```text
StarResonanceAutoMod_JP_Release_v1.7.0-jp.1/
  StarResonanceAutoMod_Release_CPU/
    StarResonanceAutoMod.exe
    modules.vdata
    README.txt
    LICENSE
  StarResonanceAutoMod_Release_CUDA/
    StarResonanceAutoMod.exe
    modules.vdata
    README.txt
    LICENSE
  README*.md
  Update.txt
  LICENSE
```

Windows 10/11 x64。キャプチャには Npcap が必要です。CPU 版は AVX2 対応 CPU が必要です。
CUDA 版は CUDA 12.9 でビルドし、RTX 20/30/40/50 系のターゲットを含みます。
CUDA を利用できない場合は CPU にフォールバックします。このリリースでは OpenCL は含みません。
`modules.vdata` は上流に含まれるサンプルで、実際の自身のモジュールはキャプチャして取得してください。

新形式パケット対応の参照: [c7a1b736](https://github.com/fudiyangjin/resonance-logs-cn/commit/c7a1b73649c3fda73f10d3fdd946027f5d548050)。
参照リポジトリ HEAD `ed85bbb2eef66727bdfa330d8cf687dac8e6bc1a` でも同じ方式を確認しました。
各地域の実際のゲーム通信と、実 GPU 上での CUDA カーネル実行は未検証です。
C++ / GPU 内部の診断と OS メッセージは英語の場合があります。

Windows / Linux の回帰テストは CI で実行します。リリースジョブは CPU / CUDA
各ビルドの回帰テストおよび exe のスモークテストに成功した場合のみ公開します。

ソースコードはこのタグの GitHub 標準 Source code アーカイブで取得できます。
CCCL の固定サブモジュールはソースビルド時に `git submodule update --init --recursive` で取得してください。
ライセンスは上流同様 AGPL-3.0（同梱 LICENSE を参照）。
