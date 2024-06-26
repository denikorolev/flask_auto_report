from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7346c4bcb2f'
down_revision = '04926b2ade46'
branch_labels = None
depends_on = None

def upgrade():
    # Check if the column already exists
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='report_paragraphs' AND column_name='paragraph_visible'"))
    if result.fetchone() is None:
        with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
            batch_op.add_column(sa.Column('paragraph_visible', sa.Boolean(), nullable=False, server_default=sa.false()))
            batch_op.alter_column('paragraph_visible', server_default=None)

def downgrade():
    with op.batch_alter_table('report_paragraphs', schema=None) as batch_op:
        batch_op.drop_column('paragraph_visible')
