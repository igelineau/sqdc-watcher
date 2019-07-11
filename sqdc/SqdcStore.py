import datetime
import logging
import string
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, joinedload

from sqdc.dataobjects.app_state import AppState
from sqdc.dataobjects.base import Base
from sqdc.dataobjects.product import Product as Product
from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.product_variant import ProductVariant
from sqdc.dataobjects.productevent import ProductEvent
from sqdc.dataobjects.sessionwrapper import SessionWrapper
from sqdc.dataobjects.trigger import Trigger
from sqdc.logic.product_calculator import find_by_id

log = logging.getLogger(__name__)

# logging.basicConfig()
sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
# sqlalchemy_logger.setLevel(logging.INFO)


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
        self.db_url = 'sqlite+pysqlite:///' + self.sqlite_db.as_posix()

    def open_session(self) -> SessionWrapper:
        return SessionWrapper(self.session_maker(expire_on_commit=False))

    def initialize(self):

        print('connecting to database: ' + self.db_url)
        self.engine = create_engine(self.db_url)
        self.session_maker = sessionmaker(bind=self.engine)

        Base.metadata.create_all(self.engine)

    def save_products(self, products: List[Product]):
        if len(products) > 0:
            with self.open_session() as session:
                for p in products:
                    session.merge(p)

                session.commit()

    def add_product_history_entries(self, entries: List[ProductHistory]):
        with self.open_session() as session:
            session.add_all(entries)
            session.commit()

    def get_products(self) -> List[Product]:
        with self.open_session() as session:
            results = session\
                .query(Product)\
                .options(joinedload(Product.variants, innerjoin=True)
                         .joinedload(ProductVariant.product, innerjoin=True))\
                .all()
            return results

    def get_variant(self, product_id: string, variant_id: string) -> ProductVariant:
        with self.open_session() as session:
            return self._get_variant(product_id, variant_id, session)

    def get_variant_history(self, product_id, variant_id):
        with self.open_session() as session:
            return session.query(ProductHistory)\
                .filter_by(product_id=product_id, variant_id=variant_id)\
                .order_by(ProductHistory.timestamp)\
                .all()

    def get_last_in_stock_product_history(self, product_id: str, event: ProductEvent) -> ProductHistory:
        with self.open_session() as session:
            return session.query(ProductHistory)\
                .filter_by(product_id=product_id, event=event.name.lower())\
                .order_by(ProductHistory.timestamp.desc())\
                .first()

    def mark_products_notified(self, products: List[Product]):
        with self.open_session() as session:
            for p in [p for p in session.query(Product).all() if find_by_id(products, p)]:
                p.last_in_stock_notification = datetime.datetime.now()
            session.commit()

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

    def get_app_state(self) -> AppState:
        with self.open_session() as session:
            app_state = session.query(AppState).first()
            if app_state is None:
                app_state = AppState()
                session.add(app_state)
                session.commit()

            return session.query(AppState).first()

    def save_app_state(self, app_state: AppState):
        with self.open_session() as session:
            session.merge(app_state)
            session.commit()

    def update_last_scan_timestamp(self, last_scan_timestamp):
        with self.open_session() as session:
            state = session.query(AppState).first()
            state.last_scan_timestamp = last_scan_timestamp
            session.commit()

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
