# -*- coding: utf-8 -*-
from scrapy.crawler import CrawlerRunner
from twisted.internet import defer
from twisted.web import resource

from utils import find_settings


@defer.inlineCallbacks
def crawl(keywords):
    settings = find_settings()
    runner = CrawlerRunner(settings)
    yield runner.crawl('baidunews', keywords=keywords)


class SimpleWeb(resource.Resource):
    def __init__(self, scheduler):
        self.scheduler = scheduler

        super(SimpleWeb, self).__init__()

    isLeaf = True

    def render_GET(self, request):
        keywords = request.args[b'keywords'][0].decode('utf-8')
        self.scheduler.add_job(crawl, 'date', args=[keywords])

        request.setHeader("Content-Type", "text/html; charset=utf-8")
        return ''.encode('utf-8')

