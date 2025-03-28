"""added table body_sentences and linked with head_sentences

Revision ID: 614f356cb11b
Revises: 5898e6994759
Create Date: 2025-02-17 01:00:51.575495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '614f356cb11b'
down_revision = '5898e6994759'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('body_sentence_groups',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('body_sentence_group_link',
    sa.Column('body_sentence_id', sa.BigInteger(), nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['body_sentence_id'], ['body_sentences.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['body_sentence_groups.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('body_sentence_id', 'group_id')
    )
    with op.batch_alter_table('body_sentence_group_link', schema=None) as batch_op:
        batch_op.create_index('ix_body_sentence_group', ['body_sentence_id', 'group_id'], unique=False)

    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('body_sentence_group_id', sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key(None, 'body_sentence_groups', ['body_sentence_group_id'], ['id'], ondelete='SET NULL')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('body_sentence_group_id')

    with op.batch_alter_table('body_sentence_group_link', schema=None) as batch_op:
        batch_op.drop_index('ix_body_sentence_group')

    op.drop_table('body_sentence_group_link')
    op.drop_table('body_sentence_groups')
    # ### end Alembic commands ###
