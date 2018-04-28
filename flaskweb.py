# -*- coding: utf-8 -*-

import json

from flask import Flask, request
from scrapy_redis import connection

from utils import find_settings

app = Flask(__name__)


@app.route('/baidunews')
def hello_world():
    keywords = request.args.get('keywords', None)
    response = {'code': 0, 'message': "ok"}
    if keywords and keywords.strip():
        settings = find_settings()
        server = connection.from_settings(settings)
        request_json = json.dumps(
            {'url': 'https://news.baidu.com/news?tn=bdapinewsearch&word={0}&pn=0&rn=50&ct=0'.format(keywords), 'keywords': keywords}, ensure_ascii=False)
        server.lpush('baidunews:start_urls', request_json)
    else:
        response = {'code': 10001, 'message': "keywords为空"}

    return json.dumps(response, ensure_ascii=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
