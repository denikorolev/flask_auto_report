"""added confirmed_at data to all users

Revision ID: b69379cbd408
Revises: f882686741a4
Create Date: 2025-05-17 21:07:51.899046

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'b69379cbd408'
down_revision = 'f882686741a4'
branch_labels = None
depends_on = None


def upgrade():
    # Форматируем дату как datetime объект в UTC
    confirmation_date = datetime.strptime("Sun, 16 Feb 2025 20:51:38 GMT", "%a, %d %b %Y %H:%M:%S %Z")

    # Обновляем напрямую через SQL (без ORM)
    op.execute(
        f"""
        UPDATE users
        SET confirmed_at = '{confirmation_date.isoformat()}'
        WHERE confirmed_at IS NULL
        """
    )


def downgrade():
    # Откат — обнуляем только те записи, у которых стоит указанная дата
    op.execute(
        """
        UPDATE users
        SET confirmed_at = NULL
        WHERE confirmed_at = '2025-02-16T20:51:38'
        """
    )
