"""Add caption and tags to issues

Revision ID: bc70ba100bb7
Revises: 5356ca981e89
Create Date: 2025-12-27 21:56:32.535067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc70ba100bb7'
down_revision: Union[str, None] = '5356ca981e89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add caption and tags columns to issues table
    op.add_column('issues', sa.Column('caption', sa.String(), nullable=True))
    op.add_column('issues', sa.Column('tags', sa.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'tags')
    op.drop_column('issues', 'caption')
