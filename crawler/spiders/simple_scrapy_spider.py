import scrapy
import datetime
import re
from pathlib import Path
from crawler.spiders.items import ThreadItem
import json


def _coerce_persist_to_disk(value, default=True):
    """CLI の -a persist_to_disk=false など文字列でも正しく扱う。"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on")


class SimpleScrapySpider(scrapy.Spider):
    name = "simple_scrapy_spider"

    def __init__(
        self, url=None, thread_data_dir=None, persist_to_disk=True, *args, **kwargs
    ):
        super(SimpleScrapySpider, self).__init__(*args, **kwargs)

        if not url or not url.strip():
            raise ValueError("url が指定されていません")

        self.persist_to_disk = _coerce_persist_to_disk(persist_to_disk, default=True)
        self.start_urls = [url.strip()]
        self.thread_data_dir = Path(thread_data_dir or "data/simple")
        if self.persist_to_disk:
            self.thread_data_dir.mkdir(parents=True, exist_ok=True)

    def parse(self, response):
        """スレッド詳細ページのパース（series_thread_spider と同一の抽出方法）"""
        self.logger.info(f"スレッド詳細ページをパース中: {response.url}")

        thread = {
            "title": "No Title",
            "url": response.url,
            "res_count": 0,
        }

        responses = []
        current_response = None
        thread_elements = response.css("dl.thread > *")

        for i, element in enumerate(thread_elements):
            if element.css("dt"):
                if current_response:
                    responses.append(current_response)

                current_response = {
                    "number": None,
                    "name": None,
                    "date": None,
                    "id": None,
                    "text": None,
                }

                number_text = element.css("::text").get()
                if number_text:
                    number_match = re.search(r"(\d+)", number_text)
                    if number_match:
                        current_response["number"] = int(number_match.group(1))

                name = element.css("b::text").get()
                if name:
                    current_response["name"] = name.strip()

                meta_text = "".join(element.css("::text").getall())
                date_match = re.search(
                    r"(\d{4}/\d{2}/\d{2}(?:\([月火水木金土日]\))?\s+\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)",
                    meta_text,
                )
                if date_match:
                    current_response["date"] = date_match.group(1)

                id_match = re.search(r"ID:([^\s]+)", meta_text)
                if id_match:
                    current_response["id"] = id_match.group(1)

            elif element.css("dd"):
                if current_response:
                    text_parts = []
                    for text in element.css("::text").getall():
                        text = text.strip()
                        if text:
                            text_parts.append(text)
                    if text_parts:
                        current_response["text"] = "\n".join(text_parts)

        if current_response:
            responses.append(current_response)

        thread["responses"] = responses
        thread["res_count"] = len(responses)

        thread_id_match = re.search(r"/(\d+)/?$", thread["url"])
        if thread_id_match:
            thread_id = thread_id_match.group(1)
        else:
            self.logger.error(f"スレッドIDの取得に失敗: {thread['url']}")
            return

        if self.persist_to_disk:
            thread_data_file = self.thread_data_dir / f"thread_{thread_id}.json"
            with open(thread_data_file, "w", encoding="utf-8") as f:
                json.dump(thread, f, ensure_ascii=False, indent=2)
            self.logger.info(f"スレッドデータを {thread_data_file} に保存しました")

        thread_item = ThreadItem()
        thread_item["thread_id"] = thread_id
        thread_item["title"] = thread["title"]
        thread_item["url"] = thread["url"]
        thread_item["preview_count"] = None
        thread_item["res_count"] = thread["res_count"]
        thread_item["created_at"] = None
        thread_item["board_name"] = ""
        thread_item["domain"] = ""
        thread_item["crawled_at"] = datetime.datetime.now().isoformat()
        thread_item["responses"] = responses

        yield thread_item
