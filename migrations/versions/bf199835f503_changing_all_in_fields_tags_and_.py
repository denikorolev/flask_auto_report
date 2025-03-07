"""changing all '' in fields tags and comments to Null

Revision ID: bf199835f503
Revises: 9fb3c73e4888
Create Date: 2025-03-07 13:08:14.561159

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf199835f503'
down_revision = '9fb3c73e4888'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем временное поле 'temp' (оставляем из авто-генерации)
    with op.batch_alter_table('body_sentences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.Boolean(), nullable=True))

    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.Boolean(), nullable=True))

    with op.batch_alter_table('tail_sentences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.Boolean(), nullable=True))

    # Меняем "" на NULL в полях tags и comment
    op.execute("UPDATE body_sentences SET tags = NULL WHERE tags = '';")
    op.execute("UPDATE body_sentences SET comment = NULL WHERE comment = '';")

    op.execute("UPDATE head_sentences SET tags = NULL WHERE tags = '';")
    op.execute("UPDATE head_sentences SET comment = NULL WHERE comment = '';")

    op.execute("UPDATE tail_sentences SET tags = NULL WHERE tags = '';")
    op.execute("UPDATE tail_sentences SET comment = NULL WHERE comment = '';")

    print("✅ Пустые строки в tags и comment заменены на NULL")


def downgrade():
    # Удаляем временное поле 'temp'
    with op.batch_alter_table('tail_sentences', schema=None) as batch_op:
        batch_op.drop_column('temp')

    with op.batch_alter_table('head_sentences', schema=None) as batch_op:
        batch_op.drop_column('temp')

    with op.batch_alter_table('body_sentences', schema=None) as batch_op:
        batch_op.drop_column('temp')

    print("⚠️ Обратная замена NULL на '' не выполняется, так как это может исказить данные")