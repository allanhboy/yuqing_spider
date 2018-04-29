# -*- coding: utf-8 -*-
import json
import time

from newspaper import Article
from scrapy.exceptions import DontCloseSpider
from scrapy.http import Request
from scrapy_redis.spiders import RedisSpider
from scrapy_redis.utils import bytes_to_str
from twisted.internet.threads import deferToThread

from yuqing_spider.unit import get_encoding, send_template

from . import Article as YuqingArticle


class BaiduNewsSpider(RedisSpider):
    name = "baidunews"
    is_running = False

    def make_request_from_data(self, data):
        data = bytes_to_str(data, self.redis_encoding)
        data = json.loads(data)
        url = data.get('url', None)
        if url and not url.strip():
            raise ValueError('url is required')

        keywords = data.get('keywords', None)
        if keywords and not keywords.strip():
            raise ValueError('keywords is required')
        self.keywords = keywords
        self.is_running = True
        return Request(url, dont_filter=True, meta={'keywords': keywords})

    def spider_idle(self):
        """Schedules a request if available, otherwise waits."""
        # XXX: Handle a sentinel to close the spider.
        if self.is_running:
            self.is_running = False
            deferToThread(send_template, self.crawler.settings)
            # send_template(self.crawler.settings)

        self.schedule_next_requests()
        raise DontCloseSpider

    def parse(self, response):
        keywords = response.meta.get("keywords")
        res = json.loads(response.body, encoding='utf-8')
        if res['errno'] == 0 and 'data' in res and 'list' in res['data']:
            for item in res['data']['list']:
                yield Request(item['url'], callback=self.parse_news, dont_filter=False, meta={'item': item, 'keywords': keywords})

    def parse_news(self, response):
        item = response.meta['item']
        keywords = response.meta.get("keywords")
        body = response.body.decode(get_encoding(response.body), 'ignore')

        article = Article(item['url'], language='zh', fetch_images= False)
        article.download(input_html=body, title=item['title'])
        article.parse()
        article.nlp()
        if article.text.find(keywords) == -1:
            pass
        else:
            news = YuqingArticle(
                title=article.title,
                text=article.text,
                body=body,
                publish_time=time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(item['publicTime'])),
                thumb_img=article.top_image,
                url=item['url'],
                description=article.summary,
                companies=[{'short_name': keywords}],
                source_site=item['author'])
            return news
