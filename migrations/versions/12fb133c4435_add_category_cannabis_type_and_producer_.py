"""add category, cannabis_type and producer_name to products table

Revision ID: 12fb133c4435
Revises: 8ddd32cb4c77
Create Date: 2019-07-05 00:33:40.736737

"""
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import Column, VARCHAR

revision = '12fb133c4435'
down_revision = '8ddd32cb4c77'
branch_labels = None
depends_on = None


COLUMN_NAME_CATEGORY = 'category'
COLUMN_NAME_CANNABIS_TYPE = 'cannabis_type'
COLUMN_NAME_PRODUCER_NAME = 'producer_name'


def upgrade():
    op.add_column('products', Column(COLUMN_NAME_CATEGORY, VARCHAR))
    op.add_column('products', Column(COLUMN_NAME_CANNABIS_TYPE, VARCHAR))
    op.add_column('products', Column(COLUMN_NAME_PRODUCER_NAME, VARCHAR))


def downgrade():
    op.drop_column('products', COLUMN_NAME_CATEGORY)
    op.drop_column('products', COLUMN_NAME_CANNABIS_TYPE)
    op.drop_column('products', COLUMN_NAME_PRODUCER_NAME)
