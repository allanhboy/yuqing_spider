# -*- coding: utf-8 -*-

from flask import Flask
from flask import request
from tasks import crawl_keywords
app = Flask(__name__)

@app.route('/')
def hello_world():
    keywords = request.args.get('keywords', '')
    print(keywords)
    crawl_keywords.delay(keywords)
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0')