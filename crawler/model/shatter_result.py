from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.types import LargeBinary

Base = declarative_base()

class ShatterResult(Base):
    __tablename__ = 'shatter_result'

    id = Column(Integer, primary_key=True)
    domain = Column(String)
    xpath = Column(String)
    crawl_id = Column(Integer)
    text = Column(String)

    def __repr__(self):
        return f'{domain}|{crawl_id}|{xpath}'
