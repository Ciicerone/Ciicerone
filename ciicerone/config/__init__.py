"""Configuration management and validation.

Handles YAML configuration loading, schema validation,
and configuration object management.
"""

from ciicerone.config.models import (
    ThreatScenario,
    ThreatType,
    DeliveryVector,
    TargetProfile,
    SimulationParameters,
)
from ciicerone.config.loader import ConfigurationLoader, CiiceroneConfig, load_config
from ciicerone.config.validator import ConfigurationValidator
from ciicerone.config.exceptions import (
    ConfigurationError,
    ValidationError,
    SchemaError,
)
from ciicerone.config.validate_env import (
    validate_environment,
    print_environment_status,
    get_missing_vars,
)

__all__ = [
    "ThreatScenario",
    "ThreatType",
    "DeliveryVector",
    "TargetProfile",
    "SimulationParameters",
    "ConfigurationLoader",
    "CiiceroneConfig",
    "load_config",
    "ConfigurationValidator",
    "ConfigurationError",
    "ValidationError",
    "SchemaError",
    "validate_environment",
    "print_environment_status",
    "get_missing_vars",
]
