# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request

from scrapy_redis.spiders import RedisCrawlSpider

from yuqing_spider.spiders import Stock

import re


class ChinaipoSpider(scrapy.Spider):
    name = "chinaipo"
    allowed_domains = ["chinaipo.com"]

    fields = {
        '机构名称': 'company_name',
        '机构简称': 'short_name',
        '机构类型(大类)': 'category1',
        '机构类型(小类)': 'category2',
    }
    start_urls = [
        "http://www.chinaipo.com/listed/?p=1"
    ]

    def parse(self, response):
        totalpage = response.meta.get('totalpage', -1)
        page = response.meta.get('page', 1)
        for tr in response.xpath('//div[@class="list_return"]/table/tbody/tr'):
            a = tr.xpath('td[1]/a')
            if a:
                u = a.xpath('@href').extract_first()
                url = '{0}{1}'.format(u, '/profile.html')
                id = a.xpath('text()').extract_first()
                yield Request(url, callback=self.parse_profile, meta={'id': id, 'url': u})

        if totalpage == -1:
            totalpage, = [int(re.search(r'共\d+页', x).group().replace('共', '').replace('页', ''))
                          for x in response.xpath('//div[@class="page"]/text()').extract() if re.search(r'共\d+页', x)]

        if page < totalpage:
            page += 1
            yield Request('http://www.chinaipo.com/listed/?p={0}'.format(page), callback=self.parse, meta={'totalpage': totalpage, 'page': page})

    def parse_profile(self, response):
        id = response.meta['id']
        url = response.meta['url']
        item = {'id': id, 'url': url}
        for tr in response.xpath('//div[@class="pstock"]/div[@class="f10_data"]/table/tr[position()<7]'):
            k = tr.xpath('td[1]/text()').extract_first().strip()
            v = tr.xpath('td[2]/text()').extract_first().strip()
            if k in self.fields:
                item[self.fields[k]] = v

        return Stock(item)
