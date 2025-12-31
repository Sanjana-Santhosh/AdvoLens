"""Add users table and department to issues

Revision ID: c1a2b3d4e5f6
Revises: bc70ba100bb7
Create Date: 2024-12-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, None] = 'bc70ba100bb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Create userrole enum if not exists
    connection.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('super_admin', 'official');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create department enum if not exists
    connection.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE department AS ENUM ('municipality', 'water_authority', 'kseb', 'pwd', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create users table if not exists
    connection.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR NOT NULL UNIQUE,
            hashed_password VARCHAR NOT NULL,
            name VARCHAR,
            role userrole DEFAULT 'official',
            department department
        );
        CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
        CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
    """))
    
    # Add department column to issues if not exists
    connection.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE issues ADD COLUMN department department DEFAULT 'other';
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $$;
    """))


def downgrade() -> None:
    # Remove department column from issues
    op.drop_column('issues', 'department')
    
    # Drop users table
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='department').drop(op.get_bind(), checkfirst=True)
