"""Add active field to users table

Revision ID: 26f6ea4bac75
Revises: 3a327743e1c9
Create Date: 2024-11-23 22:51:28.412607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26f6ea4bac75'
down_revision = '3a327743e1c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=True, default=True))


    # Устанавливаем значение active = True для всех существующих записей
    op.execute("UPDATE users SET active = TRUE WHERE active IS NULL")
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('active')

    # ### end Alembic commands ###