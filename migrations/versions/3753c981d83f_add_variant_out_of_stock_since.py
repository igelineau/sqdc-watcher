"""add_variant_out_of_stock_since

Revision ID: 3753c981d83f
Revises: b95d9bac4a0d
Create Date: 2019-07-13 22:58:27.176435

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import Column, BOOLEAN

revision = '3753c981d83f'
down_revision = 'b95d9bac4a0d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('product_variants', Column('out_of_stock_since', BOOLEAN, default=True))


def downgrade():
    op.drop_column('product_variants', 'out_of_stock_since')
