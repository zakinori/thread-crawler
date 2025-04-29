import json
import datetime
from pathlib import Path
from scrapy.exceptions import DropItem
from scrapy import signals
from scrapy.exporters import JsonItemExporter


class JsonWriterPipeline:
    """スレッド情報をJSONファイルに保存するパイプライン"""
    
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.files = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            data_dir=crawler.settings.get('DATA_DIR', 'data')
        )
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_opened(self, spider):
        # # 出力ディレクトリの作成
        # output_dir = Path(self.data_dir) / datetime.datetime.now().strftime('%Y%m%d')
        # output_dir.mkdir(parents=True, exist_ok=True)
        
        # # 単一のJSONファイル（全スレッド）
        # all_threads_file = open(output_dir / f"all_threads_{spider.name}.json", 'wb')
        # self.files[spider] = all_threads_file
        # self.exporter = JsonItemExporter(all_threads_file, encoding='utf-8', ensure_ascii=False)
        # self.exporter.start_exporting()
        pass
    
    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        for file in self.files.values():
            file.close()
    
    def process_item(self, item, spider):
        # 全スレッドファイルにエクスポート
        self.exporter.export_item(item)
        
        # 個別のJSONファイル（スレッドごと）
        if 'thread_id' in item:
            thread_dir = Path(self.data_dir) / 'threads'
            thread_dir.mkdir(parents=True, exist_ok=True)
            
            thread_file = thread_dir / f"{item['thread_id']}.json"
            with open(thread_file, 'w', encoding='utf-8') as f:
                json.dump(dict(item), f, ensure_ascii=False, indent=2)
        
        return item