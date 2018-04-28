# -*- coding: utf-8 -*-
import datetime
import json
import re
from urllib.parse import urljoin

import pymysql
import pytz
import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy_redis.spiders import RedisSpider
from scrapy_redis.utils import bytes_to_str

from yuqing_spider.spiders import Article
from yuqing_spider.unit import get_encoding


class IndustryNewsSpider(RedisSpider):
    name = "industrynews"
    first_time = False
    pattern = re.compile(
        r'((\d{2,4}-)?)\d{1,2}-\d{1,2}( \d{1,2}:\d{1,2}(:\d{1,2})?)?')

    def make_request_from_data(self, data):
        data = bytes_to_str(data, self.redis_encoding)
        data = json.loads(data)

        url = data.get('url', None)
        if url and not url.strip():
            raise ValueError('url is required')

        industry = {'id': data.get('industry_id'),
                    'industry_name': data.get('industry_name')}
        data.pop('url')
        data.pop('industry_id')
        data.pop('industry_name')

        return Request(url, dont_filter=True, meta={'industry': industry, 'rule': data})

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
