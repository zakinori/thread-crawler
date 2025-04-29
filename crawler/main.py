#!/usr/bin/env python
"""
thread-crawler メインスクリプト

オプション:
    --limit=LIMIT    クロールするスレッドの最大数
    --days=DAYS      過去何日分のスレッドをクロールするか
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders import ThreadSpider


# 環境設定
# from pathlib import Path
# project_root = str(Path(__file__).parent.parent.absolute())
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'crawler.settings')


def setup_logging(settings):
    """ログ設定の初期化"""
    # ログディレクトリの作成
    log_dir = settings.get('LOG_DIR')
    os.makedirs(log_dir, exist_ok=True)
    
    # ログファイルの設定
    log_file = settings.get('LOG_FILE')
    log_level = settings.get('LOG_LEVEL', 'INFO')
    
    # ファイルハンドラの設定
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        settings.get('LOG_FORMAT'),
        datefmt=settings.get('LOG_DATEFORMAT')
    ))
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        settings.get('LOG_FORMAT'),
        datefmt=settings.get('LOG_DATEFORMAT')
    ))
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Scrapyのロガーの設定
    scrapy_logger = logging.getLogger('scrapy')
    scrapy_logger.setLevel(log_level)
    scrapy_logger.addHandler(file_handler)
    scrapy_logger.addHandler(console_handler)


def load_config():
    """設定ファイルの読み込み"""
    config_path = Path('crawler/config/boards.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_arguments():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description='thread-crawler')
    parser.add_argument('--limit', type=int, help='クロールするスレッドの最大数')
    parser.add_argument('--days', type=int, help='過去何日分のスレッドをクロールするか')
    return parser.parse_args()


def main():
    """メイン関数"""
    try:
        # コマンドライン引数のパース
        args = parse_arguments()
        
        # 設定の読み込み
        config = load_config()
        settings = get_project_settings()
        
        # ログ設定の初期化
        setup_logging(settings)
        logger = logging.getLogger(__name__)
        
        # 設定を上書き
        settings.set('DOWNLOAD_DELAY', config['settings']['download_delay'])
        settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', config['settings']['concurrent_requests_per_domain'])
        settings.set('ROBOTSTXT_OBEY', True)
        
        if args.limit:
            settings.set('CLOSESPIDER_ITEMCOUNT', args.limit)
        
        # クローラーの実行
        process = CrawlerProcess(settings)
        
        # 各ボードに対してスパイダーを実行
        for board in config['boards']:
            logger.info(f'クローラーを開始します: {board["name"]} ({board["url"]})')
            process.crawl(
                ThreadSpider,
                board=board,
                min_res_count=config['settings']['min_res_count']
            )
        
        # クローラーの実行
        process.start()  # これはブロッキング呼び出し
        
        logger.info('クローラーが完了しました')
    except KeyboardInterrupt:
        print('ユーザーによってクローラーが中断されました')
        sys.exit(0)
    except Exception as e:
        print(f'予期せぬエラーが発生しました: {str(e)}')
        sys.exit(1)


if __name__ == "__main__":
    main()