# -*- coding: utf-8 -*-

import datetime

import pymysql
from scrapy.exceptions import DropItem

from yuqing_spider.db import MysqlDb
from yuqing_spider.spiders import Article, Stock

import logging
logger = logging.getLogger(__name__)

class DuplicatesStockPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if isinstance(item, Stock):
            if item['id'] in self.ids_seen:
                raise DropItem("Duplicate Stock found: %s" % item)
            else:
                self.ids_seen.add(item['id'])
                return item
        else:
            return item


class MysqlStockPipeline(object):
    def __init__(self, mysql_host, mysql_port, mysql_user, mysql_passwd, mysql_db, mysql_charset):
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_user = mysql_user
        self.mysql_passwd = mysql_passwd
        self.mysql_db = mysql_db
        self.mysql_charset = mysql_charset

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_host=crawler.settings.get('STOCK_MYSQL_HOST'),
            mysql_port=crawler.settings.get('STOCK_MYSQL_PORT', 3306),
            mysql_user=crawler.settings.get('STOCK_MYSQL_USER', 'root'),
            mysql_passwd=crawler.settings.get('STOCK_MYSQL_PASSWD'),
            mysql_db=crawler.settings.get('STOCK_MYSQL_DB'),
            mysql_charset=crawler.settings.get('STOCK_MYSQL_CHARSET', 'utf8')
        )

    def open_spider(self, spider):
        self.client = pymysql.connect(host=self.mysql_host, port=self.mysql_port, user=self.mysql_user,
                                      passwd=self.mysql_passwd, db=self.mysql_db, charset=self.mysql_charset)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, Stock):
            try:
                with self.client.cursor() as cursor:
                    sql = "INSERT IGNORE INTO `company`(`company_name`, `short_name`, `is_chinaipo`, `url`, `stock_id`, `category1`, `category2`) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(
                        sql, (item['company_name'], item['short_name'], True, item['url'], item['id'], item['category1'], item['category2']))
                self.client.commit()
            except Exception as e:
                logger.error(e)
            finally:
                return item
        else:
            return item


class DuplicatesArticlePipeline(object):
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item, spider):
        if isinstance(item, Article):
            if item['url'] in self.urls_seen:
                raise DropItem("Duplicate Article found: %s" % item)
            else:
                self.urls_seen.add(item['url'])
                return item
        else:
            return item


class MysqlArticlePipeline(object):
    def __init__(self, mysql_host, mysql_port, mysql_user, mysql_passwd, mysql_db, mysql_charset):
        self.mysql_host = mysql_host
        self.mysql_port = mysql_port
        self.mysql_user = mysql_user
        self.mysql_passwd = mysql_passwd
        self.mysql_db = mysql_db
        self.mysql_charset = mysql_charset

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_host=crawler.settings.get('ARTICLE_MYSQL_HOST'),
            mysql_port=crawler.settings.get('ARTICLE_MYSQL_PORT', 3306),
            mysql_user=crawler.settings.get('ARTICLE_MYSQL_USER', 'root'),
            mysql_passwd=crawler.settings.get('ARTICLE_MYSQL_PASSWD'),
            mysql_db=crawler.settings.get('ARTICLE_MYSQL_DB'),
            mysql_charset=crawler.settings.get('ARTICLE_MYSQL_CHARSET', 'utf8')
        )

    def open_spider(self, spider):
        self.client = pymysql.connect(host=self.mysql_host, port=self.mysql_port, user=self.mysql_user,
                                      passwd=self.mysql_passwd, db=self.mysql_db, charset=self.mysql_charset)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, Article):
            try:
                with self.client.cursor() as cursor:
                    db = MysqlDb(cursor)

                    number, article_id = db.InsertArticle(item)
                    if number and article_id:
                        if "companies" in item:
                            for company in item['companies']:
                                if "stock_id" in company:
                                    number, company_id = db.FetchCompanyIdByStockId(company['stock_id'])
                                elif "short_name" in company:
                                    number, company_id = db.FetchCompanyIdByShortName(company['short_name'])
                                
                                if company_id:
                                    db.InsertCompanyArticle(company_id, article_id)
                                    employee_ids = db.FetchFollowCompanyEmployeeId(company_id)
                                    for employee_id in employee_ids:
                                        db.InsertEmployeeArticle(employee_id, article_id)


                        if "industries" in item:
                            for industry in item['industries']:
                                db.InsertIndustryArticle(industry['id'], article_id)
                                employee_ids = db.FetchFollowIndustryEmployeeId(industry['id'])
                                for employee_id in employee_ids:
                                    db.InsertEmployeeArticle(employee_id, article_id)

                self.client.commit()
            except Exception as e:
                logger.error(e)
            finally:
                return item
        else:
            return item
