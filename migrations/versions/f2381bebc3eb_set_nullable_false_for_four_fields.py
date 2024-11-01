"""set nullable false for four fields

Revision ID: f2381bebc3eb
Revises: e48a3e3aa893
Create Date: 2024-10-29 10:58:35.033906

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2381bebc3eb'
down_revision = 'e48a3e3aa893'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('key_words_group', schema=None) as batch_op:
        batch_op.alter_column('profile_id',
               existing_type=sa.BIGINT(),
               nullable=False)

    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.alter_column('paragraph_weight',
               existing_type=sa.SMALLINT(),
               nullable=False)

    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.alter_column('profile_id',
               existing_type=sa.BIGINT(),
               nullable=False)

    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.alter_column('default_profile',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.alter_column('default_profile',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    with op.batch_alter_table('report_type', schema=None) as batch_op:
        batch_op.alter_column('profile_id',
               existing_type=sa.BIGINT(),
               nullable=True)

    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.alter_column('paragraph_weight',
               existing_type=sa.SMALLINT(),
               nullable=True)

    with op.batch_alter_table('key_words_group', schema=None) as batch_op:
        batch_op.alter_column('profile_id',
               existing_type=sa.BIGINT(),
               nullable=True)

    # ### end Alembic commands ###