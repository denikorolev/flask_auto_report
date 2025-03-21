"""delete field paragraph_type and all accompanying logic

Revision ID: c339bbe7ccbf
Revises: f8d877f18bb6
Create Date: 2025-03-12 13:44:58.797628

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c339bbe7ccbf'
down_revision = 'f8d877f18bb6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('is_impression',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.drop_column('paragraph_type')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paragraph_type', postgresql.ENUM('text', 'custom', 'impression', 'clincontext', 'scanparam', 'dinamics', 'scanlimits', 'title', name='paragraph_type_enum'), server_default=sa.text("'text'::paragraph_type_enum"), autoincrement=False, nullable=True))
        batch_op.alter_column('is_impression',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###
