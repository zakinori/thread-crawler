#!/bin/bash
# thread-crawler 実行スクリプト
# クローラー実行を順番に実行します

set -e  # エラーが発生したら即座に終了

echo "=========================================="
echo "thread-crawler 実行開始"
echo "=========================================="
echo ""

# クローラーを実行
echo "[1/3] クローラーを実行中..."
PYTHONPATH=$PYTHONPATH:. python3 crawler/main.py "$@"
if [ $? -ne 0 ]; then
    echo "エラー: クローラー実行に失敗しました"
    exit 1
fi
echo ""

# シンプルスクレイピングを実行（指定URLのみ1ページずつ）
echo "[2/3] シンプルスクレイピングを実行中..."
PYTHONPATH=$PYTHONPATH:. python3 crawler/simple_scrapy.py
if [ $? -ne 0 ]; then
    echo "エラー: シンプルスクレイピング実行に失敗しました"
    exit 1
fi
echo ""

# シリーズクローラーを実行
echo "[3/3] シリーズクローラーを実行中..."
PYTHONPATH=$PYTHONPATH:. python3 crawler/series_crawler.py
if [ $? -ne 0 ]; then
    echo "エラー: シリーズクローラー実行に失敗しました"
    exit 1
fi
echo ""

echo "=========================================="
echo "すべての処理が完了しました"
echo "=========================================="
