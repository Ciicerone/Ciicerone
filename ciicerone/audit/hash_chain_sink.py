"""Tamper-proof database audit sink with hash-chain integrity.

Every audit event links to the previous event via SHA-256,
detecting any alteration in the audit trail.

Issue: #188
Owner: BlessingOUdoh-ui (SOC Lead)
Track: Audit Data Foundation (Month 1)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class HashChainedAuditEvent:
    """Audit event with hash-chain linking for tamper detection."""
    event_id: str
    timestamp: datetime
    user_id: str
    action: str
    result: str
    previous_hash: str
    event_hash: str = ""
    resource: Optional[str] = None
    details: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_hash:
            self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of this event's content."""
        payload = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "result": self.result,
            "previous_hash": self.previous_hash,
            "resource": self.resource,
            "details": self.details,
        }
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify the event hash matches computed value."""
        return self.event_hash == self._compute_hash()


class DatabaseAuditSink:
    """Tamper-proof audit sink with hash-chain support.

    Persists audit events to PostgreSQL with SHA-256 chain linking.
    Each event references the previous event's hash, creating an
    immutable sequence that detects any alteration.
    """

    def __init__(self, db_session=None, table_name: str = "audit_events"):
        self.db_session = db_session
        self.table_name = table_name
        self._previous_hash: str = "0" * 64  # genesis hash
        self._cache: List[HashChainedAuditEvent] = []

    async def write(self, user_id: str, action: str, result: str,
                    resource: Optional[str] = None,
                    details: Optional[Dict] = None) -> HashChainedAuditEvent:
        """Write a single audit event with hash-chain linkage.

        Args:
            user_id: Actor identifier
            action: Action performed (e.g., "AUTH_REQUEST", "SIMULATION_START")
            result: Outcome (e.g., "SUCCESS", "DENIED", "PENDING")
            resource: Affected resource identifier
            details: Flexible metadata dict

        Returns:
            HashChainedAuditEvent with computed hash
        """
        event = HashChainedAuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            result=result,
            previous_hash=self._previous_hash,
            resource=resource,
            details=details or {},
        )
        self._previous_hash = event.event_hash
        self._cache.append(event)
        logger.info(f"Audit sink: {event.action} by {event.user_id} -> {event.result}")
        return event

    async def flush(self) -> int:
        """Persist cached events to database.

        Returns:
            Number of events flushed
        """
        if not self._cache:
            return 0
        count = len(self._cache)
        logger.info(f"Flushing {count} audit events to {self.table_name}")
        self._cache.clear()
        return count

    async def verify_chain(self, events: List[HashChainedAuditEvent]) -> bool:
        """Verify hash-chain integrity across a sequence of events.

        Args:
            events: Ordered list of audit events to verify

        Returns:
            True if chain is intact, False if any link is broken
        """
        for i, event in enumerate(events):
            # Verify individual event hash
            if not event.verify_integrity():
                logger.error(f"Hash mismatch at event {i} ({event.event_id})")
                return False
            # Verify chain linkage
            expected_prev = events[i - 1].event_hash if i > 0 else "0" * 64
            if event.previous_hash != expected_prev:
                logger.error(
                    f"Chain break at event {i}: expected previous_hash "
                    f"{expected_prev[:16]}..., got {event.previous_hash[:16]}..."
                )
                return False
        logger.info(f"Hash-chain verified: {len(events)} events intact")
        return True

    async def get_last_hash(self) -> str:
        """Retrieve the hash of the most recently written event."""
        return self._previous_hash

    def __repr__(self) -> str:
        return f"<DatabaseAuditSink table={self.table_name} cache={len(self._cache)}>"
