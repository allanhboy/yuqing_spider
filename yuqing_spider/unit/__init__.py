# -*- coding: utf-8 -*-
import datetime
import logging
import sys

import chardet
import pymysql
import requests

logger = logging.getLogger(__name__)

sys.setrecursionlimit(1000000)


def get_encoding(s):
    '''
    获取文字编码
    '''
    try:
        chardit1 = chardet.detect(s)
        if chardit1['encoding'] == "utf-8" or chardit1['encoding'] == "UTF-8":
            return "UTF-8"
        else:
            return "GBK"
    except:
        return "UTF-8"


def send_template(settings, name=None):
    mysql_host = settings.get('STOCK_MYSQL_HOST')
    mysql_port = settings.get('STOCK_MYSQL_PORT', 3306)
    mysql_user = settings.get('STOCK_MYSQL_USER', 'root')
    mysql_passwd = settings.get('STOCK_MYSQL_PASSWD')
    mysql_db = settings.get('STOCK_MYSQL_DB')
    mysql_charset = settings.get('STOCK_MYSQL_CHARSET', 'utf8')

    try:
        client = pymysql.connect(host=mysql_host, port=mysql_port, user=mysql_user,
                                 passwd=mysql_passwd, db=mysql_db, charset=mysql_charset)
        with client.cursor() as cursor:
            number = cursor.execute("""SELECT c.`openid`, COUNT(*) as `count` FROM `employee_article`  a
    JOIN `employee` b ON a.`employee_id`=b.`id`
    JOIN `wechat` c ON c.`unionid`=b.`unionid`
    where a.`is_send`=0
    GROUP BY c.`openid`
            """)
            if number:
                rows = cursor.fetchall()
                first_value = '您好,您关注的企业(行业)有新的动态'
                if name:
                    first_value = '您好,您关注的{0}有新的动态'.format(name)
                for openid, count in rows:
                    data = {
                        "first": {
                            "value": first_value,
                            "color": "#173177"
                        },
                        "keyword1": {
                            "value": "{0}条新的舆情".format(count),
                            "color": "#173177"
                        },
                        "keyword2": {
                            "value": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "color": "#173177"
                        },
                        "remark": {
                            "value": "点击查看",
                            "color": "#173177"
                        }
                    }

                    def callback():
                        cursor.execute("UPDATE `employee_article` SET `is_send`=%s,`send_time`=%s WHERE `is_send`=%s", (
                            True, datetime.datetime.now(), False))
                        client.commit()
                    template(openid, data, callback)
        client.close()
    except Exception as e:
        logger.error(e)


def template(user_id, data, callback):
    template_id = 'THB0YXpq1xUJz9UICD5QfsgTUujwKMl8tpsq_ZY4FrQ'
    r = requests.post("http://yuqing.wechat.qianjifang.com.cn/template/", json={
        "touser": user_id,
        "template_id": template_id,
        "data": data,
        "miniprogram": {
            "appid": "wx79edc80703771261",
            #"pagepath": "pages/monitor/monitor"
        }
    })
    if r.ok:
        j = r.json()
        logger.debug(j)
        if j['errcode'] == 0:
            callback()
