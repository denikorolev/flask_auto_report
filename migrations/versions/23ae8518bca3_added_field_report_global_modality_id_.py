"""added field report_global_modality_id to the SentenceBase

Revision ID: 23ae8518bca3
Revises: 729253196568
Create Date: 2025-09-18 13:39:13.818643
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "23ae8518bca3"
down_revision = "729253196568"
branch_labels = None
depends_on = None


def upgrade():
    # --- 1) Добавляем колонку во все таблицы предложений ---
    with op.batch_alter_table("body_sentences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_global_modality_id", sa.BigInteger(), nullable=True))

    with op.batch_alter_table("head_sentences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_global_modality_id", sa.BigInteger(), nullable=True))

    with op.batch_alter_table("tail_sentences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_global_modality_id", sa.BigInteger(), nullable=True))

    # --- 2) PASS 1: Заполняем по соответствию report_type.type_text -> report_categories.name (is_global = TRUE) ---

    # HEAD
    op.execute(
        """
        UPDATE head_sentences AS hs
        SET report_global_modality_id = rc.id
        FROM report_type AS rt
        JOIN report_categories AS rc
          ON rc.name = rt.type_text
         AND rc.is_global = TRUE
        WHERE hs.report_type_id = rt.id
          AND (hs.report_global_modality_id IS NULL OR hs.report_global_modality_id <> rc.id);
        """
    )

    # BODY
    op.execute(
        """
        UPDATE body_sentences AS bs
        SET report_global_modality_id = rc.id
        FROM report_type AS rt
        JOIN report_categories AS rc
          ON rc.name = rt.type_text
         AND rc.is_global = TRUE
        WHERE bs.report_type_id = rt.id
          AND (bs.report_global_modality_id IS NULL OR bs.report_global_modality_id <> rc.id);
        """
    )

    # TAIL
    op.execute(
        """
        UPDATE tail_sentences AS ts
        SET report_global_modality_id = rc.id
        FROM report_type AS rt
        JOIN report_categories AS rc
          ON rc.name = rt.type_text
         AND rc.is_global = TRUE
        WHERE ts.report_type_id = rt.id
          AND (ts.report_global_modality_id IS NULL OR ts.report_global_modality_id <> rc.id);
        """
    )

    
def downgrade():
    # Откатываем только схему (данные оставляем как есть)
    with op.batch_alter_table("tail_sentences", schema=None) as batch_op:
        batch_op.drop_column("report_global_modality_id")

    with op.batch_alter_table("head_sentences", schema=None) as batch_op:
        batch_op.drop_column("report_global_modality_id")

    with op.batch_alter_table("body_sentences", schema=None) as batch_op:
        batch_op.drop_column("report_global_modality_id")