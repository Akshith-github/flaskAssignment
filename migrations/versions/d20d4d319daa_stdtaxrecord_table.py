"""Stdtaxrecord table

Revision ID: d20d4d319daa
Revises: f57d74f2b215
Create Date: 2021-08-26 12:26:33.393714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd20d4d319daa'
down_revision = 'f57d74f2b215'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('standardtaxrecords',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('taxname', sa.String(length=10), nullable=True),
    sa.Column('state_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['state_id'], ['states.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_standardtaxrecords_taxname'), 'standardtaxrecords', ['taxname'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_standardtaxrecords_taxname'), table_name='standardtaxrecords')
    op.drop_table('standardtaxrecords')
    # ### end Alembic commands ###
