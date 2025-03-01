"""deleted ParagraphType class and all additional logic

Revision ID: 10547b73ac57
Revises: 723d641c5fde
Create Date: 2025-02-20 14:11:56.889700

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "10547b73ac57"
down_revision = "723d641c5fde"
branch_labels = None
depends_on = None


def upgrade():
   
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paragraph_type_enum') THEN
                CREATE TYPE paragraph_type_enum AS ENUM (
                    'text', 'custom', 'impression', 'clincontext', 
                    'scanparam', 'dinamics', 'scanlimits', 'title'
                );
            END IF;
        END $$;
    """)

   
    op.add_column("report_paragraphs", sa.Column(
        "paragraph_type",
        sa.Enum("text", "custom", "impression", "clincontext", 
                "scanparam", "dinamics", "scanlimits", "title",
                name="paragraph_type_enum"),
        nullable=True, 
        server_default="text"  
    ))

   
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE report_paragraphs p
        SET paragraph_type = pt.type_name::paragraph_type_enum
        FROM paragraph_types pt
        WHERE p.type_paragraph_id = pt.id
    """))

   
    op.alter_column("report_paragraphs", "paragraph_type", nullable=False)

   
    with op.batch_alter_table("report_paragraphs", schema=None) as batch_op:
        batch_op.drop_constraint("report_paragraphs_type_paragraph_id_fkey", type_="foreignkey")
        batch_op.drop_column("type_paragraph_id")

    
    op.drop_table("paragraph_types")

    
    with op.batch_alter_table("report_paragraphs", schema=None) as batch_op:
        batch_op.drop_constraint("report_paragraphs_head_sentence_group_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("report_paragraphs_tail_sentence_group_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(None, "head_sentence_groups", ["head_sentence_group_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key(None, "tail_sentence_groups", ["tail_sentence_group_id"], ["id"], ondelete="SET NULL")

   
    with op.batch_alter_table("head_sentences", schema=None) as batch_op:
        batch_op.drop_constraint("head_sentences_body_sentence_group_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(None, "body_sentence_groups", ["body_sentence_group_id"], ["id"], ondelete="SET NULL")


def downgrade():
   
    op.create_table(
        "paragraph_types",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("type_name", sa.VARCHAR(length=50), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="paragraph_types_pkey"),
        sa.UniqueConstraint("type_name", name="paragraph_types_type_name_key"),
    )

   
    with op.batch_alter_table("report_paragraphs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("type_paragraph_id", sa.INTEGER(), nullable=False))
        batch_op.create_foreign_key("report_paragraphs_type_paragraph_id_fkey", "paragraph_types", ["type_paragraph_id"], ["id"])

    
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO paragraph_types (type_name)
        SELECT DISTINCT paragraph_type::text FROM report_paragraphs
        ON CONFLICT (type_name) DO NOTHING
    """))

    conn.execute(sa.text("""
        UPDATE report_paragraphs p
        SET type_paragraph_id = pt.id
        FROM paragraph_types pt
        WHERE p.paragraph_type::text = pt.type_name
    """))

   
    with op.batch_alter_table("report_paragraphs", schema=None) as batch_op:
        batch_op.drop_column("paragraph_type")

   
    with op.batch_alter_table("report_paragraphs", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.create_foreign_key("report_paragraphs_head_sentence_group_id_fkey", "head_sentence_groups", ["head_sentence_group_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("report_paragraphs_tail_sentence_group_id_fkey", "tail_sentence_groups", ["tail_sentence_group_id"], ["id"], ondelete="CASCADE")

  
    with op.batch_alter_table("head_sentences", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.create_foreign_key("head_sentences_body_sentence_group_id_fkey", "body_sentence_groups", ["body_sentence_group_id"], ["id"], ondelete="CASCADE")

   
    op.execute("DROP TYPE IF EXISTS paragraph_type_enum")