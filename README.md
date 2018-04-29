# 爬虫

```dos
scrapy crawl chinaipo

redis-cli lpush chinaipo:start_urls http://www.chinaipo.com/listed/?p=1

celery -A tasks worker --loglevel=info -P eventlet --concurrency=1
```