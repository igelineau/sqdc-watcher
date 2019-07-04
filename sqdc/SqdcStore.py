import datetime
import logging
import string
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from sqdc.dataobjects.base import Base
from sqdc.dataobjects.product import Product as Product
from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.product_variant import ProductVariant
from sqdc.dataobjects.sessionwrapper import SessionWrapper
from sqdc.dataobjects.trigger import Trigger

log = logging.getLogger(__name__)

# logging.basicConfig()
# logger = logging.getLogger('sqlalchemy.engine')
# logger.setLevel(logging.DEBUG)


class SqdcStore:
    engine: Engine
    session_maker: sessionmaker

    def __init__(self, is_test, root_directory=None):
        self.dir = Path(Path.cwd().joinpath('data') if root_directory is None else root_directory)
        if self.dir.is_file():
            raise FileExistsError('The path must be a directory. a file exists here: {}'.format(self.dir))

        if not self.dir.exists():
            self.dir.mkdir()

        test_suffix = '-test' if is_test else ''
        self.sqlite_db = self.dir.joinpath(f'data{test_suffix}.db')
        self.db_url = 'sqlite:///' + self.sqlite_db.as_posix()

    def open_session(self) -> SessionWrapper:
        return SessionWrapper(self.session_maker())

    def initialize(self):

        print('connecting to database: ' + self.db_url)
        self.engine = create_engine(self.db_url)
        self.session_maker = sessionmaker(bind=self.engine)

        Base.metadata.create_all(self.engine)

    def save_products(self, products: List[Product]):
        with self.open_session() as session:
            # make sure we don't leave any flag set to True (only in-stock products are provided to this method).
            session.query(Product).update(values={'in_stock': False})
            session.query(ProductVariant).update(values={'in_stock': False})

            for p in products:
                session.merge(p)

            session.commit()

    def add_product_history_entries(self, entries: List[ProductHistory]):
        with self.open_session() as session:
            session.add_all(entries)
            session.commit()

    def get_products(self):
        with self.open_session() as session:
            return session.query(Product).all()

    def get_variant(self, product_id: string, variant_id: string) -> ProductVariant:
        with self.open_session() as session:
            return self._get_variant(product_id, variant_id, session)

    def get_variant_history(self, product_id, variant_id):
        with self.open_session() as session:
            return session.query(ProductHistory)\
                .filter_by(product_id=product_id, variant_id=variant_id)\
                .order_by(ProductHistory.timestamp)\
                .all()

    def get_last_in_stock_variant_history(self, product_id: str, variant_id: str, event):
        with self.open_session() as session:
            return session.query(ProductHistory)\
                .filter_by(product_id=product_id, variant_id=variant_id, event=event)\
                .order_by(ProductHistory.timestamp.desc())\
                .first()

    @staticmethod
    def _get_variant(product_id, variant_id, session: Session):
        return session.query(ProductVariant).filter_by(product_id=product_id, id=variant_id).first()

    def get_all_product_variants(self, product_id) -> List[ProductVariant]:
        with self.open_session() as session:
            return session.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()

    def get_products_last_saved_timestamp(self):
        with self.open_session() as session:
            result = session.query(func.max(Product.last_updated)).scalar()
            if not result:
                result = datetime.datetime.now()
            return result

    # Returns True if the keyword was added, and False if the keyword was not added because it already exists.
    def add_watch_keyword(self, username, keyword):
        with self.open_session() as session:
            trigger = self._get_notification_rule(session, username, keyword)
            if trigger is not None:
                return False

            trigger = Trigger(username=username, keyword=keyword)
            session.add(trigger)
            session.commit()
            return True

    def get_user_notification_rules(self, username):
        with self.open_session() as session:
            return session.query(Trigger).filter_by(username=username).all()

    @staticmethod
    def get_all_notification_rules():
        return {}

    @staticmethod
    def _get_notification_rule(session: Session, username: string, keyword: string):
        return session.query(Trigger).filter_by(username=username, keyword=keyword).one_or_none()

    def delete_trigger(self, username, keyword):
        with self.open_session() as session:
            rowcount = session.query(Trigger).filter_by(username=username, keyword=keyword).delete()
            session.commit()
            return rowcount > 0
