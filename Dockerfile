FROM python:3.6

RUN mkdir -p /app
WORKDIR /app

ADD . /app

RUN pip3 install -r requirements.txt
RUN echo "Asia/Shanghai" > /etc/timezone && \
dpkg-reconfigure -f noninteractive tzdata
RUN python __init__.py

EXPOSE 5000

ENTRYPOINT ["scrapy", "crawl"]
CMD ["chinaiponews"]