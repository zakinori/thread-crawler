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

**エラーが出る場合**

Debian/Ubuntu はシステムPythonへのpipインストールを禁止しています。  
※PEP 668（externally-managed-environment）により、apt以外でシステム全体にパッケージを入れると、OS の Python が壊れるリスクがあるためブロックされます。  

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# venvから抜ける
deactivate
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

**venv環境を構築している場合（参考）**

```bash
# venv内に移動
source .venv/bin/activate
# スクリプトの実行
./run_crawler.sh
```
※run_crawler.shは.venv/bin/python3を直接使うため、事前のsource .venv/bin/activateは不要です。

※出力先: data

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

## コンバート処理

クロールしたスレッドデータの加工アプリがUTF-8未対応のためshift-JIS文字コード変換スクリプトを準備しました。  
run_crawler.sh内で実行されますが、個別にも実行可能となります。

```bash
# 一括（今回実行済み）
python3 convert_encoding.py --src data --dst convert_data

# 1ファイル
python3 convert_encoding.py --src data/viper.2ch.sc_news4vip/thread_data/thread_xxx.json --dst convert_data
```

## cron 設定（定期実行）

`run_crawler.sh` はリポジトリルートへの移動と `.venv` 内の Python 利用をスクリプト内で行うため、cron から直接呼び出せます。  
実行間隔の例: **毎週土曜日 12:00**

### 前提

- リポジトリ直下に `.venv` があり、`pip install -e .` 済みであること
- `run_crawler.sh` に実行権限があること（`chmod +x run_crawler.sh`）

### 手順など

```bash
# 登録内容の確認
crontab -l
```

| 項目 | 意味 |
|------|------|
| `0 12 * * 6` | 毎週土曜 12:00 |
| スクリプトパス | 絶対パスで指定 |
| `>> .../cron.log 2>&1` | 標準出力・標準エラーをログへ追記 |


### HTTP API（単一 URL スクレイプ）

`data/` には書き込まず、レスポンスの JSON のみでスレッドデータを返します。内部は `crawler/scrape_one_for_api.py` が子プロセスで実行されます（親プロセスと同じ Python = `.venv` を使用）。

#### 前提

- リポジトリ直下に `.venv` があり、`pip install -e .` 済みであること（環境構築を参照）
- 起動はリポジトリルートで行うこと

#### 環境変数

| 変数 | 説明 |
|------|------|
| `API_KEY` | API_KEYは必須です |
| `API_SCRAPE_ALLOWED_HOST_SUFFIXES` | 許可ホスト（カンマ区切り）。未設定時は `.2ch.sc,2ch.sc` |
| `API_SCRAPE_TIMEOUT_SEC` | スクレイプのタイムアウト秒（既定: 180） |

#### 起動

systemd設定例
※thread-crawler-api.service

```bash
sudo cp thread-crawler-api.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now thread-crawler-api
sudo systemctl status thread-crawler-api
```

ヘルスチェック:

```bash
curl -sS "http://127.0.0.1:8000/health"
```

#### リクエスト例

```bash
# 認証あり（起動時の API_KEY と同じ値をヘッダに付与）
curl -sS -X POST "http://127.0.0.1:8000/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"url":"https://viper.2ch.sc/test/read.cgi/news4vip/1771308334/"}'
```

#### ワーカーのみ CLI で実行

```bash
PYTHONPATH=. .venv/bin/python3 -m crawler.scrape_one_for_api "https://..."
```
