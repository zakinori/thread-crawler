# Scrapy settings for tread-crawler

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

BOT_NAME = 'thread-crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# robots.txtの指示に従う設定
# サイトの利用規約に応じて設定を変更
ROBOTSTXT_OBEY = True

# 並列リクエスト数の設定
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 1

# ダウンロード遅延設定
DOWNLOAD_DELAY = 5
RANDOMIZE_DOWNLOAD_DELAY = True

# 自動スロットル設定
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = True

# ログ設定
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_DIR = 'logs'
LOG_FILE = f'{LOG_DIR}/crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# ログディレクトリの作成
os.makedirs(LOG_DIR, exist_ok=True)

# ログハンドラの設定
LOG_ENABLED = True
LOG_STDOUT = False
LOG_FILE_APPEND = False

# ログハンドラの詳細設定
LOG_HANDLERS = {
    'file': {
        'class': 'logging.FileHandler',
        'filename': LOG_FILE,
        'formatter': 'scrapy',
        'level': 'INFO',
    },
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'scrapy',
        'level': 'INFO',
    }
}

# フォーマッタの設定
LOG_FORMATTERS = {
    'scrapy': {
        'format': LOG_FORMAT,
        'datefmt': LOG_DATEFORMAT,
    }
}

# Crawl responsibly by identifying yourself on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# ミドルウェア設定
DOWNLOADER_MIDDLEWARES = {
    'crawler.spiders.middlewares.RotateUserAgentMiddleware': 543,
    'crawler.spiders.middlewares.CustomCookiesMiddleware': 544,
    'crawler.spiders.middlewares.CustomRetryMiddleware': 545,
}

# 項目パイプライン設定
ITEM_PIPELINES = {
    'crawler.spiders.pipelines.JsonWriterPipeline': 300,
}

# データ保存ディレクトリ設定
DATA_DIR = os.getenv('DATA_DIR', 'data')

# クローラーの制限設定
CLOSESPIDER_ITEMCOUNT = 1000
CLOSESPIDER_PAGECOUNT = 100
CLOSESPIDER_TIMEOUT = 3600  # 1時間でタイムアウト

# メモリ使用量の制限
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048  # 最大2GB
MEMUSAGE_WARNING_MB = 1024  # 1GBで警告
MEMUSAGE_NOTIFY_MAIL = []  # メール通知が必要な場合は設定