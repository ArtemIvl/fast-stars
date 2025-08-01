"""add username to task

Revision ID: c51d15ac03b9
Revises: e416aec1349c
Create Date: 2025-05-23 02:28:52.495496

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c51d15ac03b9"
down_revision: Union[str, None] = "e416aec1349c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("tasks", sa.Column("username", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tasks", "username")
    # ### end Alembic commands ###
