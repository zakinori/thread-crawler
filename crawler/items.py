import scrapy


class ThreadItem(scrapy.Item):
    """スレッド情報を格納するためのアイテム"""
    thread_id = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    preview_count = scrapy.Field()
    res_count = scrapy.Field()
    created_at = scrapy.Field()
    responses = scrapy.Field()
    board_name = scrapy.Field()
    domain = scrapy.Field()
    crawled_at = scrapy.Field()


class ResponseItem(scrapy.Item):
    """個々のレスを格納するためのアイテム"""
    number = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()
    id = scrapy.Field()
    text = scrapy.Field()