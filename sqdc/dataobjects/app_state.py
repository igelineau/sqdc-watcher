from sqlalchemy import Column, DateTime, Integer

from sqdc.dataobjects.base import Base


class AppState(Base):
    __tablename__ = 'app_state'

    id = Column('id', Integer, autoincrement=True, primary_key=True)
    last_scan_timestamp = Column(DateTime)
