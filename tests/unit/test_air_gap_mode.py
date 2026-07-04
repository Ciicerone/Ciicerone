"""Unit tests for air-gap mode in model downloads."""

import asyncio
import os
from pathlib import Path
from unittest import mock

import pytest

from ciicerone.llm.exceptions import AirGapViolationError
from ciicerone.llm.model_manager import ModelManager
from ciicerone.llm.providers.ollama_provider import OllamaProvider


def _patch_requests(monkeypatch):
    """Ensure requests.get is never called during air-gap tests."""
    monkeypatch.setattr("ciicerone.llm.model_manager.REQUESTS_AVAILABLE", True)
    requests_mock = mock.MagicMock()
    requests_mock.get.side_effect = Exception("network unavailable")
    monkeypatch.setattr("ciicerone.llm.model_manager.requests", requests_mock)
    return requests_mock


class TestModelManagerAirGap:
    """Tests for ModelManager air-gap behavior."""

    def test_air_gapped_mode_enabled_via_config(self, tmp_path):
        """Air-gap mode can be enabled through configuration."""
        manager = ModelManager(
            config={"model_cache_dir": str(tmp_path), "air_gapped_mode": True}
        )
        assert manager.air_gapped is True

    def test_air_gapped_mode_enabled_via_env(self, tmp_path, monkeypatch):
        """Air-gap mode can be enabled through environment variable."""
        monkeypatch.setenv("AIR_GAPPED_MODE", "true")
        manager = ModelManager(config={"model_cache_dir": str(tmp_path)})
        assert manager.air_gapped is True

    def test_air_gapped_mode_disabled_by_default(self, tmp_path):
        """Air-gap mode is disabled by default."""
        manager = ModelManager(config={"model_cache_dir": str(tmp_path)})
        assert manager.air_gapped is False

    def test_download_raises_air_gap_violation_when_not_preloaded(
        self, tmp_path, monkeypatch
    ):
        """Downloading a missing model in air-gap mode raises AirGapViolationError."""
        _patch_requests(monkeypatch)
        manager = ModelManager(
            config={"model_cache_dir": str(tmp_path), "air_gapped_mode": True}
        )

        with pytest.raises(AirGapViolationError) as exc_info:
            asyncio.run(
                manager.download_model(
                    provider="llamacpp",
                    model_name="missing-model",
                    download_url="https://example.com/model.gguf",
                )
            )

        assert "missing-model not found in local cache" in str(exc_info.value)

    def test_download_uses_preloaded_model_in_air_gap_mode(
        self, tmp_path, monkeypatch
    ):
        """A pre-loaded model is returned in air-gap mode without HTTP calls."""
        _patch_requests(monkeypatch)
        manager = ModelManager(
            config={"model_cache_dir": str(tmp_path), "air_gapped_mode": True}
        )
        model_file = tmp_path / "llamacpp" / "preloaded.gguf"
        model_file.parent.mkdir(parents=True, exist_ok=True)
        model_file.write_text("dummy model")
        manager.register_model("preloaded-model", "llamacpp", str(model_file))

        result = asyncio.run(
            manager.download_model(
                provider="llamacpp",
                model_name="preloaded-model",
                download_url="https://example.com/preloaded.gguf",
            )
        )

        assert result["status"] == "success"
        assert result["model_name"] == "preloaded-model"
        assert Path(result["path"]) == model_file

    def test_non_air_gapped_mode_allows_download(self, tmp_path, monkeypatch):
        """Normal mode falls through to HTTP download when model is missing."""
        _patch_requests(monkeypatch)
        manager = ModelManager(
            config={"model_cache_dir": str(tmp_path), "air_gapped_mode": False}
        )

        # Should not raise AirGapViolationError; instead it proceeds to download
        # and returns an error due to mocked requests.
        result = asyncio.run(
            manager.download_model(
                provider="llamacpp",
                model_name="missing-model",
                download_url="https://example.com/model.gguf",
            )
        )
        assert "error" in result


class TestLlamaCppProviderAirGap:
    """Tests for LlamaCppProvider air-gap behavior."""

    @pytest.fixture
    def llama_cpp_provider(self, tmp_path, monkeypatch):
        """Create a LlamaCppProvider with a valid local model file."""
        monkeypatch.delenv("AIR_GAPPED_MODE", raising=False)
        model_file = tmp_path / "model.gguf"
        model_file.write_text("dummy gguf")
        try:
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider

            return LlamaCppProvider(
                config={"model_path": str(model_file), "air_gapped_mode": True}
            )
        except ImportError:
            pytest.skip("llama-cpp-python not installed")

    def test_air_gapped_mode_blocks_download(self, tmp_path, monkeypatch):
        """External download is blocked in air-gap mode for LlamaCppProvider."""
        model_file = tmp_path / "model.gguf"
        model_file.write_text("dummy gguf")
        try:
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
        except ImportError:
            pytest.skip("llama-cpp-python not installed")

        provider = LlamaCppProvider(
            config={"model_path": str(model_file), "air_gapped_mode": True}
        )
        assert provider.air_gapped is True

        with pytest.raises(AirGapViolationError) as exc_info:
            asyncio.run(
                provider.download_model("https://example.com/model.gguf")
            )

        assert "External model download is blocked" in str(exc_info.value)

    def test_local_model_path_verified(self, tmp_path, monkeypatch):
        """Missing local model raises AirGapViolationError in air-gap mode."""
        missing_path = tmp_path / "missing.gguf"
        try:
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
        except ImportError:
            pytest.skip("llama-cpp-python not installed")

        provider = LlamaCppProvider(
            config={"model_path": str(missing_path), "air_gapped_mode": True}
        )

        with pytest.raises(AirGapViolationError) as exc_info:
            provider._verify_local_model_path(missing_path)

        assert "Pre-load GGUF models" in str(exc_info.value)

    def test_air_gap_disabled_allows_normal_behavior(self, tmp_path, monkeypatch):
        """When air-gap is disabled, missing model raises FileNotFoundError."""
        missing_path = tmp_path / "missing.gguf"
        try:
            from ciicerone.llm.providers.llamacpp_provider import LlamaCppProvider
        except ImportError:
            pytest.skip("llama-cpp-python not installed")

        provider = LlamaCppProvider(
            config={"model_path": str(missing_path), "air_gapped_mode": False}
        )
        assert provider.air_gapped is False

        with pytest.raises(FileNotFoundError):
            provider._verify_local_model_path(missing_path)


class TestOllamaProviderAirGap:
    """Tests for OllamaProvider air-gap behavior."""

    def test_local_only_verification_passes_for_localhost(self, monkeypatch):
        """Localhost Ollama base URL is accepted in air-gap mode."""
        monkeypatch.setenv("AIR_GAPPED_MODE", "true")
        provider = OllamaProvider(
            config={"base_url": "http://localhost:11434", "model": "llama3.2:1b"}
        )
        assert provider.air_gapped is True
        provider._verify_local_only()

    def test_local_only_verification_fails_for_remote(self, monkeypatch):
        """Remote Ollama base URL is rejected in air-gap mode."""
        monkeypatch.setenv("AIR_GAPPED_MODE", "true")
        provider = OllamaProvider(
            config={"base_url": "http://ollama.example.com:11434", "model": "llama3.2:1b"}
        )

        with pytest.raises(AirGapViolationError) as exc_info:
            provider._verify_local_only()

        assert "requires Ollama to run on localhost" in str(exc_info.value)

    def test_ensure_model_available_raises_when_not_preloaded(
        self, monkeypatch
    ):
        """Pulling a missing model in air-gap mode raises AirGapViolationError."""
        monkeypatch.setenv("AIR_GAPPED_MODE", "true")
        provider = OllamaProvider(
            config={"base_url": "http://localhost:11434", "model": "llama3.2:1b"}
        )

        async def _list_models():
            return {"models": []}

        provider._list_models = _list_models

        with pytest.raises(AirGapViolationError) as exc_info:
            asyncio.run(provider._ensure_model_available())

        assert "llama3.2:1b is not pre-loaded" in str(exc_info.value)

    def test_ensure_model_available_uses_preloaded_model(
        self, monkeypatch
    ):
        """A pre-loaded Ollama model is accepted in air-gap mode."""
        monkeypatch.setenv("AIR_GAPPED_MODE", "true")
        provider = OllamaProvider(
            config={"base_url": "http://localhost:11434", "model": "llama3.2:1b"}
        )

        async def _list_models():
            return {"models": [{"name": "llama3.2:1b"}]}

        provider._list_models = _list_models
        asyncio.run(provider._ensure_model_available())

    def test_non_air_gapped_mode_allows_remote_pull(self, monkeypatch):
        """Remote Ollama base URL is allowed when air-gap mode is disabled."""
        monkeypatch.delenv("AIR_GAPPED_MODE", raising=False)
        provider = OllamaProvider(
            config={"base_url": "http://ollama.example.com:11434", "model": "llama3.2:1b"}
        )
        assert provider.air_gapped is False
        provider._verify_local_only()


class TestConfigAirGap:
    """Tests for air-gap configuration schema."""

    def test_air_gapped_mode_default(self):
        """air_gapped_mode defaults to False."""
        from ciicerone.config.loader import CiiceroneConfig

        config = CiiceroneConfig()
        assert config.air_gapped_mode is False

    def test_air_gapped_mode_from_config(self):
        """air_gapped_mode can be set from config data."""
        from ciicerone.config.loader import CiiceroneConfig

        config = CiiceroneConfig(air_gapped_mode=True)
        assert config.air_gapped_mode is True

    def test_air_gapped_mode_from_env(self, monkeypatch):
        """AIR_GAPPED_MODE environment variable is applied."""
        from ciicerone.config.loader import load_config

        monkeypatch.setenv("AIR_GAPPED_MODE", "true")
        config = load_config(config_path="/nonexistent/config.yaml")
        assert config.air_gapped_mode is True

    def test_air_gapped_mode_env_false(self, monkeypatch):
        """AIR_GAPPED_MODE=false disables air-gap mode."""
        from ciicerone.config.loader import load_config

        monkeypatch.setenv("AIR_GAPPED_MODE", "false")
        config = load_config(config_path="/nonexistent/config.yaml")
        assert config.air_gapped_mode is False

