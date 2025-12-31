"""Add votes comments and engagement fields

Revision ID: f1g2h3i4j5k6
Revises: de7656ac9346
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1g2h3i4j5k6'
down_revision: Union[str, None] = 'de7656ac9346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create votes table
    op.create_table('votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('citizen_token', sa.String(), nullable=False),
        sa.Column('vote_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_votes_id', 'votes', ['id'], unique=False)
    op.create_index('ix_votes_citizen_token', 'votes', ['citizen_token'], unique=False)
    op.create_index('ix_votes_issue_citizen', 'votes', ['issue_id', 'citizen_token'], unique=True)
    
    # Create comments table
    op.create_table('comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('citizen_token', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comments_id', 'comments', ['id'], unique=False)
    op.create_index('ix_comments_citizen_token', 'comments', ['citizen_token'], unique=False)
    
    # Add engagement columns to issues table
    op.add_column('issues', sa.Column('upvote_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('issues', sa.Column('priority_score', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Remove engagement columns from issues
    op.drop_column('issues', 'priority_score')
    op.drop_column('issues', 'upvote_count')
    
    # Drop comments table
    op.drop_index('ix_comments_citizen_token', table_name='comments')
    op.drop_index('ix_comments_id', table_name='comments')
    op.drop_table('comments')
    
    # Drop votes table
    op.drop_index('ix_votes_issue_citizen', table_name='votes')
    op.drop_index('ix_votes_citizen_token', table_name='votes')
    op.drop_index('ix_votes_id', table_name='votes')
    op.drop_table('votes')
