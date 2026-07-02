"""Event Sourcing System for Ciicerone Audit Trail.

Single source of truth for event sourcing: domain events, event store
(PostgreSQL-backed with in-memory fallback), aggregate base class, and
repository pattern.

Provides immutable audit logging, compliance queries, and state
reconstruction via event replay.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, AsyncIterator
from uuid import UUID, uuid4
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')

try:
    import asyncpg
    from asyncpg import Pool, Connection
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    Pool = Any
    Connection = Any


class AggregateType(str, Enum):
    """Types of aggregates that emit events."""
    SIMULATION = "simulation"
    SCENARIO = "scenario"
    USER_ACTION = "user_action"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


@dataclass(frozen=True)  # Immutable by design
class Event:
    """Immutable event record representing a state change in the system.
    
    Events are the source of truth for all state changes. They are:
    - Immutable: Once written, never modified
    - Append-only: Only new events added, never deleted
    - Ordered: Sequence number provides global ordering
    - Complete: Contains all information to reconstruct state
    
    Attributes:
        event_id: Unique identifier for this event
        aggregate_id: ID of the aggregate this event belongs to
        aggregate_type: Type of aggregate (simulation, scenario, etc.)
        event_type: Specific event type (SimulationStarted, StageCompleted, etc.)
        event_data: Event payload with all relevant data
        metadata: Contextual information (user_id, correlation_id, etc.)
        sequence_number: Global event ordering number
        timestamp: When the event occurred (UTC)
        version: Aggregate version for optimistic concurrency control
    """
    event_id: UUID
    aggregate_id: UUID
    aggregate_type: AggregateType
    event_type: str
    event_data: Dict[str, Any]
    metadata: Dict[str, Any]
    sequence_number: int
    timestamp: datetime
    version: int

    def __post_init__(self):
        """Validate event data after creation."""
        if not self.event_type:
            raise ValueError("event_type cannot be empty")
        if self.version < 0:
            raise ValueError(f"version must be >= 0, got {self.version}")
        # Ensure timestamp is timezone-aware (UTC)
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, 'timestamp', self.timestamp.replace(tzinfo=timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            'event_id': str(self.event_id),
            'aggregate_id': str(self.aggregate_id),
            'aggregate_type': self.aggregate_type.value,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'metadata': self.metadata,
            'sequence_number': self.sequence_number,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_id=UUID(data['event_id']),
            aggregate_id=UUID(data['aggregate_id']),
            aggregate_type=AggregateType(data['aggregate_type']),
            event_type=data['event_type'],
            event_data=data['event_data'],
            metadata=data['metadata'],
            sequence_number=data['sequence_number'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            version=data['version']
        )


# ============================================================================
# Simulation Events
# ============================================================================

@dataclass(frozen=True)
class SimulationStarted(Event):
    """Event emitted when a simulation begins execution."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        scenario_id: UUID,
        max_stages: int,
        initiated_by: str,
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create SimulationStarted event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="SimulationStarted",
            event_data={
                "scenario_id": str(scenario_id),
                "max_stages": max_stages,
                "initiated_by": initiated_by
            },
            metadata={
                "command": "execute_simulation",
                "initiated_by": initiated_by
            },
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


@dataclass(frozen=True)
class StageStarted(Event):
    """Event emitted when a simulation stage begins."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        stage_number: int,
        stage_type: str,
        stage_description: str,
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create StageStarted event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="StageStarted",
            event_data={
                "stage_number": stage_number,
                "stage_type": stage_type,
                "description": stage_description
            },
            metadata={},
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


@dataclass(frozen=True)
class StageCompleted(Event):
    """Event emitted when a simulation stage completes successfully."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        stage_number: int,
        stage_id: str,
        content_length: int,
        duration_ms: float,
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create StageCompleted event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="StageCompleted",
            event_data={
                "stage_number": stage_number,
                "stage_id": stage_id,
                "content_length": content_length,
                "duration_ms": duration_ms,
                "success": True
            },
            metadata={},
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


@dataclass(frozen=True)
class StageFailed(Event):
    """Event emitted when a simulation stage fails."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        stage_number: int,
        error_message: str,
        error_type: str,
        retry_count: int,
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create StageFailed event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="StageFailed",
            event_data={
                "stage_number": stage_number,
                "error_message": error_message,
                "error_type": error_type,
                "retry_count": retry_count,
                "success": False
            },
            metadata={
                "severity": "warning"
            },
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


@dataclass(frozen=True)
class SimulationCompleted(Event):
    """Event emitted when a simulation completes (successfully or with partial success)."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        total_stages: int,
        successful_stages: int,
        success_rate: float,
        duration_ms: float,
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create SimulationCompleted event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="SimulationCompleted",
            event_data={
                "total_stages": total_stages,
                "successful_stages": successful_stages,
                "success_rate": success_rate,
                "duration_ms": duration_ms
            },
            metadata={
                "final_state": "completed"
            },
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


@dataclass(frozen=True)
class SimulationFailed(Event):
    """Event emitted when a simulation fails completely."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        error_message: str,
        failed_at_stage: Optional[int],
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create SimulationFailed event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="SimulationFailed",
            event_data={
                "error_message": error_message,
                "failed_at_stage": failed_at_stage
            },
            metadata={
                "severity": "error",
                "final_state": "failed"
            },
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


@dataclass(frozen=True)
class SimulationCancelled(Event):
    """Event emitted when a simulation is cancelled by user."""
    
    @classmethod
    def create(
        cls,
        aggregate_id: UUID,
        cancelled_by: str,
        reason: str,
        version: int,
        sequence_number: int
    ) -> Event:
        """Factory method to create SimulationCancelled event."""
        return Event(
            event_id=uuid4(),
            aggregate_id=aggregate_id,
            aggregate_type=AggregateType.SIMULATION,
            event_type="SimulationCancelled",
            event_data={
                "cancelled_by": cancelled_by,
                "reason": reason
            },
            metadata={
                "final_state": "cancelled"
            },
            sequence_number=sequence_number,
            timestamp=datetime.now(timezone.utc),
            version=version
        )


# ============================================================================
# Event Store Exceptions
# ============================================================================

class EventStoreError(Exception):
    """Base exception for event store errors."""
    pass


class ConcurrencyError(EventStoreError):
    """Raised when optimistic concurrency check fails."""
    def __init__(self, aggregate_id: UUID, expected_version: int, actual_version: int):
        self.aggregate_id = aggregate_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Concurrency conflict for aggregate {aggregate_id}: "
            f"expected version {expected_version}, got {actual_version}"
        )


class EventNotFoundError(EventStoreError):
    """Raised when requested events don't exist."""
    pass


# ============================================================================
# Database Schema SQL
# ============================================================================

EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit.events (
    event_id UUID PRIMARY KEY,
    sequence_number BIGSERIAL UNIQUE NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_aggregate_version UNIQUE (aggregate_id, version)
);

CREATE INDEX IF NOT EXISTS idx_events_aggregate_id ON audit.events(aggregate_id);
CREATE INDEX IF NOT EXISTS idx_events_aggregate_type ON audit.events(aggregate_type);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON audit.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON audit.events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_aggregate_version ON audit.events(aggregate_id, version);
CREATE INDEX IF NOT EXISTS idx_events_event_data ON audit.events USING GIN (event_data);
CREATE INDEX IF NOT EXISTS idx_events_metadata ON audit.events USING GIN (metadata);
"""

SNAPSHOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit.snapshots (
    aggregate_id UUID PRIMARY KEY,
    aggregate_type VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""


# ============================================================================
# Event Store — PostgreSQL implementation with in-memory fallback
# ============================================================================

class EventStore:
    """PostgreSQL-backed event store for immutable audit trail.

    Provides:
    - Append-only event log
    - Optimistic concurrency control
    - Event replay for aggregate reconstruction
    - Temporal queries (events between timestamps)
    - Compliance-ready audit trail

    When no database connection is available, falls back to in-memory
    storage (useful for testing and development).
    """

    def __init__(self, pool: Any = None):
        """Initialize event store.

        Args:
            pool: asyncpg connection pool. If None, falls back to in-memory mode.
        """
        self._pool = pool
        self._initialized = False
        self._sequence_lock = asyncio.Lock()
        self._current_sequence = 0
        self._in_memory_events: Dict[UUID, List[Event]] = {}
        self._in_memory_sequences: Dict[UUID, int] = {}
        logger.info("EventStore initialized (%s mode)", "PostgreSQL" if pool else "in-memory")

    @classmethod
    async def create(
        cls,
        database_url: Optional[str] = None,
        min_connections: int = 2,
        max_connections: int = 10,
        **pool_kwargs
    ) -> 'EventStore':
        """Create a new EventStore with a PostgreSQL connection pool.

        Args:
            database_url: PostgreSQL connection string (or from DATABASE_URL env)
            min_connections: Minimum pool connections
            max_connections: Maximum pool connections
            **pool_kwargs: Additional arguments for asyncpg.create_pool

        Returns:
            Initialized EventStore
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for PostgreSQL-backed EventStore. "
                "Install with: pip install asyncpg"
            )

        url = database_url or os.getenv("DATABASE_URL")
        if not url:
            raise ValueError(
                "Database URL required. Provide database_url or set DATABASE_URL env var"
            )

        logger.info(f"Creating connection pool (min={min_connections}, max={max_connections})")

        pool = await asyncpg.create_pool(
            url,
            min_size=min_connections,
            max_size=max_connections,
            **pool_kwargs
        )

        store = cls(pool)
        await store.initialize_schema()
        return store

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Connection pool closed")

    async def __aenter__(self) -> 'EventStore':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @asynccontextmanager
    async def _acquire(self) -> AsyncIterator[Any]:
        """Acquire a connection from the pool."""
        async with self._pool.acquire() as conn:
            yield conn

    async def initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        if self._initialized or self._pool is None:
            return

        async with self._acquire() as conn:
            await conn.execute("CREATE SCHEMA IF NOT EXISTS audit")
            await conn.execute(EVENTS_TABLE_SQL)
            await conn.execute(SNAPSHOTS_TABLE_SQL)
            self._initialized = True
            logger.info("Event store schema initialized")

    async def _get_next_sequence(self) -> int:
        """Get next global sequence number (thread-safe, in-memory only)."""
        async with self._sequence_lock:
            self._current_sequence += 1
            return self._current_sequence

    async def append(self, event: Event) -> int:
        """Append event to the store with optimistic concurrency control.

        Args:
            event: Event to append

        Returns:
            The assigned sequence number

        Raises:
            ConcurrencyError: If version conflict detected
            EventStoreError: If write fails
        """
        if self._pool is None:
            return await self._append_in_memory(event)

        async with self._acquire() as conn:
            async with conn.transaction():
                current_version = await self._get_aggregate_version_pg(conn, event.aggregate_id)
                expected_version = event.version - 1
                if current_version != expected_version:
                    raise ConcurrencyError(
                        event.aggregate_id, expected_version, current_version
                    )

                sequence = await conn.fetchval(
                    """
                    INSERT INTO audit.events (
                        event_id, aggregate_id, aggregate_type, version,
                        event_type, event_data, metadata, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING sequence_number
                    """,
                    event.event_id,
                    event.aggregate_id,
                    event.aggregate_type.value,
                    event.version,
                    event.event_type,
                    json.dumps(event.event_data),
                    json.dumps(event.metadata),
                    event.timestamp
                )

                logger.debug(
                    f"Event appended: {event.event_type} for "
                    f"{event.aggregate_type}:{event.aggregate_id} "
                    f"(v{event.version}, seq={sequence})"
                )
                return sequence

    async def _append_in_memory(self, event: Event) -> int:
        """Append event to in-memory store (for testing/development)."""
        aggregate_events = self._in_memory_events.setdefault(event.aggregate_id, [])
        current_version = self._in_memory_sequences.get(event.aggregate_id, 0)
        expected_version = event.version - 1
        if current_version != expected_version:
            raise ConcurrencyError(
                event.aggregate_id, expected_version, current_version
            )

        sequence = await self._get_next_sequence()
        stored_event = Event(
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            event_type=event.event_type,
            event_data=event.event_data,
            metadata=event.metadata,
            sequence_number=sequence,
            timestamp=event.timestamp,
            version=event.version
        )
        aggregate_events.append(stored_event)
        self._in_memory_sequences[event.aggregate_id] = event.version
        logger.debug(
            f"Event appended (in-memory): {event.event_type} for "
            f"{event.aggregate_type}:{event.aggregate_id} "
            f"(v{event.version}, seq={sequence})"
        )
        return sequence

    async def append_batch(self, events: List[Event]) -> List[int]:
        """Append multiple events atomically.

        All events must be for the same aggregate and sequential versions.

        Args:
            events: List of events to append

        Returns:
            List of assigned sequence numbers

        Raises:
            ConcurrencyError: If version conflict detected
            EventStoreError: If write fails
        """
        if not events:
            return []

        aggregate_id = events[0].aggregate_id
        if not all(e.aggregate_id == aggregate_id for e in events):
            raise EventStoreError("All events in batch must be for same aggregate")

        for i, event in enumerate(events):
            if i > 0 and event.version != events[i - 1].version + 1:
                raise EventStoreError("Event versions must be sequential")

        if self._pool is None:
            sequences = []
            for event in events:
                seq = await self._append_in_memory(event)
                sequences.append(seq)
            return sequences

        async with self._acquire() as conn:
            async with conn.transaction():
                current_version = await self._get_aggregate_version_pg(conn, aggregate_id)
                expected_version = events[0].version - 1
                if current_version != expected_version:
                    raise ConcurrencyError(aggregate_id, expected_version, current_version)

                sequences = []
                for event in events:
                    sequence = await conn.fetchval(
                        """
                        INSERT INTO audit.events (
                            event_id, aggregate_id, aggregate_type, version,
                            event_type, event_data, metadata, timestamp
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING sequence_number
                        """,
                        event.event_id,
                        event.aggregate_id,
                        event.aggregate_type.value,
                        event.version,
                        event.event_type,
                        json.dumps(event.event_data),
                        json.dumps(event.metadata),
                        event.timestamp
                    )
                    sequences.append(sequence)

                logger.debug(f"Batch of {len(events)} events appended for {aggregate_id}")
                return sequences

    async def get_events(
        self,
        aggregate_id: UUID,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """Get all events for an aggregate within version range.

        Args:
            aggregate_id: ID of the aggregate
            from_version: Start version (inclusive, default 0)
            to_version: End version (inclusive), None for latest

        Returns:
            List of events ordered by version
        """
        if self._pool is None:
            events = self._in_memory_events.get(aggregate_id, [])
            filtered = [e for e in events if e.version >= from_version]
            if to_version is not None:
                filtered = [e for e in filtered if e.version <= to_version]
            return filtered

        async with self._acquire() as conn:
            if to_version is not None:
                rows = await conn.fetch(
                    """
                    SELECT event_id, aggregate_id, aggregate_type, version,
                           event_type, event_data, metadata, sequence_number, timestamp
                    FROM audit.events
                    WHERE aggregate_id = $1 AND version >= $2 AND version <= $3
                    ORDER BY version ASC
                    """,
                    aggregate_id, from_version, to_version
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT event_id, aggregate_id, aggregate_type, version,
                           event_type, event_data, metadata, sequence_number, timestamp
                    FROM audit.events
                    WHERE aggregate_id = $1 AND version >= $2
                    ORDER BY version ASC
                    """,
                    aggregate_id, from_version
                )
            return [self._row_to_event(row) for row in rows]

    async def get_events_by_type(
        self,
        event_type: str,
        from_timestamp: datetime,
        to_timestamp: datetime,
        limit: int = 1000
    ) -> List[Event]:
        """Query events by type within time range (for compliance queries).

        Args:
            event_type: Event type to filter
            from_timestamp: Start time (inclusive)
            to_timestamp: End time (inclusive)
            limit: Maximum events to return

        Returns:
            List of events ordered by timestamp
        """
        if self._pool is None:
            results = []
            for events in self._in_memory_events.values():
                for e in events:
                    if e.event_type == event_type and from_timestamp <= e.timestamp <= to_timestamp:
                        results.append(e)
            results.sort(key=lambda e: e.timestamp)
            return results[:limit]

        async with self._acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, aggregate_id, aggregate_type, version,
                       event_type, event_data, metadata, sequence_number, timestamp
                FROM audit.events
                WHERE event_type = $1 AND timestamp >= $2 AND timestamp <= $3
                ORDER BY timestamp ASC
                LIMIT $4
                """,
                event_type, from_timestamp, to_timestamp, limit
            )
            return [self._row_to_event(row) for row in rows]

    async def get_events_by_aggregate_type(
        self,
        aggregate_type: AggregateType,
        from_timestamp: datetime,
        to_timestamp: datetime,
        limit: int = 1000
    ) -> List[Event]:
        """Query events by aggregate type within time range.

        Args:
            aggregate_type: Type of aggregate
            from_timestamp: Start time (inclusive)
            to_timestamp: End time (inclusive)
            limit: Maximum events to return

        Returns:
            List of events ordered by timestamp
        """
        if self._pool is None:
            results = []
            for events in self._in_memory_events.values():
                for e in events:
                    if e.aggregate_type == aggregate_type and from_timestamp <= e.timestamp <= to_timestamp:
                        results.append(e)
            results.sort(key=lambda e: e.timestamp)
            return results[:limit]

        async with self._acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, aggregate_id, aggregate_type, version,
                       event_type, event_data, metadata, sequence_number, timestamp
                FROM audit.events
                WHERE aggregate_type = $1 AND timestamp >= $2 AND timestamp <= $3
                ORDER BY timestamp ASC
                LIMIT $4
                """,
                aggregate_type.value, from_timestamp, to_timestamp, limit
            )
            return [self._row_to_event(row) for row in rows]

    async def get_aggregate_version(self, aggregate_id: UUID) -> int:
        """Get current version of an aggregate.

        Args:
            aggregate_id: ID of aggregate

        Returns:
            Current version number (0 if aggregate doesn't exist)
        """
        if self._pool is None:
            return self._in_memory_sequences.get(aggregate_id, 0)

        async with self._acquire() as conn:
            return await self._get_aggregate_version_pg(conn, aggregate_id)

    async def _get_aggregate_version_pg(self, conn: Any, aggregate_id: UUID) -> int:
        """Internal version lookup (within existing connection)."""
        result = await conn.fetchval(
            """
            SELECT COALESCE(MAX(version), 0)
            FROM audit.events
            WHERE aggregate_id = $1
            """,
            aggregate_id
        )
        return result or 0

    async def aggregate_exists(self, aggregate_id: UUID) -> bool:
        """Check if an aggregate has any events."""
        if self._pool is None:
            return aggregate_id in self._in_memory_events

        async with self._acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM audit.events WHERE aggregate_id = $1)",
                aggregate_id
            )
            return result

    async def replay_events(
        self,
        aggregate_id: UUID,
        handler: callable
    ) -> int:
        """Replay all events for an aggregate through a handler.

        Args:
            aggregate_id: ID of aggregate to replay
            handler: Async or sync function called with each event

        Returns:
            Number of events replayed
        """
        events = await self.get_events(aggregate_id)
        for event in events:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        logger.debug(f"Replayed {len(events)} events for aggregate {aggregate_id}")
        return len(events)

    async def replay_aggregate(self, aggregate_id: UUID) -> Optional[Any]:
        """Rebuild aggregate state from all its events (event replay).

        Args:
            aggregate_id: ID of aggregate to rebuild

        Returns:
            Reconstructed aggregate state or None if no events
        """
        events = await self.get_events(aggregate_id)
        if not events:
            return None
        logger.debug(f"Replaying {len(events)} events for aggregate {aggregate_id}")
        return events

    async def get_all_aggregate_ids(
        self,
        aggregate_type: Optional[AggregateType] = None
    ) -> List[UUID]:
        """Get all unique aggregate IDs, optionally filtered by type.

        Args:
            aggregate_type: Optional filter by aggregate type

        Returns:
            List of unique aggregate IDs
        """
        if self._pool is None:
            ids = set()
            for aid, events in self._in_memory_events.items():
                if aggregate_type is None or events[0].aggregate_type == aggregate_type:
                    ids.add(aid)
            return list(ids)

        async with self._acquire() as conn:
            if aggregate_type:
                rows = await conn.fetch(
                    "SELECT DISTINCT aggregate_id FROM audit.events WHERE aggregate_type = $1",
                    aggregate_type.value
                )
            else:
                rows = await conn.fetch("SELECT DISTINCT aggregate_id FROM audit.events")
            return [row['aggregate_id'] for row in rows]

    async def get_event_count(
        self,
        aggregate_id: Optional[UUID] = None,
        event_type: Optional[str] = None
    ) -> int:
        """Get count of events with optional filters."""
        if self._pool is None:
            count = 0
            for events in self._in_memory_events.values():
                for e in events:
                    if aggregate_id and e.aggregate_id != aggregate_id:
                        continue
                    if event_type and e.event_type != event_type:
                        continue
                    count += 1
            return count

        async with self._acquire() as conn:
            if aggregate_id and event_type:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM audit.events WHERE aggregate_id = $1 AND event_type = $2",
                    aggregate_id, event_type
                )
            elif aggregate_id:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM audit.events WHERE aggregate_id = $1",
                    aggregate_id
                )
            elif event_type:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM audit.events WHERE event_type = $1",
                    event_type
                )
            else:
                return await conn.fetchval("SELECT COUNT(*) FROM audit.events")

    async def get_latest_sequence(self) -> int:
        """Get the latest global sequence number."""
        if self._pool is None:
            return self._current_sequence

        async with self._acquire() as conn:
            result = await conn.fetchval(
                "SELECT COALESCE(MAX(sequence_number), 0) FROM audit.events"
            )
            return result or 0

    def _row_to_event(self, row: Any) -> Event:
        """Convert database row to Event object."""
        return Event(
            event_id=row['event_id'],
            aggregate_id=row['aggregate_id'],
            aggregate_type=AggregateType(row['aggregate_type']),
            event_type=row['event_type'],
            event_data=json.loads(row['event_data']) if isinstance(row['event_data'], str) else row['event_data'],
            metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata'],
            sequence_number=row['sequence_number'],
            timestamp=row['timestamp'],
            version=row['version']
        )


# ============================================================================
# Retry Logic for Concurrency Conflicts
# ============================================================================

async def append_with_retry(
    store: EventStore,
    event_factory: callable,
    aggregate_id: UUID,
    max_retries: int = 3,
    retry_delay: float = 0.1
) -> Event:
    """Append an event with automatic retry on concurrency conflicts.

    Args:
        store: The event store
        event_factory: Function that creates the event given current version
        aggregate_id: ID of the aggregate
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries (seconds)

    Returns:
        The successfully appended event

    Raises:
        ConcurrencyError: If all retries exhausted
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            current_version = await store.get_aggregate_version(aggregate_id)
            event = event_factory(current_version + 1)
            await store.append(event)
            return event
        except ConcurrencyError as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    f"Concurrency conflict (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {retry_delay}s"
                )
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"All {max_retries + 1} attempts failed due to concurrency conflicts")
    raise last_error


# ============================================================================
# Event-Sourced Aggregate Base Class
# ============================================================================

class EventSourcedAggregate(Generic[T]):
    """Base class for event-sourced aggregates.
    
    Aggregates are domain entities that:
    - Emit events for state changes
    - Maintain internal version for concurrency control
    - Can be reconstructed from event history
    """

    def __init__(self, aggregate_id: UUID):
        self.aggregate_id = aggregate_id
        self.version = 0
        self._uncommitted_events: List[Event] = []

    def apply_event(self, event: Event) -> None:
        """Apply an event to this aggregate (update state)."""
        self.version = event.version
        # Subclasses override to update their specific state

    def get_uncommitted_events(self) -> List[Event]:
        """Get events that haven't been persisted yet."""
        return self._uncommitted_events.copy()

    def mark_events_committed(self) -> None:
        """Mark all uncommitted events as committed."""
        self._uncommitted_events.clear()

    def _raise_event(self, event: Event) -> None:
        """Raise a new event (add to uncommitted)."""
        self._uncommitted_events.append(event)
        self.apply_event(event)


# ============================================================================
# Repository Pattern for Event-Sourced Aggregates
# ============================================================================

class EventSourcedRepository(Generic[T]):
    """Repository for loading and saving event-sourced aggregates."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def get(self, aggregate_id: UUID) -> Optional[T]:
        """Load aggregate from event store."""
        return await self.event_store.replay_aggregate(aggregate_id)

    async def save(self, aggregate: EventSourcedAggregate) -> None:
        """Save aggregate by persisting uncommitted events."""
        for event in aggregate.get_uncommitted_events():
            await self.event_store.append(event)
        aggregate.mark_events_committed()
