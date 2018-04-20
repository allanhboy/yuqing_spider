# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import requests
import logging

logger = logging.getLogger(__name__)

class YuqingSpiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class YuqingSpiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)





class ProxyIpMiddleware(object):
    def __init__(self, ip=''):
        self.ip = ip

    def process_request(self, request, spider):
        for index in range(5): 
            r = requests.get('http://proxy-pool.c2fd1643d9abe4d9fb2887ea58a7a3202.cn-hangzhou.alicontainer.com/get/')
            if r.ok:
                ip = r.text
                proxy_ip = "http://{proxy}".format(proxy=ip)
                proxies = {"http": proxy_ip}
                try:
                    r = requests.get( 'http://httpbin.org/ip', proxies=proxies, timeout=20, verify=False)
                    if r.ok:
                        logger.debug('Current Proxy Ip: %s ok, %s' % (ip, r.text))
                        request.meta["proxy"] = proxy_ip
                        break
                    else:
                        logger.warning('Current Proxy Ip: %s fill' % ip)
                except Exception:
                    logger.error('Current Proxy Ip: %s fill' % ip)
                    requests.get('http://proxy-pool.c2fd1643d9abe4d9fb2887ea58a7a3202.cn-hangzhou.alicontainer.com/delete/?proxy={0}'.format(ip))
                    
            
        # ip = r.data.decode('utf-8').strip()
        # if ip:
        #     http.request('GET', 'http://httpbin.org/ip', proxies=proxies)
        #     logger.debug('Current Proxy Ip: %s' % ip)
        #     request.meta["proxy"] = "http://"+ip
        # r.close()
    
    def process_exception(self, request, exception, spider):
        pass
        # ip = str(request.meta["proxy"]).replace('http://','')
        # if ip:
        #     http = urllib3.PoolManager()
        #     r = http.request('GET', 'http://proxy-pool.c2fd1643d9abe4d9fb2887ea58a7a3202.cn-hangzhou.alicontainer.com/delete/?proxy={0}'.format(ip))
        #     logger.debug('{0} deleted {1}'.format(ip, r.data.decode('utf-8')))
        #     r.close()
    
    # def process_response(self, request, response, spider):
    #     print('这里这里' )