"""Add username field to giveaways

Revision ID: 5ff015e3e31a
Revises: ee7a120aa69a
Create Date: 2025-06-18 15:14:06.867555

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ff015e3e31a"
down_revision: Union[str, None] = "ee7a120aa69a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("giveaways", sa.Column("username", sa.String(), nullable=True))
    op.alter_column(
        "giveaways", "num_of_winners", existing_type=sa.INTEGER(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "giveaways", "num_of_winners", existing_type=sa.INTEGER(), nullable=True
    )
    op.drop_column("giveaways", "username")
    # ### end Alembic commands ###
