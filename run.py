# -*- coding: utf-8 -*-

import argparse
from importlib import import_module

import pytz
from apscheduler.schedulers.twisted import TwistedScheduler
from apscheduler.triggers.cron import CronTrigger
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.conf import closest_scrapy_cfg
from twisted.internet import defer, reactor
from scrapy.utils.log import configure_logging

from six.moves.configparser import (NoOptionError, NoSectionError,
                                    SafeConfigParser)


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
    crawler_settings.setmodule(module, priority='project')
    return crawler_settings


# @defer.inlineCallbacks
# def crawl(spider_name):
#     print('============crawl===========', spider_name)
#     yield process.crawl(spider_name)


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


def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


# if __name__ == '__main__':

arguments = parse_arguments()
settings = find_settings()
configure_logging(settings=settings)
runner = CrawlerRunner(settings)

@defer.inlineCallbacks
def crawl(spider_name):
    yield print('======================', spider_name)
    yield runner.crawl(spider_name)

sched = TwistedScheduler()

if arguments.enable_date:
    sched.add_job(crawl, 'date', args=[arguments.name])
else:
    tz = pytz.timezone('Asia/Shanghai')
    sched.add_job(crawl, CronTrigger.from_crontab(
        arguments.cron, timezone=tz), args=[arguments.name])
# sched.add_job(crawl, 'date', args=[arguments.name])
sched.daemonic = False
sched.start()

reactor.run()
