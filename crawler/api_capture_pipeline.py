"""API 用: スクレイプ結果をファイルに書かずメモリに保持するパイプライン。"""

_captured_item = None


def reset_captured_item():
    global _captured_item
    _captured_item = None


def get_captured_item():
    return _captured_item


class ApiCapturePipeline:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        global _captured_item
        _captured_item = dict(item)
        return item
