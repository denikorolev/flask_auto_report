"""Added key_words_group table

Revision ID: 5f7d0accead4
Revises: 8b2865a48360
Create Date: 2024-08-24 14:41:41.241999

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f7d0accead4'
down_revision = '8b2865a48360'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('key_words_group',
    sa.Column('group_index', sa.Integer(), nullable=False),
    sa.Column('index', sa.Integer(), nullable=False),
    sa.Column('key_word', sa.String(length=50), nullable=False),
    sa.Column('key_word_comment', sa.String(length=100), nullable=True),
    sa.Column('public', sa.Boolean(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('key_words_group')
    # ### end Alembic commands ###
