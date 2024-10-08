"""Add report_side to Report model

Revision ID: 8b2865a48360
Revises: 794e631be2e4
Create Date: 2024-08-21 11:40:13.957788

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b2865a48360'
down_revision = '794e631be2e4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('report_side', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_column('report_side')

    # ### end Alembic commands ###
