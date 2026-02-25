#!/usr/bin/env python
"""
crawler/simple_scrapy.json を読み込み、設定ファイルに存在するURLを1ページずつスクレイピングするスクリプト。

出力: data/simple/thread_{thread_id}.json

オプション:
    --config=PATH  simple_scrapy.json のパス（デフォルト: crawler/simple_scrapy.json）
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from twisted.internet import reactor
from twisted.internet import defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crawler.spiders.simple_scrapy_spider import SimpleScrapySpider


os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")

# このスクリプトと同じディレクトリの simple_scrapy.json をデフォルトとする
_DEFAULT_CONFIG = Path(__file__).parent / "simple_scrapy.json"


def setup_logging(settings):
    """ログ設定の初期化"""
    log_dir = settings.get("LOG_DIR")
    os.makedirs(log_dir, exist_ok=True)

    log_file = settings.get("LOG_FILE")
    log_level = settings.get("LOG_LEVEL", "INFO")

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter(
            settings.get("LOG_FORMAT"), datefmt=settings.get("LOG_DATEFORMAT")
        )
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        logging.Formatter(
            settings.get("LOG_FORMAT"), datefmt=settings.get("LOG_DATEFORMAT")
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    scrapy_logger = logging.getLogger("scrapy")
    scrapy_logger.setLevel(log_level)
    scrapy_logger.addHandler(file_handler)
    scrapy_logger.addHandler(console_handler)


def load_url_list(config_path=None):
    """simple_scrapy.json を読み込み、URLのリストを返す"""
    path = Path(config_path or _DEFAULT_CONFIG)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error(f"設定ファイルが見つかりません: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"設定ファイルのJSON解析エラー: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        logging.error("設定ファイルはURLの配列である必要があります")
        sys.exit(1)

    return [u.strip() for u in data if u and str(u).strip()]


def parse_arguments():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(
        description="指定URLを1ページずつスクレイピングするスクリプト"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="simple_scrapy.json のパス（未指定時は crawler/simple_scrapy.json）",
    )
    return parser.parse_args()


def main():
    """メイン関数"""
    try:
        args = parse_arguments()
        settings = get_project_settings()
        setup_logging(settings)
        logger = logging.getLogger(__name__)

        config_path = args.config if args.config else str(_DEFAULT_CONFIG)
        urls = load_url_list(config_path)
        if not urls:
            logger.info("クロール対象のURLがありません")
            return

        data_dir = Path(settings.get("DATA_DIR", "data"))
        thread_data_dir = data_dir / "simple"
        thread_data_dir.mkdir(parents=True, exist_ok=True)

        runner = CrawlerRunner(settings)

        @defer.inlineCallbacks
        def crawl_seq(index=0):
            if index >= len(urls):
                logger.info(f"シンプルスクレイピング完了（合計 {len(urls)} URL）")
                reactor.stop()
                return
            url = urls[index]
            logger.info(f"クローラーを開始します: {url}")
            yield runner.crawl(
                SimpleScrapySpider,
                url=url,
                thread_data_dir=str(thread_data_dir),
            )
            logger.info(f"クローラーが完了しました: {url}")
            yield crawl_seq(index + 1)

        def on_err(f):
            logger.error("クロール中にエラーが発生しました: %s", f.getErrorMessage())
            reactor.stop()

        d = crawl_seq()
        d.addErrback(on_err)
        reactor.run()

    except KeyboardInterrupt:
        print("ユーザーによってクローラーが中断されました")
        sys.exit(0)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
