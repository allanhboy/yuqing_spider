# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
from yuqing_spider.spiders import Stock
from yuqing_spider.spiders import Article

import pymysql
import datetime


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
                print('出问题了', e)
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
                    sql = """INSERT IGNORE INTO `article`(`title`, `thumb_img`, `url`, `description`, `publish_time`, `text`, `create_time`, `source_site`, `body`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """
                    number = cursor.execute(sql, (item['title'], item['thumb_img'], item['url'], item['description'], item['publish_time'],
                                                  item['text'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item['source_site'], item['body'],))
                    if number:
                        cursor.execute('SELECT last_insert_id()')
                        article_id, = cursor.fetchone()
         
                        sql1 = "SELECT `id`FROM `company` WHERE `stock_id`=%s"
                        sql2 = "INSERT INTO `company_article`(`company_id`, `article_id`) VALUES (%s,%s)"
                        sql3 = "INSERT INTO `employee_article`(`employee_id`, `article_id`, `is_read`, `is_invalid`) VALUES (%s,%s,%s,%s)"
                        sql4 = "SELECT `employee_id` FROM `follow_company` WHERE `company_id`=%s AND `is_follow`=1"
                        sql5 ="SELECT `id`FROM `company` WHERE `short_name`=%s"
                        for sn in item['tags']:
                            if 'id' in sn:
                                number = cursor.execute(sql1, (sn['id']))
                            else:
                                number = cursor.execute(sql5, (sn['name']))
                            
                            if number:
                                company_id, = cursor.fetchone()
                                cursor.execute(sql2, (company_id, article_id))
                                number = cursor.execute(sql4, (company_id))
                                if number:
                                    row3 = cursor.fetchall()
                                    for employee_id, in row3:
                                        cursor.execute(sql3, (employee_id, article_id, False, False))
                            else:
                                print(sn)
                        

                self.client.commit()
            except Exception as e:
                print('出问题了', e)
            finally:
                return item
        else:
            return item
