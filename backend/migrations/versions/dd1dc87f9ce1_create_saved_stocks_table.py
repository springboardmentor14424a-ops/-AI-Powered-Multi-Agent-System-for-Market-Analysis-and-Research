
"""create saved stocks table

Revision ID: dd1dc87f9ce1
Revises: c0ac118812ec
Create Date: 2026-11-25 07:41:12.756803

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'dd1dc87f9ce1'
down_revision: Union[str, Sequence[str], None] = 'c0ac118812ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create saved stocks table."""

    op.create_table(
        'saved_stocks',

        sa.Column(
            'saved_stock_id',
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
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.user_id'],
            ondelete='CASCADE'
        ),

        sa.PrimaryKeyConstraint('saved_stock_id'),

        sa.UniqueConstraint(
            'user_id',
            'ticker',
            name='uq_user_saved_stock'
        )
    )

    op.create_index(
        op.f('ix_saved_stocks_saved_stock_id'),
        'saved_stocks',
        ['saved_stock_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove saved stocks table."""

    op.drop_index(
        op.f('ix_saved_stocks_saved_stock_id'),
        table_name='saved_stocks'
    )

    op.drop_table('saved_stocks')
