"""add product.availability_stats

Revision ID: fff6ca437508
Revises: 7a429bd19ff1
Create Date: 2019-07-03 00:28:49.213245

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import Column, BOOLEAN

revision = 'fff6ca437508'
down_revision = '7a429bd19ff1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', Column('availability_stats', BOOLEAN, default=True))


def downgrade():
    op.drop_column('products', 'availability_stats')
