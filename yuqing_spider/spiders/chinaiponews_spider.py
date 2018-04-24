# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request

from scrapy_redis.spiders import RedisCrawlSpider

# import time
import datetime
import json
import re


from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from yuqing_spider.spiders import Article
import pytz
import logging
logger = logging.getLogger(__name__)

# handler = logging.FileHandler("log.txt", encoding='utf-8')
# handler.setLevel(logging.ERROR)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# console.setFormatter(formatter)
# logger.addHandler(console)

class ChinaipoNewsSpider(scrapy.Spider):
    name = "chinaiponews"
    allowed_domains = ["chinaipo.com"]
    start_urls = [
        "http://m.chinaipo.com/index.php?app=3g&mod=Index&act=catList&type=1&cid=100000&p=1"
    ]
    first_time = False

    def parse(self, response):
        print('我来也.....')
        tz = pytz.timezone('Asia/Shanghai')
        page = response.meta.get('page', 1)
        
        next_page = True
        for item in response.xpath('//ul[@class="htnews-ul"]/li'):
            news = {}
            news['thumb_img'] = item.xpath('div/a/img/@data-original').extract_first()   
            news['url'] = item.xpath('div/a/@href').extract_first()
            news['title'] = item.xpath('div/h3/a/text()').extract_first()
            yield Request(news['url'], callback=self.parse_news, meta={'news': news})

            if not self.first_time:
                time = ''.join([t.strip() for t in item.xpath('p/span/text()').extract_first().split('·') if t.strip()])
                now = datetime.datetime.now(tz)
                time = '{0}-{1}'.format(str(now.year),time)
                time = [int(t) for t in time.split('-')]
                time = datetime.date(time[0], time[1], time[2])
                today = datetime.date(now.year, now.month, now.day)
                next_page = next_page and (today == time)
            
            
        if next_page:
            page += 1
            yield Request('http://m.chinaipo.com/index.php?app=3g&mod=Index&act=catList&type=1&cid=100000&p={0}'.format(page), callback=self.parse, meta={'page': page})

    def parse_news(self, response):
        news = response.meta['news']
        body = response.xpath('//div[@class="artical-summary"]').extract_first()
        if body:
            soup = BeautifulSoup(body)
            soup.span.decompose()
            news['description'] = soup.get_text(strip=True)

            content_eml = response.xpath('//div[@class="airtical-content"]').extract_first().replace('\n','').replace('\r','').replace('\t','').strip()
            soup = BeautifulSoup(content_eml)
            news['publish_time'] = [x.strip() for x in soup.div.contents[0].contents[1].string.split('·') if x.strip()][0]
            # news['publish_time'] = time.mktime(time.strptime(news['publish_time'], '%Y-%m-%d'))
            text = ""
            news['companies'] = []
            for child in soup.div.contents[1:]:
                t = child.string
                if t == None:
                    tc = [x for x in child.contents if x]
                    is_deleted = False
                    i = 0
                    last_tag_name = None
                    for ch in tc:
                        if isinstance(ch, NavigableString):
                            v = ch.string.strip()
                            if len(v):
                                if i == 1:
                                    if last_tag_name == "strong":
                                        is_deleted = True
                                        break
                                else:
                                    if v.find('本文为新三板在线原创稿件，转载需注明出处和作者，否则视为侵权') != -1:
                                        is_deleted = True
                                        break
                                    
                                i += 1
                                last_tag_name = None
                        elif isinstance(ch, Tag):
                            if i == 1:
                                if last_tag_name == "strong":
                                    is_deleted = True
                                    break
                            elif i==0:
                                if ch.name =="span":
                                    if ch.string.find('本文为新三板在线原创稿件，转载需注明出处和作者，否则视为侵权') != -1:
                                        is_deleted = True
                                        break
                            
                            last_tag_name = ch.name
                            i += 1
                        else:
                            last_tag_name = None
             

                    if not is_deleted:
                        [news['companies'].append({'short_name': x.string,'stock_id': re.search(r'\d+', x['href']).group()}) for x in tc if x.name=='a' and x.string and x.string.find('新三板')==-1 and re.search(r'\d+', x['href'])]
                        t = ''.join([x.strip() for x in child.stripped_strings if x])
                else:
                    if t.find('本文为新三板在线原创稿件，转载需注明出处和作者，否则视为侵权') == -1:
                        t = t.strip()
                    else:
                        t = None
                    
                if t:
                    if text:
                        text ='{0}\n{1}'.format(text, t) 
                    else: text = t
            
            news['text'] = text
            news['source_site'] = '新三板在线'
            news['body'] = response.body_as_unicode()
           
            return Article(news)