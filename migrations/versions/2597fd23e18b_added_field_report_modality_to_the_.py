"""added field report_modality to the ReportTextSnapshot

Revision ID: 2597fd23e18b
Revises: 23ae8518bca3
Create Date: 2025-09-18 18:53:45.230462
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2597fd23e18b"
down_revision = "23ae8518bca3"
branch_labels = None
depends_on = None


def upgrade():
    # --- schema changes ---
    with op.batch_alter_table("body_sentences", schema=None) as batch_op:
        batch_op.drop_column("report_type_id")

    with op.batch_alter_table("head_sentences", schema=None) as batch_op:
        batch_op.drop_column("report_type_id")

    with op.batch_alter_table("report_text_snapshots", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_modality", sa.BigInteger(), nullable=True))

    with op.batch_alter_table("tail_sentences", schema=None) as batch_op:
        batch_op.drop_column("report_type_id")

    # --- data backfill: fill report_text_snapshots.report_modality from reports.global_category_id ---
    # Only when a matching report exists and has a non-null global_category_id.
    op.execute(
        """
        UPDATE report_text_snapshots AS s
        SET report_modality = r.global_category_id
        FROM reports AS r
        WHERE r.id = s.report_id
          AND r.global_category_id IS NOT NULL
          AND (s.report_modality IS NULL OR s.report_modality <> r.global_category_id);
        """
    )


def downgrade():
    # rollback schema only (data rollback is not required)
    with op.batch_alter_table("tail_sentences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_type_id", sa.BIGINT(), autoincrement=False, nullable=True))

    with op.batch_alter_table("report_text_snapshots", schema=None) as batch_op:
        batch_op.drop_column("report_modality")

    with op.batch_alter_table("head_sentences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_type_id", sa.BIGINT(), autoincrement=False, nullable=True))

    with op.batch_alter_table("body_sentences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("report_type_id", sa.BIGINT(), autoincrement=False, nullable=True))