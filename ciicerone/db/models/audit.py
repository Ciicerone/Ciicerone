"""Audit ORM models for tamper-evident compliance logging.

Maps the ``audit.audit_events`` table used by :class:`DatabaseAuditSink`.
Each record includes a SHA-256 hash chain linking it to the previous event
for the same aggregate, plus MITRE technique and compliance framework
metadata required for bank-pilot reporting.

Owner: Jeremiah Okino (@okino007) — Compliance Lead
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ciicerone.db.base import Base


class AuditEventRecord(Base):
    """ORM record for an audit event in the hash-chained audit trail.

    Attributes:
        id: Primary key UUID.
        aggregate_id: Logical aggregate/scenario identifier for the chain.
        event_type: Hierarchical event identifier, e.g. ``simulation.stage.started``.
        timestamp: UTC time the event occurred.
        actor: JSONB describing who/what performed the action.
        target: JSONB describing the resource acted upon.
        category: Audit category (security, compliance, auth, etc.).
        severity: Severity level (INFO, WARNING, ERROR, etc.).
        context: JSONB additional event context.
        tenant_id: Tenant scope for multi-tenant isolation.
        mitre_techniques: JSONB list of MITRE ATT&CK technique IDs.
        compliance_frameworks: JSONB list of compliance frameworks (PCI-DSS, SOC2, etc.).
        prev_hash: SHA-256 hash of the previous event in the aggregate chain.
        event_hash: SHA-256 hash of this event's data + prev_hash.
        created_at: UTC insertion time.
    """

    __tablename__ = "audit_events"
    __table_args__ = {"schema": "audit"}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    actor: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    target: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mitre_techniques: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    compliance_frameworks: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    prev_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
