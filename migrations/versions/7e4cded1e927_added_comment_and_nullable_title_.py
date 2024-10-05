"""Added comment and nullable title_paragraph fields to ReportParagraph

Revision ID: 7e4cded1e927
Revises: 9586753b79fd
Create Date: 2024-10-05 13:38:51.537976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e4cded1e927'
down_revision = '9586753b79fd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title_paragraph', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('comment', sa.String(length=255), nullable=True))

    with op.batch_alter_table('report_subtype', schema=None) as batch_op:
        batch_op.alter_column('subtype_index',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.alter_column('type_index',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.alter_column('profile_id',
               existing_type=sa.BIGINT(),
               nullable=False)
        batch_op.alter_column('report_side',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.alter_column('report_side',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('profile_id',
               existing_type=sa.BIGINT(),
               nullable=True)

    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.alter_column('type_index',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('report_subtype', schema=None) as batch_op:
        batch_op.alter_column('subtype_index',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.drop_column('comment')
        batch_op.drop_column('title_paragraph')

    # ### end Alembic commands ###
