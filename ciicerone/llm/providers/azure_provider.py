"""Azure OpenAI provider implementation for Ciicerone."""

import logging
from typing import Dict, Any

from ..base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI LLM provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Azure OpenAI provider.

        Args:
            config: Configuration dictionary with Azure OpenAI settings
        """
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.endpoint = config.get('endpoint', 'https://api.cognitive.microsoft.com')
        self.model = config.get('model', 'gpt-4o-mini')
        self.api_version = config.get('api_version', '2024-02-15-preview')
        self._client = None

        if not self.api_key:
            raise ValueError("Azure OpenAI API key is required")
        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint is required")

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a response from Azure OpenAI."""
        raise NotImplementedError(
            "Azure OpenAI provider requires openai>=1.0 with Azure endpoint"
        )

    async def is_available(self) -> bool:
        """Check if Azure OpenAI is available."""
        return bool(self.api_key and self.endpoint)
