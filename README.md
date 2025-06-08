# thread-crawler

プレビュー数の多いスレッドを収集するクローラーシステムです。

## 機能

- プレビュー数が多いスレッドを検出
- スレッドのレス内容を収集
- JSONファイル形式でデータを保存
- robots.txtに対応
- スクレイピング間隔の設定による負荷軽減

## 環境構築

### 前提条件

- Python 3.8以上

### インストール

```bash
# 依存パッケージのインストール
pip install -e .

# [option] 仮想環境の作成
python -m venv venv

# [option] 仮想環境の有効化
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 環境変数の設定

`.env`ファイルを作成し、必要な設定を記述します：

```env
# データ保存先ディレクトリ
DATA_DIR=data

# クロール設定
MIN_PREVIEW_COUNT=100

https://2ch.sc/2ch.html
https://maguro.2ch.sc/fortune/subback.html
https://viper.2ch.sc/news4vip/subback.html
https://nozomi.2ch.sc/be/subback.html
https://nozomi.2ch.sc/retro/subback.html
https://ikura.2ch.sc/oversea/subback.html
```

## 使用方法

### 基本的な実行方法

```bash
# 実行コマンド
PYTHONPATH=$PYTHONPATH:. python3 crawler/main.py

PYTHONPATH=$PYTHONPATH:. python3 crawler/url_crawler.py --domain ikura.2ch.sc --name oversea
PYTHONPATH=$PYTHONPATH:. python3 crawler/url_crawler.py --domain maguro.2ch.sc --name fortune
PYTHONPATH=$PYTHONPATH:. python3 crawler/url_crawler.py --domain nozomi.2ch.sc --name be
PYTHONPATH=$PYTHONPATH:. python3 crawler/url_crawler.py --domain nozomi.2ch.sc --name retro
PYTHONPATH=$PYTHONPATH:. python3 crawler/url_crawler.py --domain viper.2ch.sc --name news4vip
```
