"""add product last notification timestamp

Revision ID: 8ddd32cb4c77
Revises: fff6ca437508
Create Date: 2019-07-04 01:48:11.603080

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import BOOLEAN, Column

revision = '8ddd32cb4c77'
down_revision = 'fff6ca437508'
branch_labels = None
depends_on = None

COLUMN_NAME = 'last_in_stock_notification'


def upgrade():
    op.add_column('products', Column(COLUMN_NAME, BOOLEAN, default=True))


def downgrade():
    op.drop_column('products', COLUMN_NAME)
