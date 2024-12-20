"""made field active non-nullable

Revision ID: 99def729b1f1
Revises: 26f6ea4bac75
Create Date: 2024-11-23 22:59:13.048719

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99def729b1f1'
down_revision = '26f6ea4bac75'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('active',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('active',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###
