"""make hashed_password nullable

Revision ID: 20251126_oauth
Revises: 64f52b1c4310
Create Date: 2025-11-26 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251126_oauth'
down_revision = '64f52b1c4310'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    # Make hashed_password not nullable
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=False)
