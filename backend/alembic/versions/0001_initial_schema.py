"""Initial gateway schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admin_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_audit_logs_action"), "admin_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_admin_audit_logs_admin_id"), "admin_audit_logs", ["admin_id"], unique=False)

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("hashed_password", sa.String(length=512), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_users_username"), "admin_users", ["username"], unique=True)

    op.create_table(
        "gateway_clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.String(length=128), nullable=False),
        sa.Column("hashed_secret", sa.String(length=512), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("rate_limit", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gateway_clients_client_id"), "gateway_clients", ["client_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_gateway_clients_client_id"), table_name="gateway_clients")
    op.drop_table("gateway_clients")
    op.drop_index(op.f("ix_admin_users_username"), table_name="admin_users")
    op.drop_table("admin_users")
    op.drop_index(op.f("ix_admin_audit_logs_admin_id"), table_name="admin_audit_logs")
    op.drop_index(op.f("ix_admin_audit_logs_action"), table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
