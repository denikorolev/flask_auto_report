"""changed aditonal to additional

Revision ID: 09588ffb28e7
Revises: 688557ce0476
Create Date: 2025-03-17 12:19:22.761648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09588ffb28e7'
down_revision = '688557ce0476'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_additional', sa.Boolean(), nullable=True))
        batch_op.alter_column('str_before',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('str_after',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('is_aditional',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    # ### end Alembic commands ###
    # Перенос данных из старого поля в новое
    op.execute("""
        UPDATE report_paragraphs
        SET is_additional = is_aditional
    """)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.alter_column('is_aditional',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('str_after',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('str_before',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.drop_column('is_additional')

    # ### end Alembic commands ###
