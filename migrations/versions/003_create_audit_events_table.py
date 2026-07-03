"""Create audit_events table for tamper-evident audit logging

Revision ID: 003_create_audit_events_table
Revises: 002_create_snapshots_table
Create Date: 2026-07-03

Author: Jeremiah Okino (@okino007)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_create_audit_events_table'
down_revision: Union[str, None] = '002_create_snapshots_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the audit_events table with hash-chain integrity fields."""

    # Create audit schema if not exists
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('aggregate_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('actor', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('target', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('context', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('mitre_techniques', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('compliance_frameworks', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('prev_hash', sa.String(128), nullable=False),
        sa.Column('event_hash', sa.String(128), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.current_timestamp()),
        schema='audit'
    )

    op.create_index(
        'idx_audit_events_aggregate_id',
        'audit_events',
        ['aggregate_id'],
        schema='audit'
    )
    op.create_index(
        'idx_audit_events_event_type',
        'audit_events',
        ['event_type'],
        schema='audit'
    )
    op.create_index(
        'idx_audit_events_category',
        'audit_events',
        ['category'],
        schema='audit'
    )
    op.create_index(
        'idx_audit_events_severity',
        'audit_events',
        ['severity'],
        schema='audit'
    )
    op.create_index(
        'idx_audit_events_tenant_id',
        'audit_events',
        ['tenant_id'],
        schema='audit'
    )
    op.create_index(
        'idx_audit_events_timestamp',
        'audit_events',
        [sa.text('timestamp DESC')],
        schema='audit'
    )
    op.create_index(
        'idx_audit_events_event_hash',
        'audit_events',
        ['event_hash'],
        schema='audit'
    )

    op.execute(
        "CREATE INDEX idx_audit_events_context ON audit.audit_events USING GIN (context)"
    )
    op.execute(
        "CREATE INDEX idx_audit_events_actor ON audit.audit_events USING GIN (actor)"
    )
    op.execute(
        "CREATE INDEX idx_audit_events_target ON audit.audit_events USING GIN (target)"
    )


def downgrade() -> None:
    """Drop the audit_events table."""
    op.drop_table('audit_events', schema='audit')
