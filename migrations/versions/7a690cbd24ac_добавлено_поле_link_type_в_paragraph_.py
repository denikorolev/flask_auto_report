"""Добавлено поле link_type в paragraph_links

Revision ID: 7a690cbd24ac
Revises: 3a10b26f5d39
Create Date: 2025-02-08 15:59:40.334597

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '7a690cbd24ac'
down_revision = '3a10b26f5d39'
branch_labels = None
depends_on = None

# Определяем ENUM
link_type_enum = ENUM("equivalent", "expanding", "excluding", "additional", name="paragraph_link_type", create_type=True)

# Имя таблицы
TABLE_NAME = "paragraph_links"

def upgrade():
    # 🔹 1. Создаем ENUM-тип в БД
    link_type_enum.create(op.get_bind(), checkfirst=True)

    # 🔹 2. Добавляем колонку
    op.add_column(TABLE_NAME, sa.Column("link_type", link_type_enum, nullable=True))

    # 🔹 3. Заполняем старые данные значением "expanding"
    op.execute(f"UPDATE {TABLE_NAME} SET link_type = 'expanding' WHERE link_type IS NULL")

    # 🔹 4. Делаем колонку обязательной
    op.alter_column(TABLE_NAME, "link_type", nullable=False)

def downgrade():
    # 🔹 1. Удаляем колонку
    op.drop_column(TABLE_NAME, "link_type")

    # 🔹 2. Удаляем тип ENUM
    link_type_enum.drop(op.get_bind(), checkfirst=True)