# thread-crawler

プレビュー数の多いスレッドを収集するクローラーシステムです。

## 機能

- プレビュー数が多いスレッドを検出（ボードクローラー）
- 指定URLのみを1ページずつスクレイピング（シンプルスクレイピング）
- シリーズ単位でのスレッド収集（シリーズクローラー）
- スレッドのレス内容を収集
- JSONファイル形式でデータを保存
- robots.txtに対応
- スクレイピング間隔の設定による負荷軽減
- HTTP API による単一 URL のシンプルスクレイピング（`data/` へは保存しない）

## 環境構築

### 前提条件

- Python 3.8以上

### インストール

```bash
# 依存パッケージのインストール
pip install -e .
```

## 使用方法

### 推奨: クローラー実行（一括実行）

`run_crawler.sh` は次の順で実行します：

1. ボードクローラー（`crawler/main.py`）… プレビュー数でスレッドを検出・収集
2. シンプルスクレイピング（`crawler/simple_scrapy.py`）… 指定URLのみ1ページずつ収集
3. シリーズクローラー（`crawler/series_crawler.py`）… シリーズ設定に基づく収集

#### シェルスクリプトを使用（推奨）

```bash
# デフォルト設定で実行
./run_crawler.sh

# ボードクローラーに引数を渡す場合（--limit, --days は main.py 用）
./run_crawler.sh --limit 10 --days 7
```

※出力先: data

### HTTP API（単一 URL スクレイプ）

`data/` には書き込まず、レスポンスの JSON のみでスレッドデータを返します。内部は `crawler/scrape_one_for_api.py` が子プロセスで実行されます。

#### 環境変数

| 変数 | 説明 |
|------|------|
| `API_KEY` | 設定した場合、`X-API-Key` ヘッダと一致が必要 |
| `API_SCRAPE_ALLOWED_HOST_SUFFIXES` | 許可ホスト（カンマ区切り）。未設定時は `.2ch.sc,2ch.sc` |
| `API_SCRAPE_TIMEOUT_SEC` | スクレイプのタイムアウト秒（既定: 180） |

#### 起動

リポジトリルートで:

```bash
pip install -e .
PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000
```

#### リクエスト例

```bash
curl -sS -X POST "http://127.0.0.1:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://viper.2ch.sc/test/read.cgi/news4vip/1771308334/"}'
```

#### ワーカーのみ CLI で実行

```bash
PYTHONPATH=. python3 -m crawler.scrape_one_for_api "https://..."
```

### 個別実行

#### 基本的なクローラー実行（ボード単位）

設定ファイルに書いたスレッド一覧から、スレッド数が多いスレッドをまとめてクロールします。

```bash
PYTHONPATH=$PYTHONPATH:. python3 crawler/main.py
```

※設定ファイル: crawler/boards.json

* 現在のクロール対象URL

https://2ch.sc/2ch.html
https://maguro.2ch.sc/fortune/subback.html
https://viper.2ch.sc/news4vip/subback.html
https://nozomi.2ch.sc/be/subback.html
https://nozomi.2ch.sc/retro/subback.html
https://ikura.2ch.sc/oversea/subback.html
https://toro.2ch.sc/occult/subback.html
https://maguro.2ch.sc/sfe/subback.html
https://nozomi.2ch.sc/kankon/subback.html
https://ai.2ch.sc/newsplus/subback.html
https://anago.2ch.sc/dqnplus/subback.html

#### シンプルスクレイピング（指定URLのみ）

設定ファイルに書いたURLを、1ページずつスクレイピングします。

```bash
# デフォルト（crawler/simple_scrapy.json を参照）
PYTHONPATH=$PYTHONPATH:. python3 crawler/simple_scrapy.py

# 設定ファイルを指定する場合
PYTHONPATH=$PYTHONPATH:. python3 crawler/simple_scrapy.py --config crawler/my_urls.json
```

※設定ファイル: crawler/simple_scrapy.json


#### シリーズクローラー

設定ファイルに書いたURLの一覧を、シリーズ毎にスクレイピングします。

```bash
PYTHONPATH=$PYTHONPATH:. python3 crawler/series_crawler.py
```

※設定ファイル: crawler/series.json

#### データ復元スクリプト（必要時のみ）

`_backup` から `data` へスレッドデータを復元する場合に使用します。通常のクローラー実行では不要です。

```bash
# dry-run（件数・上書き候補の確認）
python3 restore_old_threads.py

# 本実行
python3 restore_old_threads.py --execute
```

#### バックアップスクリプト（現在は無効）

`run_crawler.sh` からの自動バックアップは停止しています。手動で古いスレッドを `_backup` へ退避する場合のみ、以下を実行してください。

```bash
# デフォルト設定（3カ月前より古いデータをバックアップ）
python3 backup_old_threads.py

# カスタム設定
python3 backup_old_threads.py --data-dir data --months 3
```
