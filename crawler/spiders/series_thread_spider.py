import scrapy
import datetime
import re
from pathlib import Path
from crawler.spiders.items import ThreadItem, ResponseItem
import json
import os


class SeriesThreadSpider(scrapy.Spider):
    name = "series_thread_spider"
    
    def __init__(self, board=None, min_res_count=100, *args, **kwargs):
        super(SeriesThreadSpider, self).__init__(*args, **kwargs)
        
        # 設定値を取得
        self.board = board
        self.min_res_count = min_res_count
        
        # スタートURLを設定
        self.start_urls = [self.board['url']]
        
        # データ保存用のディレクトリを設定（thread_data_dir が指定されていればシリーズ用）
        self.base_dir = Path('data')
        if self.board.get('thread_data_dir') is not None:
            self.thread_data_dir = Path(self.board['thread_data_dir'])
            self.thread_list_file = None  # シリーズ用ではスレ一覧は更新しない
            self.existing_threads = {}
        else:
            self.session_dir = self.base_dir / f"{self.board['domain']}_{self.board['name']}"
            self.thread_list_file = self.session_dir / 'thread_list.json'
            self.thread_data_dir = self.session_dir / 'thread_data'
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.existing_threads = {}
            if self.thread_list_file.exists():
                with open(self.thread_list_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for thread in data['threads']:
                        self.existing_threads[thread['url']] = thread
        
        self.thread_data_dir.mkdir(parents=True, exist_ok=True)
    
    def parse(self, response):
        """スレッド詳細ページのパース"""
        self.logger.info(f'スレッド詳細ページをパース中: {response.url}')
        
        # スレッド情報を作成
        thread = {
            'title': self.board.get('title', 'No Title'),
            'url': response.url,
            'res_count': 0  # 後で更新
        }
        
        # レスを抽出
        responses = []
        current_response = None
        
        # dl.thread内の全要素を取得
        thread_elements = response.css('dl.thread > *')
        
        for i, element in enumerate(thread_elements):
            # dt要素（メタデータ）の処理
            if element.css('dt'):
                # 前のレスポンスがあれば保存
                if current_response:
                    responses.append(current_response)
                
                # 新しいレスポンスを作成
                current_response = {
                    'number': None,
                    'name': None,
                    'date': None,
                    'id': None,
                    'text': None
                }
                
                # レス番号を取得
                number_text = element.css('::text').get()
                if number_text:
                    number_match = re.search(r'(\d+)', number_text)
                    if number_match:
                        current_response['number'] = int(number_match.group(1))
                
                # 名前を取得
                name = element.css('b::text').get()
                if name:
                    current_response['name'] = name.strip()
                
                # 日付とIDを取得
                meta_text = ''.join(element.css('::text').getall())
                date_match = re.search(r'(\d{4}/\d{2}/\d{2}(?:\([月火水木金土日]\))?\s+\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)', meta_text)
                if date_match:
                    current_response['date'] = date_match.group(1)
                
                id_match = re.search(r'ID:([^\s]+)', meta_text)
                if id_match:
                    current_response['id'] = id_match.group(1)
            
            # dd要素（本文）の処理
            elif element.css('dd'):
                if current_response:
                    # 本文を取得
                    text_parts = []
                    for text in element.css('::text').getall():
                        text = text.strip()
                        if text:
                            text_parts.append(text)
                    
                    if text_parts:
                        current_response['text'] = '\n'.join(text_parts)
        
        # 最後のレスポンスを追加
        if current_response:
            responses.append(current_response)
        
        # スレッド情報を更新
        thread['responses'] = responses
        thread['res_count'] = len(responses)
        
        # スレッドデータを保存
        thread_id = re.search(r'/(\d+)/?$', thread['url'])
        if thread_id:
            thread_id = thread_id.group(1)
        else:
            self.logger.error(f'スレッドIDの取得に失敗: {thread["url"]}')
            return
        
        thread_data_file = self.thread_data_dir / f'thread_{thread_id}.json'
        with open(thread_data_file, 'w', encoding='utf-8') as f:
            json.dump(thread, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f'スレッドデータを {thread_data_file} に保存しました')
        
        # スレッド一覧を更新（thread_list_file がある場合のみ）
        if self.thread_list_file is not None and thread['url'] not in self.existing_threads:
            self.logger.info(f'新しいスレッドを追加: {thread["title"]} (レス数: {thread["res_count"]})')
            # 詳細データとは分け、一覧の新規スレッドは必ず有効として登録する。
            self.existing_threads[thread['url']] = {**thread, 'enable': True}
            
            # スレッド一覧をJSONファイルに保存
            with open(self.thread_list_file, 'w', encoding='utf-8') as f:
                json.dump({"threads": list(self.existing_threads.values())}, f, ensure_ascii=False, indent=2)
        
        # スレッドアイテムを生成
        thread_item = ThreadItem()
        thread_item['title'] = thread['title']
        thread_item['url'] = thread['url']
        thread_item['res_count'] = thread['res_count']
        thread_item['board_name'] = self.board['name']
        thread_item['domain'] = self.board['domain']
        thread_item['crawled_at'] = datetime.datetime.now().isoformat()
        thread_item['responses'] = responses
        
        yield thread_item
