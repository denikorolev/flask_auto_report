"""Update models

Revision ID: 570498957987
Revises: d4baf54897fc
Create Date: 2024-09-09 15:51:16.273152

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '570498957987'
down_revision = 'd4baf54897fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('key_word_paragraph_link')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('key_word_paragraph_link',
    sa.Column('key_word_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('paragraph_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['key_word_id'], ['key_words_group.id'], name='key_word_paragraph_link_key_word_id_fkey'),
    sa.ForeignKeyConstraint(['paragraph_id'], ['report_paragraphs.id'], name='key_word_paragraph_link_paragraph_id_fkey'),
    sa.PrimaryKeyConstraint('key_word_id', 'paragraph_id', name='key_word_paragraph_link_pkey')
    )
    # ### end Alembic commands ###
