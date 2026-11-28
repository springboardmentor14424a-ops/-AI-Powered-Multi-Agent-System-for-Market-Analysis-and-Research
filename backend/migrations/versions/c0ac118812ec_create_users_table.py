
"""create users table

Revision ID: c0ac118812ec
Revises:
Create Date: 2026-11-23 07:45:00.609828
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0ac118812ec'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table."""

    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('user_id')
    )

    op.create_index(
        op.f('ix_users_email'),
        'users',
        ['email'],
        unique=True
    )


def downgrade() -> None:
    """Remove users table."""

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
