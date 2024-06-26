"""create new db

Revision ID: 04926b2ade46
Revises: 
Create Date: 2024-06-25 11:45:01.202196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04926b2ade46'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('report_type',
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_role', sa.String(), nullable=False),
    sa.Column('user_email', sa.String(), nullable=False),
    sa.Column('user_name', sa.String(), nullable=False),
    sa.Column('user_pass', sa.String(), nullable=False),
    sa.Column('user_bio', sa.Text(), nullable=True),
    sa.Column('user_avatar', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_email')
    )
    op.create_table('report_subtype',
    sa.Column('type', sa.SmallInteger(), nullable=False),
    sa.Column('subtype', sa.String(length=250), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['type'], ['report_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reports',
    sa.Column('userid', sa.BigInteger(), nullable=False),
    sa.Column('comment', sa.String(length=255), nullable=True),
    sa.Column('report_name', sa.String(length=255), nullable=False),
    sa.Column('report_type', sa.Integer(), nullable=False),
    sa.Column('report_subtype', sa.Integer(), nullable=False),
    sa.Column('public', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['report_subtype'], ['report_subtype.id'], ),
    sa.ForeignKeyConstraint(['report_type'], ['report_type.id'], ),
    sa.ForeignKeyConstraint(['userid'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('report_paragraphs',
    sa.Column('paragraph_index', sa.Integer(), nullable=False),
    sa.Column('report_id', sa.BigInteger(), nullable=False),
    sa.Column('paragraph', sa.String(length=255), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sentences',
    sa.Column('paragraph_id', sa.BigInteger(), nullable=False),
    sa.Column('index', sa.SmallInteger(), nullable=False),
    sa.Column('weight', sa.SmallInteger(), nullable=False),
    sa.Column('comment', sa.String(length=100), nullable=False),
    sa.Column('sentence', sa.String(length=400), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['paragraph_id'], ['report_paragraphs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sentences')
    op.drop_table('report_paragraphs')
    op.drop_table('reports')
    op.drop_table('report_subtype')
    op.drop_table('users')
    op.drop_table('report_type')
    # ### end Alembic commands ###
