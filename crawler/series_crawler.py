#!/usr/bin/env python
"""
series.json を読み込み、シリーズごとにスレッドをクロールするスクリプト

出力: data/series/{シリーズ名}/{serial}/thread_{thread_id}.json
（ファイル名・中身の構造は main.py と同様）

オプション:
    --limit=LIMIT    クロールするスレッドの最大数
    --days=DAYS      過去何日分のスレッドをクロールするか
"""

import os
import re
import sys
import json
import argparse
import logging
from pathlib import Path
from twisted.internet import reactor
from twisted.internet import defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from crawler.spiders.series_thread_spider import SeriesThreadSpider


# 環境設定
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'crawler.settings')

# スレッドURLからドメイン・ボード名を抽出する正規表現
# 例: https://mao.5ch.net/test/read.cgi/occult/1718661212/
THREAD_URL_PATTERN = re.compile(r'https?://([^/]+)/.*/read\.cgi/([^/]+)/\d+')


def setup_logging(settings):
    """ログ設定の初期化"""
    log_dir = settings.get('LOG_DIR')
    os.makedirs(log_dir, exist_ok=True)

    log_file = settings.get('LOG_FILE')
    log_level = settings.get('LOG_LEVEL', 'INFO')

    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        settings.get('LOG_FORMAT'),
        datefmt=settings.get('LOG_DATEFORMAT')
    ))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        settings.get('LOG_FORMAT'),
        datefmt=settings.get('LOG_DATEFORMAT')
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    scrapy_logger = logging.getLogger('scrapy')
    scrapy_logger.setLevel(log_level)
    scrapy_logger.addHandler(file_handler)
    scrapy_logger.addHandler(console_handler)


def load_series_config(config_path=None):
    """series.json を読み込む"""
    path = Path(config_path or 'crawler/series.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"設定ファイルが見つかりません: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"設定ファイルのJSON解析エラー: {e}")
        sys.exit(1)


def parse_thread_url(url):
    """スレッドURLから domain と board name を抽出する"""
    m = THREAD_URL_PATTERN.match(url.strip())
    if m:
        return {'domain': m.group(1), 'name': m.group(2)}
    return {'domain': 'unknown', 'name': 'unknown'}


def parse_arguments():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description='シリーズ別スレッドクローラー')
    parser.add_argument('--limit', type=int, help='クロールするスレッドの最大数')
    parser.add_argument('--days', type=int, help='過去何日分のスレッドをクロールするか')
    parser.add_argument('--series', type=str, default='crawler/series.json', help='series.json のパス')
    return parser.parse_args()


def main():
    """メイン関数"""
    try:
        args = parse_arguments()
        settings = get_project_settings()
        setup_logging(settings)
        logger = logging.getLogger(__name__)

        if args.limit:
            settings.set('CLOSESPIDER_ITEMCOUNT', args.limit)

        series_config = load_series_config(args.series)
        data_dir = Path(settings.get('DATA_DIR', 'data'))
        series_base = data_dir / '#series'

        # 全エントリを (series_name, entry) のリストに展開
        entries = []
        for series_name, threads in series_config.items():
            if not isinstance(threads, list):
                logger.warning(f"シリーズ '{series_name}' のエントリがリストではありません。スキップします。")
                continue
            for entry in threads:
                if not entry.get('url', '').strip():
                    continue
                entries.append((series_name, entry))

        if not entries:
            logger.info('クロール対象がありません')
            return

        min_res_count = settings.get('MIN_RES_COUNT')
        runner = CrawlerRunner(settings)

        @defer.inlineCallbacks
        def crawl_seq(index=0):
            if index >= len(entries):
                logger.info(f'シリーズクロール完了（合計 {len(entries)} スレッド）')
                reactor.stop()
                return
            series_name, entry = entries[index]
            serial = entry.get('serial', '')
            subtitle = entry.get('subtitle', '')
            url = entry.get('url', '').strip()
            thread_data_dir = series_base / series_name / str(serial)
            thread_data_dir.mkdir(parents=True, exist_ok=True)
            url_info = parse_thread_url(url)
            board = {
                'domain': url_info['domain'],
                'name': url_info['name'],
                'url': url,
                'title': subtitle or series_name,
                'thread_data_dir': str(thread_data_dir),
            }
            logger.info(f'クローラーを開始します: {series_name} #{serial} {url}')
            yield runner.crawl(
                SeriesThreadSpider,
                board=board,
                min_res_count=min_res_count
            )
            logger.info(f'クローラーが完了しました: {series_name} #{serial}')
            yield crawl_seq(index + 1)

        def on_err(f):
            logger.error('クロール中にエラーが発生しました: %s', f.getErrorMessage())
            reactor.stop()

        d = crawl_seq()
        d.addErrback(on_err)
        reactor.run()

    except KeyboardInterrupt:
        print('ユーザーによってクローラーが中断されました')
        sys.exit(0)
    except Exception as e:
        print(f'予期せぬエラーが発生しました: {str(e)}')
        sys.exit(1)


if __name__ == "__main__":
    main()
