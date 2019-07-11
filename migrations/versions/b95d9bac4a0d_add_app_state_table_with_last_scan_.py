"""add app_state table with last_scan_timestamp

Revision ID: b95d9bac4a0d
Revises: 12fb133c4435
Create Date: 2019-07-05 02:03:12.759208

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b95d9bac4a0d'
down_revision = '12fb133c4435'
branch_labels = None
depends_on = None


def upgrade():
    table = op.create_table('app_state',
                    sa.Column('id', sa.INTEGER, primary_key=True, autoincrement=True),
                    sa.Column('last_scan_timestamp', sa.DATETIME())
                    )
    op.bulk_insert(table, [
        {'last_scan_timestamp': None}
    ])


def downgrade():
    op.drop_table('app_state')
