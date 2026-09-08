from unittest.mock import AsyncMock, Mock

import pytest

from ciicerone.llm.models import (
    ContentType,
    LLMModel,
    LLMProvider,
    LLMProviderConfig,
    LLMRequest,
)
from ciicerone.llm.providers_new import AtlasCloudProvider, LLMProviderManager


def atlas_config() -> LLMProviderConfig:
    return LLMProviderConfig(
        provider=LLMProvider.ATLASCLOUD,
        api_key="test-key",
        default_model=LLMModel.ATLAS_GPT_5_6_LUNA,
    )


def atlas_request() -> LLMRequest:
    return LLMRequest(
        provider=LLMProvider.ATLASCLOUD,
        model=LLMModel.ATLAS_GPT_5_6_LUNA,
        content_type=ContentType.CHAT_MESSAGE,
        user_prompt="Return a short test response.",
    )


def test_manager_registers_atlascloud_provider():
    manager = LLMProviderManager()
    manager.add_provider(atlas_config())

    assert isinstance(manager.get_provider(LLMProvider.ATLASCLOUD), AtlasCloudProvider)
    assert manager.default_provider == LLMProvider.ATLASCLOUD
    assert manager.get_supported_models(LLMProvider.ATLASCLOUD) == [
        LLMModel.ATLAS_GPT_5_6_LUNA
    ]


@pytest.mark.asyncio
async def test_atlascloud_uses_fixed_endpoint_and_does_not_retry_generation():
    config = atlas_config()
    provider = AtlasCloudProvider(config)
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 1, "total_tokens": 5},
    }
    client = Mock()
    client.post = AsyncMock(return_value=response)
    provider._client = client

    result = await provider.generate_with_retry(atlas_request())

    assert result.success
    assert result.content == "ok"
    assert provider.config.max_retries == 0
    assert config.max_retries > 0
    client.post.assert_awaited_once()
    url = client.post.await_args.args[0]
    assert url == "https://api.atlascloud.ai/v1/chat/completions"
    assert client.post.await_args.kwargs["json"]["model"] == "openai/gpt-5.6-luna"
    assert client.post.await_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
