from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.types import LargeBinary

Base = declarative_base()

class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    type  = Column(Integer)
    status = Column(Integer)
    #metadata = Column(String)

    def __repr__(self):
        return url
