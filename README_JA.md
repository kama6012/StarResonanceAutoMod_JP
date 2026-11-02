# Star Resonance Auto Module Filter（日本語対応版）

[English](README.md) | [中文](README_ZH.md)

ブループロトコル：スターレゾナンスのモジュール情報をパケットから取得し、属性の条件に合う組み合わせを計算します。

## このフォークの変更

- 新形式の `Item.ModPartLevel.Levels` を属性 ID で読み込みます。新形式のマップが空、または存在しない場合は、旧形式の `Mod.ModInfos.InitLinkNums` を使います。
- 通常アイテムが同じバッグに含まれる場合や、旧形式の付加情報がない場合にも対応しました。値のない属性・モジュールはスキップします。
- 表示言語の既定値を英語に変更しました。
- `--lang ja` でヘルプ、操作案内、結果、Python のログを日本語にできます。カテゴリ名・属性名も日本語で指定できます。`--lang zh` で中国語も利用できます。

参照: [モジュール解析の更新コミット](https://github.com/fudiyangjin/resonance-logs-cn/commit/c7a1b73649c3fda73f10d3fdd946027f5d548050)。2026-11-02 の参照リポジトリ HEAD でも同じ解析方式を確認しました。日本を含む各地域の実際の通信での動作は未確認です。

日本語のモジュール名とパワーコア名は、[スタレゾ Wiki「モジュール」](https://bpsr-wiki.regnas.blue/wiki/戦闘系育成要素/モジュール?oldid=8447)の表記を参照しています。例えば「基本 攻撃型 モジュール」「卓越 防御型 モジュール」「特攻ダメージ強化」「集中・会心」です。Wiki には数値 ID がないため、既存の属性 ID と効果・意味を対応させています。Wiki に記載のない `5500104` / `5500204` / `5500304` の「（優選）」は暫定表記です。従来の日本語属性名（例: `会心集中`）とカテゴリ名 `守護` も入力時の別名として利用できます。C++ / GPU ライブラリ内部の診断や OS のメッセージは英語の場合があります。

## ソースから実行する

既存の上流リリースの exe には、このフォークの変更は含まれていません。

Windows 10/11、Python 3.10 以上、Git、Visual Studio Build Tools（C++ デスクトップ開発と Windows SDK）が必要です。パケットの取得には Npcap も必要です。オフライン計算ではパケットを取得しません。

PowerShell で実行します。

```powershell
git clone https://github.com/kama6012/StarResonanceAutoMod.git
cd StarResonanceAutoMod
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FORCE_CPU = '1'
cd cpp_extension
python setup.py build_ext --inplace
cd ..
python star_railway_monitor.py --lang ja --help
```

CUDA / OpenCL ビルドは [英語の説明](README.md)を参照してください。exe を PyInstaller で作成する場合は `--add-data "locales/ja.json;locales"` を指定して翻訳ファイルを含めてください。C++ 拡張やキャプチャ関連ライブラリも必要です。

## 使用例

```powershell
# ネットワークインターフェースの一覧
python star_railway_monitor.py --lang ja --list

# 自動選択してキャプチャを開始し、ゲームに再ログインしてキャラクターを選択
python star_railway_monitor.py --lang ja -a

# 攻撃モジュールから、指定した属性を持つものを選別
python star_railway_monitor.py --lang ja -a -c 攻撃 -attr 筋力強化 集中・会心

# 組み合わせ全体の集中・会心を 8 以上にする
python star_railway_monitor.py --lang ja -a -mas 集中・会心 8

# 回復系属性をスコア計算から除外（モジュール自体を除外する指定ではありません）
python star_railway_monitor.py --lang ja -a -exattr 特攻回復強化 マスタリー回復強化

# プログラムと同じフォルダーの modules.vdata を使って再計算
python star_railway_monitor.py --lang ja --load-vdata -cs 5
```

キャプチャした情報は `modules.vdata` に保存されます。リポジトリに最初から含まれるファイルは上流のサンプルです。自身のモジュールを使うには、先にキャプチャしてください。

言語指定を省略すると英語になります。英語・日本語・中国語の入力は表示言語にかかわらず利用できます。空白を含む英語名は `-attr "Strength Boost" "Crit Focus"` のように引用符で囲みます。

カテゴリは `攻撃` / `防御` / `支援` / `すべて`（英語: `attack` / `guardian` / `support` / `all`）です。

## 日本語の属性名

| ID | 日本語入力 | 英語入力 |
|---|---|---|
| 1110 | 筋力強化 | Strength Boost |
| 1111 | 敏捷強化 | Agility Boost |
| 1112 | 知力強化 | Intellect Boost |
| 1113 | 特攻ダメージ強化 | Special Attack |
| 1114 | 精鋭打撃 | Elite Strike |
| 1205 | 特攻回復強化 | Healing Boost |
| 1206 | マスタリー回復強化 | Healing Enhance |
| 1407 | 集中・詠唱 | Cast Focus |
| 1408 | 集中・攻撃速度 | Attack SPD |
| 1409 | 集中・会心 | Crit Focus |
| 1410 | 集中・幸運 | Luck Focus |
| 1307 | 魔法耐性 | Resistance |
| 1308 | 物理耐性 | Armor |
| 2104 | 極・ダメージ増強 | DMG Stack |
| 2105 | 極・適応力 | Agile |
| 2204 | 極・HP凝縮 | Life Condense |
| 2205 | 極・応急処置 | First Aid |
| 2404 | 極・HP変動 | Life Wave |
| 2405 | 極・HP吸収 | Life Steal |
| 2406 | 極・幸運会心 | Team Luck&Crit |
| 2304 | 極・絶境守護 | Final Protection |

## 検証

```powershell
python -m unittest discover -s tests -v
```

新形式のバイナリ、旧形式へのフォールバック、欠落値、混在する通常アイテム、同梱の旧データ、日本語入出力と翻訳のプレースホルダーを確認します。C++ 拡張が未ビルドの場合はネイティブ連携テストがスキップされます。CI は Windows / Linux で CPU 拡張をビルドしてからテストします。

Protobuf 定義の再生成手順は [protocol/README.md](protocol/README.md) にあります。
