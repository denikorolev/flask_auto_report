"""Add rank field to Role

Revision ID: b5b946f293d9
Revises: ff86b9d701c2
Create Date: 2025-01-22 11:16:31.986612

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'b5b946f293d9'
down_revision = 'ff86b9d701c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rank', sa.Integer(), nullable=True))

    # ### end Alembic commands ###
    # Заполняем значения для существующих записей
    op.execute("UPDATE roles SET rank = 3 WHERE id = 1")  # admin
    op.execute("UPDATE roles SET rank = 1 WHERE id = 2")  # user
    op.execute("UPDATE roles SET rank = 2 WHERE id = 3")  # superuser
    op.execute("UPDATE roles SET rank = 4 WHERE id = 4")  # superadmin

   


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.drop_column('rank')

    # ### end Alembic commands ###
