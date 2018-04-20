# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import scrapy


class Stock(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    company_name = scrapy.Field()
    short_name = scrapy.Field()
    category1 = scrapy.Field()
    category2 = scrapy.Field()


class Article(scrapy.Item):
    id = scrapy.Field()
    thumb_img = scrapy.Field()
    url= scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    publish_time = scrapy.Field()
    text = scrapy.Field()
    source_site = scrapy.Field()
    body = scrapy.Field()
    companies = scrapy.Field()
    industries = scrapy.Field()
    # 
    # url= scrapy.Field()
    # url= scrapy.Field()
