"""Make title_paragraph and bold_paragraph fields non-nullable

Revision ID: afe311aef876
Revises: 55b93cf261eb
Create Date: 2024-10-05 16:43:14.593445

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afe311aef876'
down_revision = '55b93cf261eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.alter_column('title_paragraph',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('bold_paragraph',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.alter_column('bold_paragraph',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('title_paragraph',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###
