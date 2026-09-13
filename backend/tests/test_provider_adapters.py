import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.adapters.openrouter import OpenRouterAdapter
from app.adapters.google import GoogleAdapter
from app.adapters.groq import GroqAdapter
from app.adapters.cerebras import CerebrasAdapter
from app.adapters.mistral import MistralAdapter
from app.core.errors import (
    ModelNotFoundError,
    ProviderQuotaExceededError,
    ProviderUnavailableError,
)
from app.services.model_registry import ModelRegistry


@pytest.fixture
def registry():
    return ModelRegistry()


def test_adapters_metadata_and_models():
    adapters = [
        OpenRouterAdapter(api_key="test_key"),
        GoogleAdapter(api_key="test_key"),
        GroqAdapter(api_key="test_key"),
        CerebrasAdapter(api_key="test_key"),
        MistralAdapter(api_key="test_key"),
    ]

    expected_names = ["openrouter", "google", "groq", "cerebras", "mistral"]

    for adapter, name in zip(adapters, expected_names):
        assert adapter.provider_name == name
        models = adapter.get_supported_models()
        assert len(models) > 0
        first_model = models[0]
        assert adapter.supports_model(first_model.id)
        assert not adapter.supports_model("nonexistent-model-id-xyz")


def test_registry_with_all_adapters(registry):
    openrouter = OpenRouterAdapter(api_key="key1")
    google = GoogleAdapter(api_key="key2")
    groq = GroqAdapter(api_key="key3")
    cerebras = CerebrasAdapter(api_key="key4")
    mistral = MistralAdapter(api_key="key5")

    for adapter in [openrouter, google, groq, cerebras, mistral]:
        registry.register_adapter_with_models(adapter)

    # Verify total registered active models
    models = registry.list_models()
    assert len(models) >= 14

    # Verify adapter resolution for model
    assert registry.get_adapter_for_model("meta-llama/llama-3.3-70b-instruct:free").provider_name == "openrouter"
    assert registry.get_adapter_for_model("gemini-2.0-flash").provider_name == "google"
    assert registry.get_adapter_for_model("llama-3.3-70b-versatile").provider_name == "groq"
    assert registry.get_adapter_for_model("llama3.3-70b").provider_name == "cerebras"
    assert registry.get_adapter_for_model("mistral-small-latest").provider_name == "mistral"


@pytest.mark.asyncio
async def test_missing_api_key_raises_provider_unavailable():
    # If API key is missing/empty, generating response must raise ProviderUnavailableError gracefully
    adapter = GroqAdapter(api_key="")
    with pytest.raises(ProviderUnavailableError) as exc_info:
        async for _ in adapter.generate_response("Hello", "llama-3.3-70b-versatile"):
            pass
    assert "Groq API key is not configured" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_unsupported_model_raises_model_not_found():
    adapter = GoogleAdapter(api_key="test_key")
    with pytest.raises(ModelNotFoundError):
        async for _ in adapter.generate_response("Hello", "invalid-model"):
            pass


@pytest.mark.asyncio
async def test_openrouter_streaming_success():
    adapter = OpenRouterAdapter(api_key="test_openrouter_key")
    model_id = "meta-llama/llama-3.3-70b-instruct:free"

    lines = [
        'data: {"choices": [{"delta": {"content": "Hello"}}]}',
        'data: {"choices": [{"delta": {"content": " world"}}]}',
        'data: [DONE]',
    ]

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines

    class MockStreamContext:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("httpx.AsyncClient.stream", return_value=MockStreamContext()):
        chunks = []
        async for chunk in adapter.generate_response("Test prompt", model_id):
            chunks.append(chunk)

        assert "".join(chunks) == "Hello world"


@pytest.mark.asyncio
async def test_google_streaming_success():
    adapter = GoogleAdapter(api_key="test_google_key")
    model_id = "gemini-2.0-flash"

    lines = [
        'data: {"candidates": [{"content": {"parts": [{"text": "Gemini"}]}}]}',
        'data: {"candidates": [{"content": {"parts": [{"text": " response"}]}}]}',
    ]

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines

    class MockStreamContext:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("httpx.AsyncClient.stream", return_value=MockStreamContext()):
        chunks = []
        async for chunk in adapter.generate_response("Test prompt", model_id):
            chunks.append(chunk)

        assert "".join(chunks) == "Gemini response"


@pytest.mark.asyncio
async def test_adapter_rate_limit_exceeded_429():
    adapter = GroqAdapter(api_key="test_key")
    model_id = "llama-3.3-70b-versatile"

    mock_response = AsyncMock()
    mock_response.status_code = 429

    class MockStreamContext:
        async def __aenter__(self):
            return mock_response
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("httpx.AsyncClient.stream", return_value=MockStreamContext()):
        with pytest.raises(ProviderQuotaExceededError) as exc_info:
            async for _ in adapter.generate_response("Prompt", model_id):
                pass
        assert exc_info.value.details["provider"] == "groq"
