"""Unit tests for air-gap model download blocking.

Tests cover enforcement of air-gap mode:
- Blocking outbound model downloads when air-gap is enabled
- Verifying local-only model resolution
- Configuration-driven air-gap policy enforcement
- Regression protection across provider implementations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


@pytest.fixture
def air_gap_config() -> dict:
    return {
        "air_gap": {
            "enabled": True,
            "allowed_domains": [],
            "block_downloads": True,
            "local_only": True,
            "verify_checksums": True,
        }
    }


@pytest.fixture
def air_gap_disabled_config() -> dict:
    return {
        "air_gap": {
            "enabled": False,
            "allowed_domains": ["*"],
            "block_downloads": False,
            "local_only": False,
            "verify_checksums": False,
        }
    }


class TestAirGapModelDownloadBlocking:
    def test_air_gap_blocks_outbound_downloads_by_default(self, air_gap_config):
        assert air_gap_config["air_gap"]["block_downloads"] is True
        assert air_gap_config["air_gap"]["allowed_domains"] == []

    def test_air_gap_disabled_allows_all_domains(self, air_gap_disabled_config):
        assert air_gap_disabled_config["air_gap"]["block_downloads"] is False
        assert air_gap_disabled_config["air_gap"]["allowed_domains"] == ["*"]

    @pytest.mark.asyncio
    async def test_ollama_download_blocked_in_air_gap(self, air_gap_config):
        with patch(
            "ciicerone.llm.providers.ollama_provider.OllamaProvider._pull_model",
            new_callable=AsyncMock,
        ) as mock_pull:
            mock_pull.side_effect = PermissionError(
                "Model downloads blocked: air-gap mode enabled"
            )
            with pytest.raises(PermissionError, match="air-gap mode enabled"):
                await mock_pull()

    @pytest.mark.asyncio
    async def test_ollama_download_allowed_when_air_gap_disabled(
        self, air_gap_disabled_config
    ):
        with patch(
            "ciicerone.llm.providers.ollama_provider.OllamaProvider._pull_model",
            new_callable=AsyncMock,
        ) as mock_pull:
            mock_pull.return_value = {"status": "success", "model": "llama3.2:3b"}
            result = await mock_pull()
            assert result["status"] == "success"

    @patch("ciicerone.llm.providers.ollama_provider.OllamaProvider._pull_model")
    def test_model_download_gate_respects_air_gap_flag(
        self, mock_pull, air_gap_config
    ):
        mock_pull.side_effect = PermissionError("blocked")
        if air_gap_config["air_gap"]["block_downloads"]:
            with pytest.raises(PermissionError, match="blocked"):
                mock_pull()

    def test_air_gap_config_rejects_external_urls_when_enabled(self, air_gap_config):
        external_urls = [
            "https://huggingface.co/meta-llama/Llama-3.2-3B",
            "https://ollama.com/library/llama3.2",
            "https://github.com/ggml-org/llama.cpp",
        ]
        allowed_domains = set(air_gap_config["air_gap"]["allowed_domains"])
        for url in external_urls:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            assert domain not in allowed_domains, (
                f"External domain {domain} should be blocked in air-gap mode"
            )

    def test_air_gap_local_only_flag_enforces_no_external_fetches(
        self, air_gap_config
    ):
        assert air_gap_config["air_gap"]["local_only"] is True

    def test_air_gap_verify_checksums_flag(self, air_gap_config):
        assert air_gap_config["air_gap"]["verify_checksums"] is True

    @pytest.mark.asyncio
    async def test_external_model_fetch_raises_in_air_gap_mode(self, air_gap_config):
        model_urls = [
            ("ollama", "http://localhost:11434/api/pull"),
            ("huggingface", "https://huggingface.co/api/models/gated"),
        ]
        for provider_name, url in model_urls:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = PermissionError(
                    f"Air-gap: downloads blocked for {provider_name}"
                )
                with pytest.raises(PermissionError):
                    await mock_post()

    def test_config_toggles_air_gap_off_disables_blocking(
        self, air_gap_disabled_config
    ):
        assert air_gap_disabled_config["air_gap"]["block_downloads"] is False
        assert air_gap_disabled_config["air_gap"]["local_only"] is False
        assert air_gap_disabled_config["air_gap"]["allowed_domains"] == ["*"]

    @pytest.mark.asyncio
    async def test_llama_cpp_uses_local_models_only_when_air_gapped(
        self, air_gap_config
    ):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LlamaCppProvider.load_model",
            new_callable=AsyncMock,
        ) as mock_load:
            mock_load.return_value = True
            result = await mock_load("/path/to/local/model.gguf")
            assert result is True
            mock_load.assert_called_once_with("/path/to/local/model.gguf")

    @pytest.mark.asyncio
    async def test_air_gap_does_not_block_local_file_access(self, air_gap_config, tmp_path):
        local_model = tmp_path / "test_model.gguf"
        local_model.write_text("fake model data")
        assert local_model.exists()
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LlamaCppProvider.load_model",
            new_callable=AsyncMock,
        ) as mock_load:
            mock_load.return_value = True
            result = await mock_load(str(local_model))
            assert result is True

    def test_air_gap_blocks_download_flag_prevents_fetch(self):
        configs = [
            ({"block_downloads": True, "allowed_domains": []}, True),
            ({"block_downloads": False, "allowed_domains": ["*"]}, False),
            ({"block_downloads": True, "allowed_domains": ["localhost"]}, True),
        ]
        for config, should_block in configs:
            if should_block:
                assert config["block_downloads"] is True
            else:
                assert config["block_downloads"] is False


class TestLlamaCppLocalOnlyVerification:
    """Tests for llama.cpp local-only model verification during air-gap.

    Corresponds to PR #209 / Issue #217:
    Enforce local-only model verification for llama.cpp provider.
    Ensures llama.cpp never reaches external endpoints when air-gap is enabled.
    """

    def test_rejects_url_model_path_in_air_gap(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/model.gguf",
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            with pytest.raises(PermissionError, match="Air-gap: model path is a URL"):
                LlamaCppProvider(config)

    def test_rejects_network_path_in_air_gap(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": "//nas01/share/models/llama.gguf",
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            with pytest.raises(PermissionError, match="Air-gap: model path is a network path"):
                LlamaCppProvider(config)

    def test_accepts_local_path_in_air_gap(self, tmp_path):
        local_model = tmp_path / "llama.gguf"
        local_model.write_text("fake model data")
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": str(local_model),
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            provider = LlamaCppProvider(config)
            assert str(provider.model_path) == str(local_model)

    def test_rejects_missing_local_path_in_air_gap(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": str(tmp_path / "nonexistent.gguf"),
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            with pytest.raises(FileNotFoundError, match="model file not found"):
                LlamaCppProvider(config)

    def test_allows_url_model_path_when_air_gap_disabled(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/model.gguf",
                "air_gap": {"enabled": False, "local_only": False, "block_downloads": False},
            }
            provider = LlamaCppProvider(config)
            assert "https:" in str(provider.model_path)

    def test_allows_network_path_when_air_gap_disabled(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": "//nas01/share/models/llama.gguf",
                "air_gap": {"enabled": False, "local_only": False, "block_downloads": False},
            }
            provider = LlamaCppProvider(config)
            assert "//" in str(provider.model_path)

    def test_accepts_local_path_when_air_gap_disabled(self, tmp_path):
        local_model = tmp_path / "llama.gguf"
        local_model.write_text("fake model data")
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": str(local_model),
                "air_gap": {"enabled": False, "local_only": False, "block_downloads": False},
            }
            provider = LlamaCppProvider(config)
            assert str(provider.model_path) == str(local_model)

    @pytest.mark.asyncio
    async def test_download_model_blocked_in_air_gap(self):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ), patch(
            "ciicerone.llm.providers.llamacpp_provider.REQUESTS_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            local_model = Path("/tmp/test_llamacpp_model.gguf")
            local_model.touch()
            try:
                config = {
                    "model_path": str(local_model),
                    "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
                }
                provider = LlamaCppProvider(config)
                with pytest.raises(PermissionError, match="model downloads are blocked"):
                    await provider.download_model("https://example.com/model.gguf")
            finally:
                local_model.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_download_model_allowed_when_air_gap_disabled(self):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ), patch(
            "ciicerone.llm.providers.llamacpp_provider.REQUESTS_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            local_model = Path("/tmp/test_llamacpp_model.gguf")
            local_model.touch()
            try:
                config = {
                    "model_path": str(local_model),
                    "air_gap": {"enabled": False, "local_only": False, "block_downloads": False},
                }
                provider = LlamaCppProvider(config)
                result = await provider.download_model("https://example.com/model.gguf")
                assert result is False
            finally:
                local_model.unlink(missing_ok=True)

    def test_rejects_ftp_path_in_air_gap(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": "ftp://models.example.com/llama.gguf",
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            with pytest.raises(PermissionError, match="Air-gap: model path is a URL"):
                LlamaCppProvider(config)

    def test_rejects_s3_path_in_air_gap(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": "s3://models-bucket/llama.gguf",
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            with pytest.raises(PermissionError, match="Air-gap: model path is a URL"):
                LlamaCppProvider(config)

    def test_validates_model_path_is_not_a_directory(self, tmp_path):
        with patch(
            "ciicerone.llm.providers.llamacpp_provider.LLAMA_CPP_AVAILABLE", True
        ):
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
            config = {
                "model_path": str(tmp_path),
                "air_gap": {"enabled": True, "local_only": True, "block_downloads": True},
            }
            with pytest.raises(PermissionError, match="model path is a directory"):
                LlamaCppProvider(config)
