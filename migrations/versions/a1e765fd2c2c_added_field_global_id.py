"""added field global_id

Revision ID: a1e765fd2c2c
Revises: db3031f8d99a
Create Date: 2025-07-07 16:07:03.901185

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1e765fd2c2c'
down_revision = 'db3031f8d99a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('global_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key(None, 'report_categories', ['global_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_categories', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('global_id')

    # ### end Alembic commands ###
