"""empty message

Revision ID: 447a852550b6
Revises: c77b77950dde
Create Date: 2021-08-26 18:24:36.589538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '447a852550b6'
down_revision = 'c77b77950dde'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('taxrecords', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'taxrecords', 'standardtaxrecords', ['parent_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'taxrecords', type_='foreignkey')
    op.drop_column('taxrecords', 'parent_id')
    # ### end Alembic commands ###


# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.ddl.postgresql] Detected sequence named 'states_id_seq' as owned by integer column 'states(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'standardtaxrecords_id_seq' as owned by integer column 'standardtaxrecords(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'roles_id_seq' as owned by integer column 'roles(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'users_id_seq' as owned by integer column 'users(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'taxbill_id_seq' as owned by integer column 'taxbill(id)', assuming SERIAL and omitting
# INFO  [alembic.ddl.postgresql] Detected sequence named 'taxrecords_id_seq' as owned by integer column 'taxrecords(id)', assuming SERIAL and omitting
# INFO  [alembic.autogenerate.compare] Detected added column 'taxrecords.parent_id'
# INFO  [alembic.autogenerate.compare] Detected added foreign key (parent_id)(id) on table taxrecords
# Generating C:\Users\akshi\Desktop\flask assignment\migrations\versions\447a852550b6_.py ...  done