
"""create research tasks table

Revision ID: 037873b0d918
Revises: e54ce1671efa
Create Date: 2026-11-25 08:43:07.615252

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = '037873b0d918'
down_revision: Union[str, Sequence[str], None] = 'e54ce1671efa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create research tasks table."""

    op.create_table(
        'research_tasks',

        sa.Column(
            'task_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'ticker',
            sa.String(length=30),
            nullable=False
        ),

        sa.Column(
            'market',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'requested_period',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),

        sa.Column(
            'completed_at',
            sa.DateTime(timezone=True),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.user_id'],
            ondelete='CASCADE'
        ),

        sa.PrimaryKeyConstraint('task_id')
    )

    op.create_index(
        op.f('ix_research_tasks_user_id'),
        'research_tasks',
        ['user_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove research tasks table."""

    op.drop_index(
        op.f('ix_research_tasks_user_id'),
        table_name='research_tasks'
    )

    op.drop_table('research_tasks')
