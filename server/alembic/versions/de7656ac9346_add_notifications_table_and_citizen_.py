"""Add notifications table and citizen_token to issues

Revision ID: de7656ac9346
Revises: c1a2b3d4e5f6
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de7656ac9346'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('citizen_token', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_citizen_token', 'notifications', ['citizen_token'], unique=False)
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    
    # Add citizen_token column to issues table
    op.add_column('issues', sa.Column('citizen_token', sa.String(), nullable=True))
    op.create_index('ix_issues_citizen_token', 'issues', ['citizen_token'], unique=False)


def downgrade() -> None:
    # Remove citizen_token from issues
    op.drop_index('ix_issues_citizen_token', table_name='issues')
    op.drop_column('issues', 'citizen_token')
    
    # Drop notifications table
    op.drop_index('ix_notifications_id', table_name='notifications')
    op.drop_index('ix_notifications_citizen_token', table_name='notifications')
    op.drop_table('notifications')
