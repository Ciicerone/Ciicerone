"""SQLAlchemy ORM foundation for Ciicerone.

This module provides the declarative base that all ORM models inherit from,
plus the async engine factory for creating SQLAlchemy async engines with
connection pooling.

All domain ORM models (red team, blue team, simulation, intelligence, quantum,
audit) should inherit from :class:`Base` defined here.

Owner: Ajibola Shokunbi (@jiboo2022) — Core Software Lead
Phase 1 of the persistence layer fix (see docs/plans/persistence-layer-maintainer-assignment.md).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from sqlalchemy import event as sa_event
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declarative_base

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for all Ciicerone ORM models.

    All domain models should inherit from this class::

        from ciicerone.db.base import Base

        class SimulationResultRecord(Base):
            __tablename__ = "simulation_results"
            ...
    """

    pass


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------

# Default connection-pool parameters.  These can be overridden per-engine
# via the ``DatabaseConfig`` dataclass in :mod:`ciicerone.db.session` or
# via environment variables (see ``_pool_kwargs_from_env``).

_DEFAULT_POOL_SIZE = 10
_DEFAULT_MAX_OVERFLOW = 20
_DEFAULT_POOL_TIMEOUT = 30  # seconds
_DEFAULT_POOL_RECYCLE = 3600  # 1 hour — recycle connections before PG kills them


def _pool_kwargs_from_env() -> dict[str, Any]:
    """Read pool configuration from environment variables.

    Recognised variables:
        DB_POOL_SIZE
        DB_MAX_OVERFLOW
        DB_POOL_TIMEOUT
        DB_POOL_RECYCLE
    """
    def _int(name: str, default: int) -> int:
        raw = os.getenv(name)
        try:
            return int(raw) if raw is not None else default
        except (TypeError, ValueError):
            logger.warning("Invalid int for %s=%r, using default %d", name, raw, default)
            return default

    return {
        "pool_size": _int("DB_POOL_SIZE", _DEFAULT_POOL_SIZE),
        "max_overflow": _int("DB_MAX_OVERFLOW", _DEFAULT_MAX_OVERFLOW),
        "pool_timeout": _int("DB_POOL_TIMEOUT", _DEFAULT_POOL_TIMEOUT),
        "pool_recycle": _int("DB_POOL_RECYCLE", _DEFAULT_POOL_RECYCLE),
    }


def _resolve_url(database_url: Optional[str] = None) -> str:
    """Resolve the database URL from argument, env, or default.

    Order of precedence:
        1. Explicit ``database_url`` argument
        2. ``DATABASE_URL`` environment variable
        3. ``postgresql://localhost/ciicerone`` (development default)

    The URL is normalised to the ``postgresql+asyncpg`` dialect so that
    SQLAlchemy's async engine can use it directly.
    """
    url = database_url or os.getenv("DATABASE_URL", "postgresql://localhost/ciicerone")

    # Normalise to asyncpg driver if a plain postgresql:// URL is given
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def create_engine(
    database_url: Optional[str] = None,
    *,
    echo: bool = False,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    pool_timeout: Optional[int] = None,
    pool_recycle: Optional[int] = None,
    **extra: Any,
) -> AsyncEngine:
    """Create an async SQLAlchemy engine with connection pooling.

    Pool parameters default to environment variables or sensible built-in
    defaults (see :func:`_pool_kwargs_from_env`).

    Args:
        database_url: PostgreSQL URL.  Falls back to ``DATABASE_URL`` env
            var, then to ``postgresql://localhost/ciicerone``.
        echo: Echo all SQL to the logger (debugging only).
        pool_size: Override connection pool size.
        max_overflow: Override max overflow connections.
        pool_timeout: Override pool acquire timeout (seconds).
        pool_recycle: Override connection recycle age (seconds).
        **extra: Additional keyword arguments forwarded to
            :func:`sqlalchemy.ext.asyncio.create_async_engine`.

    Returns:
        An :class:`AsyncEngine` ready for use with
        :func:`ciicerone.db.session.create_session_factory`.
    """
    url = _resolve_url(database_url)

    env_kwargs = _pool_kwargs_from_env()
    pool_kwargs: dict[str, Any] = {
        "pool_size": pool_size if pool_size is not None else env_kwargs["pool_size"],
        "max_overflow": max_overflow if max_overflow is not None else env_kwargs["max_overflow"],
        "pool_timeout": pool_timeout if pool_timeout is not None else env_kwargs["pool_timeout"],
        "pool_recycle": pool_recycle if pool_recycle is not None else env_kwargs["pool_recycle"],
    }

    # asyncpg does not support the default QueuePool's "pre-ping" check
    # via SQLAlchemy in the same way psycopg2 does, but pool_pre_ping is
    # still safe and recommended for long-lived connections.
    pool_kwargs["pool_pre_ping"] = extra.pop("pool_pre_ping", True)

    logger.info(
        "Creating async engine for %s (pool_size=%d, max_overflow=%d)",
        _safe_url_for_log(url),
        pool_kwargs["pool_size"],
        pool_kwargs["max_overflow"],
    )

    engine = create_async_engine(
        url,
        echo=echo,
        **pool_kwargs,
        **extra,
    )

    # Optional: log connection checkout/checkin events at debug level
    if logger.isEnabledFor(logging.DEBUG):
        @sa_event.listens_for(engine.sync_engine, "connect")
        def _on_connect(dbapi_conn, conn_record):  # type: ignore[misc]
            logger.debug("New DB connection opened")

        @sa_event.listens_for(engine.sync_engine, "checkout")
        def _on_checkout(dbapi_conn, conn_record, conn_proxy):  # type: ignore[misc]
            logger.debug("DB connection checked out from pool")

    return engine


def _safe_url_for_log(url: str) -> str:
    """Strip credentials from a database URL for safe logging."""
    try:
        parsed = URL.create_drivername("postgresql+asyncpg")
        # Re-parse through SQLAlchemy to mask password
        from sqlalchemy.engine import make_url
        safe = make_url(url)
        if safe.password:
            safe = safe.set(password="***")
        return str(safe)
    except Exception:
        # If URL parsing fails, just return the URL without the credentials portion
        if "@" in url:
            scheme, rest = url.split("://", 1)
            creds, host_part = rest.split("@", 1)
            return f"{scheme}://***@{host_part}"
        return url


# Module-level singleton engine (lazy-initialised on first access)
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Return the module-level singleton async engine.

    Creates it on first call using environment configuration.
    """
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Return the module-level singleton session factory.

    Creates it on first call, bound to :func:`get_engine`.
    """
    global _session_factory
    if _session_factory is None:
        from ciicerone.db.session import create_session_factory
        _session_factory = create_session_factory(get_engine())
    return _session_factory


async def dispose_engine() -> None:
    """Dispose the singleton engine and session factory.

    Call this during application shutdown to cleanly close all
    pooled connections.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("Disposed async engine and closed connection pool")
    _engine = None
    _session_factory = None
