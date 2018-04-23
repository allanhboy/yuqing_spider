# -*- coding: utf-8 -*-
import re
from urllib.parse import urljoin

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from yuqing_spider.spiders import Article
from yuqing_spider.unit import get_encoding


class IndustryNewsSpider(scrapy.Spider):
    name = "industrynews"
    start_urls = []

    def __init__(self, *args, **kwargs):
        self.industry = {'id': 1, 'industry_name': '正极材料'}
        self.rule = {
            'site_name': '高工锂电',
            'url': 'http://news.gg-lb.com/news_more2-65b095fb--6b63678167506599-1.html',
            'list_xpath': '//div[@class="newslistbox"]/div[@class="lst"]',
            'list_thumb_img_xpath': 'a/img/@src',
            'list_title_xpath': 'a[@class="h3"]/text()',
            'list_url_xpath': 'a[@class="h3"]/@href',
            'list_description_xpath': 'p[@class="short"]/text()',
            'list_publish_time_xpath': 'p/span[@class="time"]/text()',
            'body_xpath': '//div[@id="ArticleCnt"]/div[@id="ArticleCnt_main"]',
            'publish_time_xpath': '//div[@class="new-suroce"]/span[@class="m"]/text()',
            'next_page_xpath': '//div[@class="pagelist"]/a/@href'
        }
        self.pattern = re.compile(
            r'(\d{2,4}-)?\d{1,2}-\d{1,2}( \d{1,2}:\d{1,2}(:\d{1,2})?)?')
        self.start_urls.append(self.rule['url'])

        super(IndustryNewsSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        for item in response.xpath(self.rule['list_xpath']):
            thumb_img = item.xpath(
                self.rule['list_thumb_img_xpath']).extract_first()
            title = item.xpath(self.rule['list_title_xpath']).extract_first()
            url = item.xpath(self.rule['list_url_xpath']).extract_first()
            description = item.xpath(
                self.rule['list_description_xpath']).extract_first()
            publish_time = ''.join(item.xpath(
                self.rule['list_publish_time_xpath']).extract())

            m = self.pattern.search(publish_time)
            publish_time = m.group() if m else None

            news = {
                'thumb_img': urljoin(response.url, thumb_img),
                'title': title,
                'url': urljoin(response.url, url),
                'description': description,
                'publish_time': publish_time,
                'industries': [self.industry],
                'source_site': self.rule['site_name']
            }
            yield Request(news['url'], callback=self.parse_news, meta={'news': news})

        next_pages = response.meta.get('next_pages', set([response.url]))
        for next_url in response.xpath(self.rule['next_page_xpath']).extract():

            next_url = urljoin(response.url, next_url)
            if next_url not in next_pages:
                next_pages.add(next_url)
                yield Request(next_url, callback=self.parse, meta={'next_pages': next_pages})

    def parse_news(self, response):
        news = response.meta['news']

        body = response.xpath(
            self.rule['body_xpath']).extract_first()

        if body:
            soup = BeautifulSoup(body)
            [t.decompose() for t in soup.find_all('script')]
            [t.decompose() for t in soup.find_all('style')]
            text = soup.get_text(strip=True)
            news['text'] = text
        publish_time = response.xpath(
            self.rule['publish_time_xpath']).extract_first()
        if publish_time:
            news['publish_time'] = publish_time.strip()

        news['body'] = response.body.decode(
            get_encoding(response.body), 'ignore')

        return (Article(news))
