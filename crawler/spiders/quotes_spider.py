
from urllib.parse import urlparse
from w3lib.http import headers_dict_to_raw, headers_raw_to_dict


import scrapy

from scrapy.linkextractors import LinkExtractor
from scrapy.extensions.httpcache import FilesystemCacheStorage

from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import LargeBinary
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

Base = declarative_base()
engine = create_engine("mysql+pymysql://scrapy:12345@localhost/crawl?charset=utf8mb4")

class CrawlResult(Base):
    __tablename__ = 'crawl_result'

    id = Column(Integer, primary_key=True)
    domain = Column(String)
    url = Column(String)
    http_code = Column(Integer)
    headers = Column(String)
    content_type = Column(String)
    content_encoding = Column(String)
    size = Column(Integer)
    content = Column(LargeBinary)

    def __repr__(self):
        return url

class MySqlCacheStorage(FilesystemCacheStorage):
    def __init__(self, *args, **kwargs):
        super(MySqlCacheStorage, self).__init__(*args, **kwargs)
        self.Session = sessionmaker(bind=engine)

    def store_response(self, spider, request, response):
        domain = urlparse(request.url).netloc
        r = CrawlResult(domain=domain, url=response.url, http_code=response.status, size=len(response.body))
        content_type = response.headers.getlist('Content-Type')
        if content_type:
            r.content_type = ','.join([str(x, encoding='utf-8') for x in content_type])
        else:
            r.content_type = ''
        content_encoding = response.headers.getlist('Content-Encoding')
        if content_encoding:
            r.content_encoding = ','.join([str(x, encoding='utf-8') for x in content_encoding])
        else:
            r.content_encoding = ''
        headers = str(headers_dict_to_raw(response.headers), encoding='utf8')
        r.headers = headers
        r.content = response.body
        session = self.Session()
        session.add(r)
        session.commit()

    def retrieve_response(self, spider, request):
        session = self.Session()
        crawl_result = session.query(CrawlResult).where(CrawlResult.url == request.url).first()

        if not crawl_result:
            return
        url = crawl_result.url
        status = crawl_result.http_code
        spider.log(crawl_result.headers)
        headers = Headers(headers_raw_to_dict(crawl_result.headers.encode('utf8')))
        respcls = responsetypes.from_args(headers=headers, url=url, body=crawl_result.content)
        response = respcls(url=url, headers=headers, status=status, body=crawl_result.content)
        return response

class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def __init__(self):
        self.link_extractor = LinkExtractor(allow_domains='www.bbc.com')

    def start_requests(self):
        urls = [
                'http://www.bbc.com/'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'playwright': True})

    def parse(self, response):
        self.log(f"{response}")
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse)
