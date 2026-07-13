"""LLM-related exceptions."""


class LLMError(Exception):
    """Base LLM error."""
    pass


class ProviderError(LLMError):
    """Provider error."""
    pass


class RateLimitError(LLMError):
    """Rate limit error."""
    pass


class CostLimitError(LLMError):
    """Cost limit error."""
    pass


# Backward compatibility — deprecated, use PermissionError instead
class AirGapViolationError(PermissionError):
    """Deprecated: raised when air-gap mode blocks external operations.

    Use PermissionError directly in new code.
    Kept for backward compatibility with PR #211 tests and fork branches.
    """
    pass
