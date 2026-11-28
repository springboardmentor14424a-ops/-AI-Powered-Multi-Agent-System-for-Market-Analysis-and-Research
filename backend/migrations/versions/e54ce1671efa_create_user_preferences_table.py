
"""create user preferences table

Revision ID: e54ce1671efa
Revises: dd1dc87f9ce1
Create Date: 2026-11-25 08:16:49.225207

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = 'e54ce1671efa'
down_revision: Union[str, Sequence[str], None] = 'dd1dc87f9ce1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user preferences table."""

    op.create_table(
        'user_preferences',

        sa.Column(
            'preference_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'preferred_market',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'default_analysis_period',
            sa.String(length=20),
            nullable=False
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.user_id'],
            ondelete='CASCADE'
        ),

        sa.PrimaryKeyConstraint('preference_id'),

        sa.UniqueConstraint(
            'user_id',
            name='uq_user_preference'
        )
    )

    op.create_index(
        op.f('ix_user_preferences_preference_id'),
        'user_preferences',
        ['preference_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove user preferences table."""

    op.drop_index(
        op.f('ix_user_preferences_preference_id'),
        table_name='user_preferences'
    )

    op.drop_table('user_preferences')
