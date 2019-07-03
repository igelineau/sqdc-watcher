"""add product.is_new

Revision ID: 98ef626ed11c
Revises: 0f51d3e61114
Create Date: 2019-07-02 19:10:54.614187

"""
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import Column, BOOLEAN

revision = '98ef626ed11c'
down_revision = '0f51d3e61114'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', Column('is_new', BOOLEAN, default=True))


def downgrade():
    op.drop_column('products', 'is_new')
