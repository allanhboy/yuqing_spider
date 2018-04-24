# -*- coding: utf-8 -*-

import argparse
from importlib import import_module

import pytz
from apscheduler.schedulers.twisted import TwistedScheduler
from apscheduler.triggers.cron import CronTrigger
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.utils.conf import closest_scrapy_cfg
from twisted.internet import defer

from six.moves.configparser import (NoOptionError, NoSectionError,
                                    SafeConfigParser)
from yuqing_spider.spiders.chinaiponews_spider import ChinaipoNewsSpider


def find_settings():
    project_config_path = closest_scrapy_cfg()
    if not project_config_path:
        raise RuntimeError('Cannot find scrapy.cfg file')
    project_config = SafeConfigParser()
    project_config.read(project_config_path)
    try:
        project_settings = project_config.get('settings', 'default')
    except (NoSectionError, NoOptionError) as e:
        raise RuntimeError(e.message)

    module = import_module(project_settings)
    crawler_settings = Settings()
    crawler_settings.setmodule(module,priority='project')
    return crawler_settings

@defer.inlineCallbacks
def crawl():
    yield process.crawl(ChinaipoNewsSpider)

def parse_arguments():

    parser = argparse.ArgumentParser(
        description='爬虫入口')
    parser.add_argument('-c', '--cron', dest='cron',
                        default='0 8-20 * * *',
                        help='任务定时机制')
    
    return parser.parse_args()

if __name__ == '__main__':
    arguments = parse_arguments()
    tz = pytz.timezone('Asia/Shanghai')
    sched = TwistedScheduler()
    settings = find_settings()
    process =  CrawlerProcess(settings=settings)
    sched.add_job(crawl, CronTrigger.from_crontab(arguments.cron, timezone=tz))
    
    sched.start()
    process.start(False)
