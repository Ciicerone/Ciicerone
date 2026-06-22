"""REST API for Ciicerone.

Provides FastAPI-based REST endpoints for threat simulation,
scenario management, and system integration.
"""

from ciicerone.api.main import app

__all__ = [
    "app",
]
