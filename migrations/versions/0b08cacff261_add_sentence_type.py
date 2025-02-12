"""add sentence_type

Revision ID: 0b08cacff261
Revises: 7a690cbd24ac
Create Date: 2025-02-12 11:09:46.821661

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0b08cacff261'
down_revision = '7a690cbd24ac'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем ENUM тип, если он еще не существует
    sentence_type_enum = postgresql.ENUM('head', 'body', 'tail', name='sentence_type_enum', create_type=True)
    sentence_type_enum.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table('sentences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sentence_type', sentence_type_enum, nullable=True))

    # Заполняем существующие записи на основе старых данных
    op.execute("UPDATE sentences SET sentence_type = 'head' WHERE is_main = True")
    op.execute("UPDATE sentences SET sentence_type = 'body' WHERE is_main = False AND index != 0")
    op.execute("UPDATE sentences SET sentence_type = 'tail' WHERE is_main = False AND index = 0")
    op.execute("UPDATE sentences SET sentence_type = 'tail' WHERE sentence_type IS NULL")  # Фикс для возможных пропусков

    # Теперь делаем колонку NOT NULL, без server_default
    with op.batch_alter_table('sentences', schema=None) as batch_op:
        batch_op.alter_column("sentence_type", nullable=False)


def downgrade():
    with op.batch_alter_table('sentences', schema=None) as batch_op:
        batch_op.drop_column('sentence_type')

    # Удаляем ENUM тип, если он больше не используется
    sentence_type_enum = postgresql.ENUM('head', 'body', 'tail', name='sentence_type_enum', create_type=False)
    sentence_type_enum.drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
