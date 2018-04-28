# -*- coding: utf-8 -*-
import json
import os

import pymysql
from celery import Celery
from celery.schedules import crontab
from scrapy_redis.connection import get_redis_from_settings

from utils import find_settings

env_dict = os.environ
broker = env_dict.get('BROKER', 'redis://localhost:6379/3')
app = Celery('tasks', broker=broker)

app.conf.beat_schedule = {
    'crawl_chinaiponews': {
        'task': 'tasks.crawl_chinaiponews',
        'schedule': crontab(hour='0-12', minute=0),
        'args': (),
    },
    'crawl_industry': {
        'task': 'tasks.crawl_industry',
        'schedule': crontab(hour='*/4,0-12', minute=20),
        'args': (),
    },
    'crawl_nonchinaiponews': {
        'task': 'tasks.crawl_nonchinaiponews',
        'schedule': crontab(hour='8,11,17', minute=40),
        'args': (),
    },
}

@app.task
def crawl_industry():
    settings = find_settings()

    sql = """
        SELECT a.`id`  as `industry_id`, a.`industry_name` , b.`site_name`,b.`url`, list_xpath,list_thumb_img_xpath,list_title_xpath,list_url_xpath,list_description_xpath,list_publish_time_xpath,body_xpath,publish_time_xpath,next_page_xpath FROM `industry`  a
        JOIN `industry_spider_rule` b ON a.`id`=b.`industry_id`
        JOIN `spider_rule` c ON c.`id`=b.`spider_rule_id` AND c.`enable`=1
         """
    mysql_host = settings.get('STOCK_MYSQL_HOST')
    mysql_port = settings.get('STOCK_MYSQL_PORT', 3306)
    mysql_user = settings.get('STOCK_MYSQL_USER', 'root')
    mysql_passwd = settings.get('STOCK_MYSQL_PASSWD')
    mysql_db = settings.get('STOCK_MYSQL_DB')
    mysql_charset = settings.get('STOCK_MYSQL_CHARSET', 'utf8')

    client = pymysql.connect(host=mysql_host, port=mysql_port, user=mysql_user,
                             passwd=mysql_passwd, db=mysql_db, charset=mysql_charset)
    with client.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
        server = get_redis_from_settings(settings)
        for industry_id, industry_name, site_name, url, list_xpath, list_thumb_img_xpath, list_title_xpath, list_url_xpath, list_description_xpath, list_publish_time_xpath, body_xpath, publish_time_xpath, next_page_xpath in rows:
            request_json = {
                'industry_name': industry_name,
                'industry_id': industry_id,
                'site_name': site_name,
                'url': url,
                'list_xpath': list_xpath,
                'list_thumb_img_xpath': list_thumb_img_xpath,
                'list_title_xpath': list_title_xpath,
                'list_url_xpath': list_url_xpath,
                'list_description_xpath': list_description_xpath,
                'list_publish_time_xpath': list_publish_time_xpath,
                'body_xpath': body_xpath,
                'publish_time_xpath': publish_time_xpath,
                'next_page_xpath': next_page_xpath
            }
            server.lpush('industrynews:start_urls', json.dumps(
                request_json, ensure_ascii=False))

        client.close()


@app.task
def crawl_chinaiponews():
    settings = find_settings()
    server = get_redis_from_settings(settings)
    server.lpush('chinaiponews:start_urls',
                 'http://m.chinaipo.com/index.php?app=3g&mod=Index&act=catList&type=1&cid=100000&p=1')


@app.task
def crawl_nonchinaiponews():
    settings = find_settings()

    sql = "SELECT `short_name` FROM `company` WHERE `is_chinaipo`=0"

    mysql_host = settings.get('STOCK_MYSQL_HOST')
    mysql_port = settings.get('STOCK_MYSQL_PORT', 3306)
    mysql_user = settings.get('STOCK_MYSQL_USER', 'root')
    mysql_passwd = settings.get('STOCK_MYSQL_PASSWD')
    mysql_db = settings.get('STOCK_MYSQL_DB')
    mysql_charset = settings.get('STOCK_MYSQL_CHARSET', 'utf8')

    client = pymysql.connect(host=mysql_host, port=mysql_port, user=mysql_user,
                             passwd=mysql_passwd, db=mysql_db, charset=mysql_charset)
    with client.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
        server = get_redis_from_settings(settings)
        for short_name, in rows:
            request_json = {'url': 'https://news.baidu.com/news?tn=bdapinewsearch&word={0}&pn=0&rn=50&ct=0'.format(
                short_name), 'keywords': short_name}
            server.lpush('baidunews:start_urls', json.dumps(
                request_json, ensure_ascii=False))


# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(
#         crontab(hour='*/4,8-20', minute=20), crawl_industry.s())

#     sender.add_periodic_task(
#         crontab(hour='8-20', minute=0), crawl_chinaiponews.s())

#     sender.add_periodic_task(
#         crontab(hour='8,11,17', minute=40), crawl_nonchinaiponews.s())


if __name__ == '__main__':
    app.start()
