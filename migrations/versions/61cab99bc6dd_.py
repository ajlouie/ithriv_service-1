"""empty message

Revision ID: 61cab99bc6dd
Revises: dd3fca520474
Create Date: 2021-04-02 11:49:05.206278

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '61cab99bc6dd'
down_revision = 'dd3fca520474'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ithriv_user', sa.Column('commons_eula_accepted', sa.Boolean(), nullable=True))
    op.add_column('ithriv_user', sa.Column('commons_eula_accepted_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ithriv_user', 'commons_eula_accepted_date')
    op.drop_column('ithriv_user', 'commons_eula_accepted')
    # ### end Alembic commands ###