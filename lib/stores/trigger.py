from sqlalchemy import Column, String

from lib.stores.base import Base


class Trigger(Base):
    __tablename__ = 'triggers'

    username = Column(String, primary_key=True)
    keyword = Column(String, primary_key=True)