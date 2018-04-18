# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request

from scrapy_redis.spiders import RedisCrawlSpider

import time
import datetime
import json
import re

from bs4 import BeautifulSoup

from yuqing_spider.spiders import Article

class ChinaipoNewsSpider(scrapy.Spider):
    name = "chinaiponews"
    allowed_domains = ["chinaipo.com"]
    start_urls = [
        "http://m.chinaipo.com/index.php?app=3g&mod=Index&act=catList&type=1&cid=100000&p=1"
    ]
    first_time = True

    def parse(self, response):
        page = response.meta.get('page', 1)
        
        next_page = True
        for item in response.xpath('//ul[@class="htnews-ul"]/li'):
            news = {}
            news['thumb_img'] = item.xpath('div/a/img/@src').extract_first()   
            news['url'] = item.xpath('div/a/@href').extract_first()
            news['title'] = item.xpath('div/h3/a/text()').extract_first()
            yield Request(news['url'], callback=self.parse_news, meta={'news': news})

            if not self.first_time:
                time = ''.join([t.strip() for t in item.xpath('p/span/text()').extract_first().split('·') if t.strip()])
                time = '{0}-{1}'.format(str(datetime.datetime.now().year),time)
                time = [int(t) for t in time.split('-')]
                time = datetime.date(time[0], time[1], time[2])
                today = datetime.date.today()
                next_page = next_page and (today == time)
            
            
        if next_page:
            page += 1
            return Request('http://m.chinaipo.com/index.php?app=3g&mod=Index&act=catList&type=1&cid=100000&p={0}'.format(page), callback=self.parse, meta={'page': page})

    def parse_news(self, response):
        news = response.meta['news']

        soup = BeautifulSoup(response.xpath('//div[@class="artical-summary"]').extract_first())
        soup.span.decompose()
        news['description'] = soup.get_text(strip=True)

        content_eml = response.xpath('//div[@class="airtical-content"]').extract_first().replace('\n','').replace('\r','').replace('\t','').strip()
        soup = BeautifulSoup(content_eml)
        news['publish_time'] = [x.strip() for x in soup.div.contents[0].contents[1].string.split('·') if x.strip()][0]
        # news['publish_time'] = time.mktime(time.strptime(news['publish_time'], '%Y-%m-%d'))
        text = ""
        news['tags'] = []
        for child in soup.div.contents[1:]:
            t = child.string
            if t == None:
                tc = [x for x in child.contents if x]
                is_deleted = False
                if len(tc):
                    if tc[0].name == "strong":
                        if tc[1].string.strip():
                            is_deleted = True

                    if not is_deleted:
                        [news['tags'].append({'name': x.string,'id': re.search(r'\d+', x['href']).group()}) for x in tc if x.name=='a' and x.string !='新三板' and x.string]
                        t = ''.join([x.strip() for x in child.stripped_strings if x])
            else:
                t = t.strip()
                
            if t:
                if text:
                    text ='{0}\n{1}'.format(text, t) 
                else: text = t
        
        news['text'] = text
        news['source_site'] = '新三板在线'
        news['body'] = response.body_as_unicode()

        return Article(news)