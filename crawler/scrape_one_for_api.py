#!/usr/bin/env python3
"""
1 URL だけシンプルスクレイピングし、結果を標準出力に JSON で返す（API ワーカー用）。

- data/ には書き込まない（SimpleScrapySpider の persist_to_disk=False）
- JsonWriterPipeline は使わず ApiCapturePipeline のみ有効化

使用例:
  PYTHONPATH=. python3 -m crawler.scrape_one_for_api "https://..."
"""

import argparse
import json
import logging
import os
import sys

os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")

from twisted.internet import defer, reactor  # noqa: E402
from scrapy.crawler import CrawlerRunner  # noqa: E402
from scrapy.utils.project import get_project_settings  # noqa: E402

from crawler.api_capture_pipeline import (  # noqa: E402
    get_captured_item,
    reset_captured_item,
)
from crawler.spiders.simple_scrapy_spider import SimpleScrapySpider  # noqa: E402


def _emit_error(message: str, code: int = 1) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(description="1 URL をスクレイプし JSON を stdout に出力")
    parser.add_argument("url", help="スレッド read.cgi URL")
    args = parser.parse_args()

    url = args.url.strip()
    if not url:
        _emit_error("url が空です")

    logging.getLogger("scrapy").setLevel(logging.ERROR)

    reset_captured_item()
    settings = get_project_settings()
    settings.set("ITEM_PIPELINES", {"crawler.api_capture_pipeline.ApiCapturePipeline": 300})
    settings.set("LOG_LEVEL", "ERROR")

    runner = CrawlerRunner(settings)
    errors = []

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(
            SimpleScrapySpider,
            url=url,
            thread_data_dir=".",
            persist_to_disk=False,
        )

    def on_ok(_):
        reactor.stop()

    def on_err(failure):
        errors.append(failure.getErrorMessage())
        reactor.stop()

    d = crawl()
    d.addCallbacks(on_ok, on_err)
    reactor.run()

    if errors:
        _emit_error(errors[0])

    item = get_captured_item()
    if not item:
        _emit_error("no_item_extracted")

    print(json.dumps(item, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
