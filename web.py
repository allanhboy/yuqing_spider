# -*- coding: utf-8 -*-
from scrapy.crawler import CrawlerRunner
from twisted.internet import defer, reactor
from twisted.web import resource, server

from utils import find_settings
from twisted.internet.task import deferLater



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
        keywords = request.args.get(b'keywords')
        if keywords:
            keywords = [k.decode('utf-8') for k in keywords][0]
            crawl(keywords)
        return 'ok'.encode('utf-8')

