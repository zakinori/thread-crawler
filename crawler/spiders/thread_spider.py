import scrapy
import datetime
import re
from pathlib import Path
from crawler.spiders.items import ThreadItem, ResponseItem
import json
import os
import glob


class ThreadSpider(scrapy.Spider):
    name = "thread_spider"
    
    def __init__(self, board=None, min_res_count=100, *args, **kwargs):
        super(ThreadSpider, self).__init__(*args, **kwargs)
        
        # 設定値を取得
        self.board = board
        self.min_res_count = min_res_count
        
        # スタートURLを設定
        self.start_urls = [self.board['url']]
        
        # データ保存用のディレクトリを設定
        self.base_dir = Path('data')
        self.session_dir = self.base_dir / f"{self.board['domain']}_{self.board['name']}"
        self.thread_list_file = self.session_dir / 'thread_list.json'
        self.thread_data_dir = self.session_dir / 'thread_data'
        self.update_log_file = self.session_dir / 'update.log'
        
        # ディレクトリを作成
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.thread_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存のスレッド一覧を読み込む
        self.existing_threads = {}
        if self.thread_list_file.exists():
            with open(self.thread_list_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for thread in data['threads']:
                    self.existing_threads[thread['url']] = thread
    
    def parse(self, response):
        """スレッド一覧ページのパース"""
        self.logger.info(f'スレッド一覧ページをパース中: {response.url}')
        
        # スレッド一覧を保存
        thread_list = []
        current_time = datetime.datetime.now().isoformat()
        
        # スレッド一覧から各スレッドへのリンクとレス数を抽出
        for thread in response.css('small#trad a'):
            link_text = thread.css('::text').get()
            url = thread.css('::attr(href)').get()
            
            if link_text and url and not thread.attrib.get('class') == 'sc':
                # レス数を抽出（例：「3: 創価学会被害者対策本部　part2 (835)」から「835」を取得）
                count_match = re.search(r'\((\d+)\)$', link_text)
                if count_match:
                    count = int(count_match.group(1))
                    
                    # レス数が閾値未満のスレッドはスキップ
                    if count < self.min_res_count:
                        self.logger.info(f'レス数が{self.min_res_count}未満のためスキップ: {link_text} (レス数: {count})')
                        continue
                    
                    # タイトルを抽出（例：「3: 創価学会被害者対策本部　part2 (835)」から「創価学会被害者対策本部　part2」を取得）
                    title_match = re.match(r'\d+:\s*(.+?)\s*\(\d+\)$', link_text)
                    if title_match:
                        title = title_match.group(1).strip()
                        
                        # リンクが相対パスの場合は絶対パスに変換
                        if not url.startswith('http'):
                            url = response.urljoin(url)
                        
                        # /l50を削除して全スレッドの内容を取得
                        url = url.replace('/l50', '')
                        
                        thread_info = {
                            'title': title,
                            'url': url,
                            'res_count': count
                        }
                        
                        # 既存のスレッドかチェック
                        if url in self.existing_threads:
                            existing_thread = self.existing_threads[url]
                            thread_id_match = re.search(r'/(\d+)/?$', url)
                            thread_id = thread_id_match.group(1) if thread_id_match else ''
                            data_file_exists = (
                                bool(thread_id)
                                and (self.thread_data_dir / f'thread_{thread_id}.json').exists()
                            )
                            res_increased = count > existing_thread['res_count']

                            # レス数増加、または thread_data が無い場合はクロール
                            if res_increased or not data_file_exists:
                                if res_increased:
                                    self.logger.info(
                                        f'既存のスレッドのレス数が増加: {title} '
                                        f'(前回: {existing_thread["res_count"]}, 現在: {count})'
                                    )
                                    with open(self.update_log_file, 'a', encoding='utf-8') as f:
                                        f.write(f"{current_time} UPD {title} {url}\n")
                                else:
                                    self.logger.info(
                                        f'既存スレッドのデータファイルが無いため再クロール: {title} ({url})'
                                    )
                                    with open(self.update_log_file, 'a', encoding='utf-8') as f:
                                        f.write(f"{current_time} RETRY {title} {url}\n")
                                thread_list.append(thread_info)
                                yield scrapy.Request(
                                    url=url,
                                    callback=self.parse_thread,
                                    meta={'thread': thread_info}
                                )
                            else:
                                self.logger.info(f'既存のスレッドをスキップ: {title} (レス数: {count})')
                        else:
                            thread_list.append(thread_info)
                            self.logger.info(f'新しいスレッドを追加: {title} (レス数: {count})')
                            # 更新ログに記録
                            with open(self.update_log_file, 'a', encoding='utf-8') as f:
                                f.write(f"{current_time} INS {title} {url}\n")
                            yield scrapy.Request(
                                url=url,
                                callback=self.parse_thread,
                                meta={'thread': thread_info}
                            )
        
        # スレッド一覧が空でない場合のみ保存
        if thread_list:
            # 既存のスレッド一覧と新しいスレッド一覧をマージ
            merged_threads = list(self.existing_threads.values()) + thread_list
            # URLで重複を除去
            unique_threads = {thread['url']: thread for thread in merged_threads}.values()
            
            # スレッド一覧をJSONファイルに保存（新しい形式で保存）
            with open(self.thread_list_file, 'w', encoding='utf-8') as f:
                json.dump({"threads": list(unique_threads)}, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f'スレッド一覧を {self.thread_list_file} に保存しました')
        
        # 次のページがあれば続ける
        next_page = response.css('a[href*="subback.html"]::attr(href)').get()
        if next_page:
            self.logger.info(f'次のページへ移動: {next_page}')
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)
    
    def parse_thread(self, response):
        """スレッド詳細ページのパース"""
        self.logger.info(f'スレッド詳細ページをパース中: {response.url}')
        
        # スレッド情報を取得
        thread = response.meta['thread']
        
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
        
        # # 最初のレスに前スレへのリンクがあるかチェック
        # if responses and responses[0]['number'] == 1:
        #     first_response_text = responses[0]['text']
        #     # 前スレへのリンクを検索（例：https://mi.5ch.net/test/read.cgi/news4vip/1745218274/）
        #     prev_thread_match = re.search(r'https?://[^\s]+/test/read\.cgi/[^\s]+/\d+/', first_response_text)
        #     if prev_thread_match:
        #         prev_thread_url = prev_thread_match.group(0)
        #         self.logger.info(f'前スレを発見: {prev_thread_url}')
                
        #         # 前スレの情報を作成
        #         prev_thread_info = {
        #             'title': f"前スレ: {thread['title']}",
        #             'url': prev_thread_url,
        #             'res_count': 0  # レス数は後で更新
        #         }
                
        #         # 前スレのクロールをリクエスト
        #         yield scrapy.Request(
        #             url=prev_thread_url,
        #             callback=self.parse_thread,
        #             meta={'thread': prev_thread_info}
        #         )
        
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