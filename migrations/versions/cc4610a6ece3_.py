"""empty message

Revision ID: cc4610a6ece3
Revises: 846cfa5ebac5
Create Date: 2018-07-31 14:34:31.075188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc4610a6ece3'
down_revision = '846cfa5ebac5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('_password', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', '_password')
    # ### end Alembic commands ###
