"""Add user_id to report_subtype and make it unnullable

Revision ID: 4e1ddf10dc07
Revises: 1ee843ce4316
Create Date: 2024-09-09 19:57:43.291505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e1ddf10dc07'
down_revision = '1ee843ce4316'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_subtype', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_subtype', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               nullable=True)

    # ### end Alembic commands ###
