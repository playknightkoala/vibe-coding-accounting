"""change transaction_date to timestamp

Revision ID: a1b2c3d4e5f6
Revises: ef8c1e512264
Create Date: 2025-11-19 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'ef8c1e512264'
branch_labels = None
depends_on = None


def upgrade():
    # Change transaction_date from DATE to TIMESTAMP
    op.alter_column('transactions', 'transaction_date',
                    existing_type=sa.DATE(),
                    type_=sa.DateTime(),
                    existing_nullable=False)


def downgrade():
    # Revert transaction_date from TIMESTAMP to DATE
    op.alter_column('transactions', 'transaction_date',
                    existing_type=sa.DateTime(),
                    type_=sa.DATE(),
                    existing_nullable=False)
