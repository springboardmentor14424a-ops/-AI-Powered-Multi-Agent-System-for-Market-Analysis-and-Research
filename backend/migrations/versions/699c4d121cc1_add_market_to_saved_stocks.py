
"""add market to saved stocks

Revision ID: 699c4d121cc1
Revises: 6ec178cb9c5b
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "699c4d121cc1"
down_revision: Union[str, Sequence[str], None] = "6ec178cb9c5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add market as nullable temporarily.
    op.add_column(
        "saved_stocks",
        sa.Column("market", sa.String(length=30), nullable=True)
    )

    # 2. Backfill existing records using confirmed exchange mappings.
    op.execute("""
        UPDATE saved_stocks
        SET market = CASE
            WHEN ticker IN ('MSFT', 'GOOGL', 'AAPL') THEN 'NASDAQ'
            WHEN ticker = 'TCS' THEN 'BSE'
            ELSE NULL
        END
        WHERE saved_stock_id IN (3, 5, 6, 8)
    """)

    # 3. Verify that every existing record has a market.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM saved_stocks
                WHERE market IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Migration stopped: one or more saved stocks have no market mapping.';
            END IF;
        END
        $$;
    """)

    # 4. Make market mandatory.
    op.alter_column(
        "saved_stocks",
        "market",
        existing_type=sa.String(length=30),
        nullable=False
    )

    # 5. Replace the old unique constraint.
    op.drop_constraint(
        "uq_saved_stock_user_ticker",
        "saved_stocks",
        type_="unique"
    )

    op.create_unique_constraint(
        "uq_saved_stock_user_ticker_market",
        "saved_stocks",
        ["user_id", "ticker", "market"]
    )


def downgrade() -> None:
    # Restore the previous uniqueness rule.
    op.drop_constraint(
        "uq_saved_stock_user_ticker_market",
        "saved_stocks",
        type_="unique"
    )

    op.create_unique_constraint(
        "uq_saved_stock_user_ticker",
        "saved_stocks",
        ["user_id", "ticker"]
    )

    op.drop_column("saved_stocks", "market")
