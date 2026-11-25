"""Add worker ownership and lease fields to intelligence jobs."""

from alembic import op
import sqlalchemy as sa

revision = "20261116_01"
down_revision = None
branch_labels = None
depends_on = None

TABLE = "intelligence_jobs"
TOKEN_INDEX = "ix_intelligence_jobs_worker_token"
LEASE_INDEX = "ix_intelligence_jobs_lease_expires_at"


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if not inspector.has_table(TABLE):
        raise RuntimeError(
            "intelligence_jobs does not exist. Run the existing application "
            "schema bootstrap before applying this migration."
        )

    columns = {column["name"] for column in inspector.get_columns(TABLE)}

    if "worker_token" not in columns:
        op.add_column(
            TABLE,
            sa.Column("worker_token", sa.String(length=36), nullable=True),
        )

    if "lease_expires_at" not in columns:
        op.add_column(
            TABLE,
            sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        )

    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes(TABLE)}

    if TOKEN_INDEX not in indexes:
        op.create_index(TOKEN_INDEX, TABLE, ["worker_token"], unique=True)

    if LEASE_INDEX not in indexes:
        op.create_index(LEASE_INDEX, TABLE, ["lease_expires_at"], unique=False)


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if not inspector.has_table(TABLE):
        return

    indexes = {index["name"] for index in inspector.get_indexes(TABLE)}

    if LEASE_INDEX in indexes:
        op.drop_index(LEASE_INDEX, table_name=TABLE)

    if TOKEN_INDEX in indexes:
        op.drop_index(TOKEN_INDEX, table_name=TABLE)

    columns = {column["name"] for column in inspector.get_columns(TABLE)}

    if "lease_expires_at" in columns:
        op.drop_column(TABLE, "lease_expires_at")

    if "worker_token" in columns:
        op.drop_column(TABLE, "worker_token")
