"""Core exception classes for Ciicerone."""

from typing import Optional


class CiiceroneError(Exception):
    """Base exception for all Ciicerone errors."""
    DEFAULT_CODE = "CIICERONE_ERROR"

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.DEFAULT_CODE


class SimulationError(CiiceroneError):
    """Error during threat simulation execution."""
    DEFAULT_CODE = "SIM_ERROR"

    def __init__(self, message: str, scenario_id: Optional[str] = None, stage_type: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code or self.DEFAULT_CODE)
        self.scenario_id = scenario_id
        self.stage_type = stage_type


class ConfigurationError(CiiceroneError):
    """Error in configuration loading or validation."""
    DEFAULT_CODE = "CONFIG_ERROR"

    def __init__(self, message: str, config_path: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code or self.DEFAULT_CODE)
        self.config_path = config_path


class ValidationError(CiiceroneError):
    """Error in data validation."""
    DEFAULT_CODE = "VALIDATION_ERROR"

    def __init__(self, message: str, field_name: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code or self.DEFAULT_CODE)
        self.field_name = field_name


class LLMProviderError(CiiceroneError):
    """Error with LLM provider operations."""
    DEFAULT_CODE = "LLM_ERROR"

    def __init__(self, message: str, provider_name: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code or self.DEFAULT_CODE)
        self.provider_name = provider_name


class DeploymentError(CiiceroneError):
    """Error during deployment operations."""
    DEFAULT_CODE = "DEPLOY_ERROR"

    def __init__(self, message: str, deployment_id: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code or self.DEFAULT_CODE)
        self.deployment_id = deployment_id


class AuthenticationError(CiiceroneError):
    """Error during authentication with external platforms."""
    DEFAULT_CODE = "AUTH_ERROR"

    def __init__(self, message: str, platform: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code or self.DEFAULT_CODE)
        self.platform = platform
