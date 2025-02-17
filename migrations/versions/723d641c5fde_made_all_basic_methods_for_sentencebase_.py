"""made all basic methods for SentenceBase, made SentenceGroupBase and made basic methods for it

Revision ID: 723d641c5fde
Revises: ef767f5c3a83
Create Date: 2025-02-17 16:00:24.812973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '723d641c5fde'
down_revision = 'ef767f5c3a83'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('head_sentence_groups',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('head_sentence_group_link',
    sa.Column('head_sentence_id', sa.BigInteger(), nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['head_sentence_groups.id'], ondelete="CASCADE"),
    sa.ForeignKeyConstraint(['head_sentence_id'], ['head_sentences.id'], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint('head_sentence_id', 'group_id')
    )
    with op.batch_alter_table('head_sentence_group_link', schema=None) as batch_op:
        batch_op.create_index('ix_head_sentence_group', ['head_sentence_id', 'group_id'], unique=False)
        batch_op.create_index('ix_head_sentence_group_link_group', ['group_id'], unique=False)

    with op.batch_alter_table('head_sentence_paragraph_link', schema=None) as batch_op:
        batch_op.drop_index('ix_head_sentence_paragraph')

    op.drop_table('head_sentence_paragraph_link')
    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.drop_constraint('head_sentences_body_sentence_group_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'body_sentence_groups', ['body_sentence_group_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('head_sentence_group_id', sa.BigInteger(), nullable=True))
        batch_op.create_index('ix_paragraph_head_sentence_group', ['head_sentence_group_id'], unique=False)
        batch_op.drop_constraint('report_paragraphs_tail_sentence_group_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'head_sentence_groups', ['head_sentence_group_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'tail_sentence_groups', ['tail_sentence_group_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('report_paragraphs_tail_sentence_group_id_fkey', 'tail_sentence_groups', ['tail_sentence_group_id'], ['id'], ondelete='SET NULL')
        batch_op.drop_index('ix_paragraph_head_sentence_group')
        batch_op.drop_column('head_sentence_group_id')

    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('head_sentences_body_sentence_group_id_fkey', 'body_sentence_groups', ['body_sentence_group_id'], ['id'], ondelete='SET NULL')

    op.create_table('head_sentence_paragraph_link',
    sa.Column('head_sentence_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('paragraph_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['head_sentence_id'], ['head_sentences.id'], name='head_sentence_paragraph_link_head_sentence_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['paragraph_id'], ['report_paragraphs.id'], name='head_sentence_paragraph_link_paragraph_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('head_sentence_id', 'paragraph_id', name='head_sentence_paragraph_link_pkey')
    )
    with op.batch_alter_table('head_sentence_paragraph_link', schema=None) as batch_op:
        batch_op.create_index('ix_head_sentence_paragraph', ['head_sentence_id', 'paragraph_id'], unique=False)

    with op.batch_alter_table('head_sentence_group_link', schema=None) as batch_op:
        batch_op.drop_index('ix_head_sentence_group_link_group')
        batch_op.drop_index('ix_head_sentence_group')

    op.drop_table('head_sentence_group_link')
    op.drop_table('head_sentence_groups')
    # ### end Alembic commands ###
