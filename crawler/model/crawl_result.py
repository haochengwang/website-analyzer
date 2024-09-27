from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import LargeBinary

Base = declarative_base()

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
    decompressed_content = Column(String)

    def __repr__(self):
        return url
