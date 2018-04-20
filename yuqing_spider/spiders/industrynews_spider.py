# -*- coding: utf-8 -*-
from urllib.parse import urljoin

import scrapy
from bs4 import BeautifulSoup
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from yuqing_spider.unit import get_encoding
from yuqing_spider.spiders import Article


class IndustryNewsSpider(scrapy.Spider):
    name = "industrynews"
    start_urls = [
        "http://news.gg-lb.com/news_more2-65b095fb--6b63678167506599-1.html"
    ]

    def __init__(self, *args, **kwargs):
        self.industry = {'id': 1, 'industry_name': '正极材料'}
        self.source_site = "高工锂电"

        super(IndustryNewsSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        for item in response.xpath('//div[@class="newslistbox"]/div[@class="lst"]'):
            thumb_img = item.xpath('a/img/@src').extract_first()
            title = item.xpath('a[@class="h3"]/text()').extract_first()
            url = item.xpath('a[@class="h3"]/@href').extract_first()
            description = item.xpath(
                'p[@class="short"]/text()').extract_first()
            publish_time = item.xpath('p/span/a/text()').extract_first()
            news = {
                'thumb_img': urljoin(response.url, thumb_img),
                'title': title,
                'url': urljoin(response.url, url),
                'description': description,
                'publish_time': publish_time,
                'industries': [self.industry],
                'source_site': self.source_site
            }
            yield Request(news['url'], callback=self.parse_news, meta={'news': news})

    def parse_news(self, response):
        news = response.meta['news']

        body = response.xpath(
            '//div[@id="ArticleCnt"]/div[@id="ArticleCnt_main"]').extract_first()

        if body:
            soup = BeautifulSoup(body)
            # style
            [t.decompose() for t in soup.find_all('script')]
            [t.decompose() for t in soup.find_all('style')]
            text = soup.get_text(strip=True)
            news['text'] = text
        publish_time = response.xpath(
            '//div[@class="new-suroce"]/span[@class="m"]/text()').extract_first()
        if publish_time:
            news['publish_time'] = publish_time.strip()

        news['body'] = response.body.decode(get_encoding(response.body), 'ignore')
        
        return (Article(news))
