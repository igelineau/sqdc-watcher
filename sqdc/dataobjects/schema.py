from pathlib import Path

from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey, String, DateTime

Path(Path.cwd().joinpath('data'))

metadata = MetaData()

products = Table('products', metadata,
                 Column('id', Integer, primary_key=True)
                 )

product_variants = Table('product_variants', metadata,
                         Column('product_id', None, ForeignKey('products.id'), primary_key=True),
                         Column('variant_id', String, primary_key=True)
                         )

product_history = Table('product_history', metadata,
                        Column('id', Integer, primary_key=True, autoincrement=True),
                        Column('product_id', String, nullable=False),
                        Column('event', String, nullable=False),
                        Column('timestamp', DateTime, nullable=False)
                        )

metadata.create_all()
