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

import pymysql

logger = logging.getLogger(__name__)


class BaiduNewsSpider(scrapy.Spider):
    name = "baidunews"
    # allowed_domains = ["chinaipo.com"]
    start_urls = [
    ]


    def __init__(self, *args, **kwargs):
        # self.mysql_host = kwargs['mysql_host']
        # self.mysql_port = kwargs['mysql_port']
        # self.mysql_user = kwargs['mysql_user']
        # self.mysql_passwd = kwargs['mysql_passwd']
        # self.mysql_db = kwargs['mysql_db']
        # self.mysql_charset = kwargs['mysql_charset']
        self.keywords = kwargs['keywords']

        super(BaiduNewsSpider, self).__init__(*args, **kwargs)

    # @classmethod
    # def from_crawler(cls, crawler):
    #     mysql_host = crawler.settings.get('INDUSTRY_MYSQL_HOST')
    #     mysql_port = crawler.settings.get('INDUSTRY_MYSQL_PORT', 3306)
    #     mysql_user = crawler.settings.get('INDUSTRY_MYSQL_USER', 'root')
    #     mysql_passwd = crawler.settings.get('INDUSTRY_MYSQL_PASSWD')
    #     mysql_db = crawler.settings.get('INDUSTRY_MYSQL_DB')
    #     mysql_charset = crawler.settings.get('INDUSTRY_MYSQL_CHARSET', 'utf8')
    #     return cls(mysql_host=mysql_host, mysql_port=mysql_port, mysql_user=mysql_user, mysql_passwd=mysql_passwd, mysql_db=mysql_db, mysql_charset=mysql_charset)

    def start_requests(self):
        # client = pymysql.connect(host=self.mysql_host, port=self.mysql_port,                    user=self.mysql_user,passwd=self.mysql_passwd, db=self.mysql_db, charset=self.mysql_charset)
        # sql ="SELECT * FROM `company` WHERE `is_chinaipo`=0"
        # with client.cursor() as cursor:


        return [
            Request('https://news.baidu.com/news?tn=bdapinewsearch&word={0}&pn=0&rn=50&ct=0'.format(
                self.keywords), callback=self.parse_baidu)
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
