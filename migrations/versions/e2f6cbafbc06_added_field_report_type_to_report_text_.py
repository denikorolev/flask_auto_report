"""added field report_type to report_text_snapshots table

Revision ID: e2f6cbafbc06
Revises: 0955294c9a21
Create Date: 2025-03-25 15:28:30.282374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f6cbafbc06'
down_revision = '0955294c9a21'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_text_snapshots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('report_type', sa.SmallInteger(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_text_snapshots', schema=None) as batch_op:
        batch_op.drop_column('report_type')

    # ### end Alembic commands ###
