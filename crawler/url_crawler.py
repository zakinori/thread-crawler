#!/usr/bin/env python
"""
URLリストを読み込んで順次クロールするスクリプト

オプション:
    --limit=LIMIT    クロールするスレッドの最大数
    --days=DAYS      過去何日分のスレッドをクロールするか
    --domain=DOMAIN  ドメイン名（例：example.com）
    --name=NAME      ボード名（例：news4vip）
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.url_thread_spider import UrlThreadSpider


# 環境設定
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


def read_urls(file_path: str):
    """URLリストファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"URLリストファイルが見つかりません: {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"URLリストファイルの読み込み中にエラーが発生しました: {str(e)}")
        sys.exit(1)


def parse_arguments():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description='URLリストクローラー')
    parser.add_argument('--limit', type=int, help='クロールするスレッドの最大数')
    parser.add_argument('--days', type=int, help='過去何日分のスレッドをクロールするか')
    parser.add_argument('--domain', type=str, required=True, help='ドメイン名（例：example.com）')
    parser.add_argument('--name', type=str, required=True, help='ボード名（例：news4vip）')
    return parser.parse_args()


def main():
    """メイン関数"""
    try:
        # コマンドライン引数のパース
        args = parse_arguments()
        
        # 設定の読み込み
        settings = get_project_settings()
        
        # ログ設定の初期化
        setup_logging(settings)
        logger = logging.getLogger(__name__)
        
        if args.limit:
            settings.set('CLOSESPIDER_ITEMCOUNT', args.limit)
        
        # URLリストの読み込み
        urls = read_urls('urls.txt')
        logger.info(f"{len(urls)}件のURLを読み込みました")
        
        # 各URLに対してクローラーを実行
        for url in urls:
            logger.info(f'クローラーを開始します: {url}')
            
            # クローラーの実行
            process = CrawlerProcess(settings)
            process.crawl(
                UrlThreadSpider,
                board={
                    'domain': args.domain,
                    'name': args.name,
                    'url': url
                },
                min_res_count=settings.get('MIN_RES_COUNT')
            )
            process.start()  # これはブロッキング呼び出し
            
            logger.info(f'クローラーが完了しました: {url}')
        
        logger.info('すべてのURLのクロールが完了しました')
        
    except KeyboardInterrupt:
        print('ユーザーによってクローラーが中断されました')
        sys.exit(0)
    except Exception as e:
        print(f'予期せぬエラーが発生しました: {str(e)}')
        sys.exit(1)


if __name__ == "__main__":
    main() 