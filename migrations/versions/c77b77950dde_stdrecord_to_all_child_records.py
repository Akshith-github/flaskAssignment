"""stdrecord to all child records

Revision ID: c77b77950dde
Revises: d2f7e25ebec6
Create Date: 2021-08-26 18:17:57.609950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c77b77950dde'
down_revision = 'd2f7e25ebec6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('standardtaxrecords_activerecord_id_fkey', 'standardtaxrecords', type_='foreignkey')
    op.drop_column('standardtaxrecords', 'activerecord_id')
    op.add_column('taxrecords', sa.Column('standardtax_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'taxrecords', 'standardtaxrecords', ['standardtax_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'taxrecords', type_='foreignkey')
    op.drop_column('taxrecords', 'standardtax_id')
    op.add_column('standardtaxrecords', sa.Column('activerecord_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('standardtaxrecords_activerecord_id_fkey', 'standardtaxrecords', 'taxrecords', ['activerecord_id'], ['id'])
    # ### end Alembic commands ###


# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.ddl.postgresql] Detected sequence named 'states_id_seq' as owned by integer column 'states(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'users_id_seq' as owned by integer column 'users(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'taxrecords_id_seq' as owned by integer column 'taxrecords(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'taxbill_id_seq' as owned by integer column 'taxbill(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'standardtaxrecords_id_seq' as owned by integer column 'standardtaxrecords(id)', assuming SERIAL and omitting
# INFO  [alembic.autogenerate.compare] Detected removed foreign key (activerecord_id)(id) on table standardtaxrecords
# INFO  [alembic.autogenerate.compare] Detected removed column 'standardtaxrecords.activerecord_id'
# INFO  [alembic.autogenerate.compare] Detected added column 'taxrecords.standardtax_id'
# INFO  [alembic.autogenerate.compare] Detected added foreign key (standardtax_id)(id) on table taxrecords
# Generating C:\Users\akshi\Desktop\flask assignment\migrations\versions\c77b77950dde_stdrecord_to_all_child_records.py ...  done