import datetime
import json
import logging
import string
from pathlib import Path
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, ResultProxy
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.elements import and_

from lib.stores.base import Base
from lib.stores.product import Product as Product
from lib.stores.product_variant import ProductVariant
from lib.stores.sessionwrapper import SessionWrapper
from lib.stores.trigger import Trigger

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
        self.config_file = self.dir.joinpath('config.json')
        self.sqlite_db = self.dir.joinpath(f'data{test_suffix}.db')

    def open_session(self) -> SessionWrapper:
        return SessionWrapper(self.session_maker())

    def initialize(self):
        db_url = 'sqlite:///' + self.sqlite_db.as_posix()
        print('connecting to database: ' + db_url)
        self.engine = create_engine(db_url)
        self.session_maker = sessionmaker(bind=self.engine)

        with self.open_session() as session:
            # session.execute('DROP TABLE IF EXISTS products')
            # session.execute('DROP TABLE IF EXISTS product_variants')
            session.commit()

        Base.metadata.create_all(self.engine)

    def save_products(self, products: List[Product]):
        with self.open_session() as session:
            for p in products:
                self._add_or_update_product(session, p)
                session.commit()

                # for variant in p.get_variants_in_stock():
                #     self._add_or_update_variant(session, p.id, variant.id)
                #     session.commit()

    @staticmethod
    def _add_or_update_product(session: Session, product: Product):
        session.merge(product)
        session.commit()

    def get_products(self):
        with self.open_session() as session:
            return session.query(Product).all()

    @staticmethod
    def _query_product_variant(session: Session, product_id: string, variant_id: string):
        return session\
            .query(ProductVariant)\
            .filter(and_(ProductVariant.product_id == product_id, ProductVariant.id == variant_id))

    def _add_or_update_variant(self, session: Session, variant: ProductVariant):
        existing_entry = self._get_variant(variant.product_id, variant.id, session)
        if existing_entry is None:
            session.add(variant)
            existing_entry = variant
        return existing_entry

    def save_variant_specifications(self, product_id, variant_id, specifications: object):
        with self.open_session() as session:
            variant = self._get_variant(product_id, variant_id, session)
            if variant is None:
                variant = ProductVariant(id=variant_id, product_id=product_id)
            variant.specifications = json.dumps(specifications)
            session.commit()

    def get_variant(self, product_id: string, variant_id: string) -> ProductVariant:
        with self.open_session() as session:
            return self._get_variant(product_id, variant_id, session)

    @staticmethod
    def _get_variant(product_id, variant_id, session: Session):
        return session.query(ProductVariant).filter_by(product_id=product_id, id=variant_id).first()

    def get_all_product_variants(self, product_id) -> List[ProductVariant]:
        with self.open_session() as session:
            return session.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()

    def get_products_last_saved_timestamp(self):
        return datetime.datetime.min

    def get_config(self):
        if not self.config_file.exists():
            return None
        else:
            return json.loads(self.config_file.read_text())

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
            delete_query = Trigger.__table__.delete().where(and_(username == username, keyword == keyword))
            result: ResultProxy = session.execute(delete_query)
            return result.rowcount > 0
