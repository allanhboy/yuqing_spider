# -*- coding: utf-8 -*-
import json
import logging
import time

import scrapy
from goose3 import Goose
from goose3.text import StopWordsChinese
from newspaper import Article
from scrapy.http import Request

# from yuqing_spider.spiders import Article
import yuqing_spider.spiders
from yuqing_spider.unit import get_encoding

logger = logging.getLogger(__name__)


class BaiduNewsSpider(scrapy.Spider):
    name = "baidunews"
    # allowed_domains = ["chinaipo.com"]
    start_urls = [
        # "https://news.baidu.com/news?tn=bdapinewsearch&word=%E6%97%A5%E6%98%8C%E5%8D%87&pn=0&rn=50&ct=0",
        # "http://news.163.com/18/0118/09/D8E3I5NR00014AEE.html",
        # "http://www.my.gov.cn/jiangyou/288798823663271936/20180314/2224291.html"
        # "http://www.ocn.com.cn/touzi/chanye/201801/vszqt19083617.shtml",
        # "http://www.sxrb.com/sxxww/dspd/ycpd/ycxw/7392687.shtml",
        # "http://www.aknews.gov.cn/news/zhengwu/zhaojunmin/2018-04-16/338467.html"
    ]
    def __init__(self, *args, **kwargs):
        self.keywords = '日昌升'

        super(BaiduNewsSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        return [
            Request('https://news.baidu.com/news?tn=bdapinewsearch&word={0}&pn=0&rn=50&ct=0'.format(self.keywords), callback=self.parse_baidu)
        ]

    def parse_baidu(self, response):
        res = json.loads(response.body, encoding='utf-8')
        if res['errno'] == 0 and 'data' in res and 'list' in res['data']:
            for item in res['data']['list']:
                yield Request(item['url'], callback=self.parse_news, meta={'item': item})

    def parse_news(self, response):
        item = response.meta['item']
       
        body = response.body.decode(get_encoding(response.body), 'ignore')

        article = Article(item['url'], language='zh')
        article.download(input_html=body, title=item['title'])
        article.parse()
        article.nlp()
        if article.text.find(self.keywords) == -1:
            pass
        else:
            news = yuqing_spider.spiders.Article(
                title=article.title,
                text=article.text,
                body=body,
                publish_time=time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.localtime(item['publicTime'])),
                thumb_img=article.top_image,
                url=item['url'],
                description=article.summary,
                companies=[{'short_name': self.keywords}],
                source_site=item['author'])
            return news
