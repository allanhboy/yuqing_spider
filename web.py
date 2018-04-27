# -*- coding: utf-8 -*-
from scrapy.crawler import CrawlerRunner
from twisted.internet import defer, reactor
from twisted.web import resource, server

from utils import find_settings
from twisted.internet.task import deferLater
from send_template import send_template
import datetime


@defer.inlineCallbacks
def crawl(keywords):
    settings = find_settings()
    runner = CrawlerRunner(settings)
    yield runner.crawl('baidunews', keywords=keywords)
    send_template(settings)


class SimpleWeb(resource.Resource):
    def __init__(self, scheduler):
        self.scheduler = scheduler

        super(SimpleWeb, self).__init__()

    isLeaf = True

    def render_GET(self, request):
        keywords = request.args.get(b'keywords')
        if keywords:
            keywords = [k.decode('utf-8') for k in keywords][0]
            self.scheduler.add_job(crawl, 'date', args=[keywords], run_date=datetime.datetime.now() +
                                   datetime.timedelta(seconds=10))
            # crawl(keywords)
        return 'ok'.encode('utf-8')
