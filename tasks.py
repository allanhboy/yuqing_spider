# -*- coding: utf-8 -*-
import os
from datetime import timedelta

from billiard.pool import Pool
from celery import Celery
from scrapy.crawler import CrawlerProcess

from send_template import send_template
from utils import find_settings

env_dict = os.environ
broker = env_dict.get('BROKER', 'redis://localhost:6379/1')
app = Celery('tasks', broker=broker)


@app.task
def crawl_keywords(keywords):
    p = Pool(4)
    p.apply_async(crawl, args=(keywords, ))
    p.close()
    p.join()

# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls say('hello') every 10 seconds.
#     sender.add_periodic_task(10.0, crawl_keywords.s('hello'), name='add every 10')

def crawl(keywords):
    settings = find_settings()
    crawler = CrawlerProcess()
    crawler.crawl('baidunews', keywords=keywords)
    crawler.start()
    crawler.stop()
    send_template(settings)


if __name__ == '__main__':
    app.start()
