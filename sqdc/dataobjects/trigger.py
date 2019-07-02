from sqlalchemy import Column, String

from sqdc.dataobjects.base import Base


class Trigger(Base):
    __tablename__ = 'triggers'

    username = Column(String, primary_key=True)
    keyword = Column(String, primary_key=True)