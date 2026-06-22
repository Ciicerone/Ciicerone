"""Ciicerone: AI-Powered Threat Simulation Platform.

A production-grade cybersecurity threat simulation platform that leverages
Large Language Models (LLMs) to generate realistic, context-aware threat
scenarios for training, awareness, and red teaming activities.
"""

__version__ = "0.1.0"
__author__ = "Ciicerone Team"
__email__ = "ciicerone@hotmail.com"
__license__ = "MIT"

# Core imports for public API
from ciicerone.core.models import SimulationResult, ThreatScenario
from ciicerone.core.simulator import Simulator
from ciicerone.config.loader import ConfigurationLoader

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "SimulationResult",
    "ThreatScenario",
    "Simulator",
    "ConfigurationLoader",
]
