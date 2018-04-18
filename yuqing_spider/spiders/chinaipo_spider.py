# -*- coding: utf-8 -*-
from scrapy.http import Request

from scrapy_redis.spiders import RedisCrawlSpider

from yuqing_spider.spiders import Stock

class ChinaipoSpider(RedisCrawlSpider):
    name = "chinaipo"
    allowed_domains = ["chinaipo.com"]

    fields = {
        '机构名称': 'company_name',
        '机构简称': 'short_name'
    }

    def parse(self, response):
        for tr in response.xpath('//div[@class="list_return"]/table/tbody/tr'):
            a = tr.xpath('td[1]/a')
            if a:
                u = a.xpath('@href').extract_first()
                url = '{0}{1}'.format(u, '/profile.html')
                id =  a.xpath('text()').extract_first()
                yield Request(url, callback=self.parse_profile, meta={'id': id, 'url': u})
        
        for u in response.xpath('//div[@class="page"]/a/@href').extract():
            if u != 'javascript:;':
                yield Request(u, callback=self.parse)

    def parse_profile(self, response):
        id = response.meta['id']
        url = response.meta['url']
        item = {'id': id, 'url': url}
        for tr in response.xpath('//div[@class="pstock"]/div[@class="f10_data"]/table/tr[position()<3]'):
            k = tr.xpath('td[1]/text()').extract_first().strip()
            v = tr.xpath('td[2]/text()').extract_first().strip()
            item[self.fields[k]] = v
        
        return Stock(item)