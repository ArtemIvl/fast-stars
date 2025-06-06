"""Change balance and bonus to Numeric, added is_vip to user

Revision ID: 19a1d3634b1d
Revises: 280181e86e1c
Create Date: 2025-05-07 14:57:04.486085

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "19a1d3634b1d"
down_revision: Union[str, None] = "280181e86e1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "daily_bonus_claims",
        "bonus_amount",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )
    op.add_column("users", sa.Column("is_vip", sa.Boolean(), nullable=True))
    op.alter_column(
        "users",
        "stars",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "users",
        "stars",
        existing_type=sa.Numeric(precision=10, scale=2),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
    )
    op.drop_column("users", "is_vip")
    op.alter_column(
        "daily_bonus_claims",
        "bonus_amount",
        existing_type=sa.Numeric(precision=10, scale=2),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
    )
    # ### end Alembic commands ###
