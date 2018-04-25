# -*- coding: utf-8 -*-
import re
from urllib.parse import urljoin

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from yuqing_spider.spiders import Article
from yuqing_spider.unit import get_encoding
import pymysql
import datetime
import pytz

class IndustryNewsSpider(scrapy.Spider):
    name = "industrynews"
    start_urls = []
    first_time = False

    def __init__(self, *args, **kwargs):
        self.mysql_host = kwargs['mysql_host']
        self.mysql_port = kwargs['mysql_port']
        self.mysql_user = kwargs['mysql_user']
        self.mysql_passwd = kwargs['mysql_passwd']
        self.mysql_db = kwargs['mysql_db']
        self.mysql_charset = kwargs['mysql_charset']
        self.pattern = re.compile(
            r'((\d{2,4}-)?)\d{1,2}-\d{1,2}( \d{1,2}:\d{1,2}(:\d{1,2})?)?')

        super(IndustryNewsSpider, self).__init__(*args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        mysql_host = crawler.settings.get('INDUSTRY_MYSQL_HOST')
        mysql_port = crawler.settings.get('INDUSTRY_MYSQL_PORT', 3306)
        mysql_user = crawler.settings.get('INDUSTRY_MYSQL_USER', 'root')
        mysql_passwd = crawler.settings.get('INDUSTRY_MYSQL_PASSWD')
        mysql_db = crawler.settings.get('INDUSTRY_MYSQL_DB')
        mysql_charset = crawler.settings.get('INDUSTRY_MYSQL_CHARSET', 'utf8')
        return cls(mysql_host=mysql_host, mysql_port=mysql_port, mysql_user=mysql_user, mysql_passwd=mysql_passwd, mysql_db=mysql_db, mysql_charset=mysql_charset)

    def start_requests(self):
        sql = """
        SELECT a.`id`  as `industry_id`, a.`industry_name` , b.`site_name`,b.`url`, list_xpath,list_thumb_img_xpath,list_title_xpath,list_url_xpath,list_description_xpath,list_publish_time_xpath,body_xpath,publish_time_xpath,next_page_xpath FROM `industry`  a
        JOIN `industry_spider_rule` b ON a.`id`=b.`industry_id`
        JOIN `spider_rule` c ON c.`id`=b.`spider_rule_id` AND c.`enable`=1
         """
        client = pymysql.connect(host=self.mysql_host, port=self.mysql_port, user=self.mysql_user,
                                 passwd=self.mysql_passwd, db=self.mysql_db, charset=self.mysql_charset)

        requests = []
        with client.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
   
            for industry_id, industry_name, site_name, url, list_xpath, list_thumb_img_xpath, list_title_xpath, list_url_xpath, list_description_xpath, list_publish_time_xpath, body_xpath, publish_time_xpath,next_page_xpath in rows:
                industry = {'id': industry_id, 'industry_name': industry_name}
                rule = {
                    'site_name': site_name,
                    'url': url,
                    'list_xpath': list_xpath,
                    'list_thumb_img_xpath': list_thumb_img_xpath,
                    'list_title_xpath': list_title_xpath,
                    'list_url_xpath': list_url_xpath,
                    'list_description_xpath': list_description_xpath,
                    'list_publish_time_xpath': list_publish_time_xpath,
                    'body_xpath': body_xpath,
                    'publish_time_xpath': publish_time_xpath,
                    'next_page_xpath': next_page_xpath
                }
                requests.append(Request(url, callback=self.parse, meta={'industry': industry, 'rule':rule}))
                
        client.close()

        return requests

    def parse(self, response):
        industry = response.meta['industry']
        rule = response.meta['rule']

        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.datetime.now(tz)

        next_page = True
        for item in response.xpath(rule['list_xpath']):
            thumb_img = item.xpath(
                rule['list_thumb_img_xpath']).extract_first()
            title = item.xpath(rule['list_title_xpath']).extract_first()
            url = item.xpath(rule['list_url_xpath']).extract_first()
            description = item.xpath(
                rule['list_description_xpath']).extract_first()
            publish_time = ''.join(item.xpath(
                rule['list_publish_time_xpath']).extract())

            m = self.pattern.search(publish_time)
            publish_time = m.group() if m else None
            if not m.group(1):
                year = now.year
                publish_time = '{0}-{1}'.format(year, publish_time)


            news = {
                'thumb_img': urljoin(response.url, thumb_img),
                'title': title,
                'url': urljoin(response.url, url),
                'description': description,
                'publish_time': publish_time,
                'industries': [industry],
                'source_site': rule['site_name']
            }
            
            if not self.first_time:
                time = [int(t) for t in re.split(' |-|:', publish_time)][:3]
                time = datetime.date(time[0], time[1], time[2])
                today = datetime.date(now.year, now.month, now.day)
                next_page = next_page and (today == time)
                
            yield Request(news['url'], callback=self.parse_news, meta={'news': news, 'rule': rule})

        if next_page:
            next_pages = response.meta.get('next_pages', set([response.url]))
            for next_url in response.xpath(rule['next_page_xpath']).extract():

                next_url = urljoin(response.url, next_url)
                if next_url not in next_pages:
                    next_pages.add(next_url)
                    yield Request(next_url, callback=self.parse, meta={'next_pages': next_pages, 'industry': industry, 'rule': rule})

    def parse_news(self, response):
        rule = response.meta['rule']

        news = response.meta['news']

        body = response.xpath(
            rule['body_xpath']).extract_first()

        if body:
            soup = BeautifulSoup(body)
            [t.decompose() for t in soup.find_all('script')]
            [t.decompose() for t in soup.find_all('style')]
            text = soup.get_text(strip=True)
            news['text'] = text
        publish_time = response.xpath(
            rule['publish_time_xpath']).extract_first()
        if publish_time:
            news['publish_time'] = publish_time.strip()

        news['body'] = response.body.decode(
            get_encoding(response.body), 'ignore')

        return Article(news)
