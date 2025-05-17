"""added field 'username' to User class

Revision ID: f882686741a4
Revises: 075abe49574b
Create Date: 2025-05-15 23:13:44.683981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f882686741a4'
down_revision = '075abe49574b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(length=80), nullable=True))
    op.execute("UPDATE users SET username = user_name")
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username', existing_type=sa.String(length=80), nullable=False)
        batch_op.drop_column('user_name')


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_name', sa.String(), nullable=True))
    op.execute("UPDATE users SET user_name = username")
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('user_name', existing_type=sa.String(), nullable=False)
        batch_op.drop_column('username')
