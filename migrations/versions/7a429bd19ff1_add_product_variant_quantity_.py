"""add product_variant.quantity_description column

Revision ID: 7a429bd19ff1
Revises: 98ef626ed11c
Create Date: 2019-07-02 22:24:06.246194

"""
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import Column, FLOAT

revision = '7a429bd19ff1'
down_revision = '98ef626ed11c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('product_variants', Column('quantity_description', FLOAT, default=True))


def downgrade():
    op.drop_column('product_variants', 'quantity_description')
