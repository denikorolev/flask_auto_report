"""deleted field is_system

Revision ID: 075abe49574b
Revises: f2c9b6adcddf
Create Date: 2025-05-10 14:57:42.703158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '075abe49574b'
down_revision = 'f2c9b6adcddf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.drop_column('is_system')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_system', sa.BOOLEAN(), autoincrement=False, nullable=False))

    # ### end Alembic commands ###
