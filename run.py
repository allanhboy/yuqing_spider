# -*- coding: utf-8 -*-

import argparse

import pytz
from apscheduler.schedulers.twisted import TwistedScheduler
from apscheduler.triggers.cron import CronTrigger
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import defer, endpoints, reactor
from twisted.web import server

from utils import find_settings
from web import SimpleWeb


def parse_arguments():

    parser = argparse.ArgumentParser(
        description='爬虫入口')

    parser.add_argument('-n', '--name', dest='name',
                        default='chinaiponews',
                        help='爬虫名称')
    parser.add_argument('-d', '--enable_date',
                        dest='enable_date', action='store_true', help='是否立即执行')

    parser.add_argument('-c', '--cron', dest='cron',
                        default='0 8,11,17 * * *',
                        help='任务定时机制')

    return parser.parse_args()



# if __name__ == '__main__':
settings = find_settings()
configure_logging(settings=settings)
arguments = parse_arguments()



@defer.inlineCallbacks
def crawl():
    runner = CrawlerRunner(settings)
    yield runner.crawl('industrynews')
    yield runner.crawl('chinaiponews')
    # yield runner.crawl('chinaipo')
    


sched = TwistedScheduler()
sched.daemonic = False
tz = pytz.timezone('Asia/Shanghai')
sched.add_job(crawl, CronTrigger.from_crontab(arguments.cron, timezone=tz))
# sched.add_job(crawl, 'date')

site = server.Site(SimpleWeb(sched))
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
endpoint.listen(site)

sched.start()
reactor.run()
