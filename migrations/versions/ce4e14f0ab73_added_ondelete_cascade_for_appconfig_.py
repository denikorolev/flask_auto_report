"""added ondelete CASCADE for appconfig items

Revision ID: ce4e14f0ab73
Revises: 80ddc775e2e7
Create Date: 2025-01-29 14:19:38.618905

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce4e14f0ab73'
down_revision = '80ddc775e2e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('app_config', schema=None) as batch_op:
        batch_op.drop_constraint('app_config_profile_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'user_profiles', ['profile_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('app_config', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('app_config_profile_id_fkey', 'user_profiles', ['profile_id'], ['id'])

    # ### end Alembic commands ###
