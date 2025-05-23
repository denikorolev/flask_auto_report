"""make user_id field on sentence_base class ondelete set null

Revision ID: 1cdda67012c3
Revises: b69379cbd408
Create Date: 2025-05-19 13:57:18.268126

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cdda67012c3'
down_revision = 'b69379cbd408'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('body_sentences', schema=None) as batch_op:
        batch_op.drop_constraint('body_sentences_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.drop_constraint('head_sentences_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('tail_sentences', schema=None) as batch_op:
        batch_op.drop_constraint('tail_sentences_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='SET NULL')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tail_sentences', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('tail_sentences_user_id_fkey', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('head_sentences_user_id_fkey', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('body_sentences', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('body_sentences_user_id_fkey', 'users', ['user_id'], ['id'])

    # ### end Alembic commands ###
