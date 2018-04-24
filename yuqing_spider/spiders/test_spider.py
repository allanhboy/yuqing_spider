import scrapy
class BaiduNewsSpider(scrapy.Spider):
     name = "testspider"
     start_urls = [
         'http://www.baidu.com'
     ]

     def parse(self, response):
         print(response.url)
         return {'url': response.url}