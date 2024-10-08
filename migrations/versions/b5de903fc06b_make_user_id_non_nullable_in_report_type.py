"""Make user_id non-nullable in report_type

Revision ID: b5de903fc06b
Revises: 82d1bb3d2e53
Create Date: 2024-09-09 19:17:01.219831

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5de903fc06b'
down_revision = '82d1bb3d2e53'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.BIGINT(),
               nullable=True)

    # ### end Alembic commands ###
