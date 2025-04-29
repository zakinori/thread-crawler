import random
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class RotateUserAgentMiddleware(UserAgentMiddleware):
    """リクエストごとにUser-Agentをランダムに変更するミドルウェア"""
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    ]
    
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
    
    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent


class CustomCookiesMiddleware:
    """必要に応じてCookieを設定するミドルウェア"""
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def process_request(self, request, spider):
        # 必要に応じてCookieを設定
        # 例: request.cookies['key'] = 'value'
        pass
    
    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class CustomRetryMiddleware:
    """カスタムリトライロジックを実装するミドルウェア"""
    
    def process_response(self, request, response, spider):
        # ステータスコードに基づいてリトライするかどうかを決定
        if response.status in [403, 429, 500, 502, 503, 504]:
            spider.logger.warning(f'リトライ対象のステータスコード: {response.status} URL: {request.url}')
            # retry_count属性がなければ初期化
            retry_count = request.meta.get('retry_count', 0)
            # 最大リトライ回数を超えていなければリトライ
            if retry_count < 3:
                spider.logger.info(f'リトライ {retry_count + 1}/3')
                retryreq = request.copy()
                retryreq.meta['retry_count'] = retry_count + 1
                retryreq.dont_filter = True
                # 指数バックオフで待機時間を設定
                retryreq.meta['download_timeout'] = 10 * (2 ** retry_count)
                return retryreq
        return response