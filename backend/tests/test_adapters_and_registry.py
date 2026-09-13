from typing import AsyncGenerator, List
import pytest

from app.adapters.base import BaseProviderAdapter
from app.core.errors import ModelNotFoundError, ProviderUnavailableError
from app.schemas.model import ModelInfo, ModelListResponse
from app.services.model_registry import ModelRegistry


class DummyProviderAdapter(BaseProviderAdapter):
    """Concrete mock adapter for testing BaseProviderAdapter contract."""

    @property
    def provider_name(self) -> str:
        return "dummy"

    def get_supported_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="dummy/model-v1",
                name="Dummy Model V1",
                provider="dummy",
                tier="free",
                context_length=2048,
                description="Test model",
                is_active=True,
            ),
            ModelInfo(
                id="dummy/model-v2-inactive",
                name="Dummy Model V2 Inactive",
                provider="dummy",
                tier="pro",
                context_length=8192,
                description="Inactive test model",
                is_active=False,
            ),
        ]

    async def generate_response(
        self, prompt: str, model_id: str
    ) -> AsyncGenerator[str, None]:
        if not self.supports_model(model_id):
            raise ModelNotFoundError(model_id=model_id)
        chunks = [f"Hello, ", f"prompt '{prompt}' ", f"received for {model_id}."]
        for chunk in chunks:
            yield chunk


@pytest.fixture
def registry() -> ModelRegistry:
    """Fixture providing a fresh ModelRegistry instance."""
    return ModelRegistry()


@pytest.fixture
def dummy_adapter() -> DummyProviderAdapter:
    """Fixture providing a DummyProviderAdapter instance."""
    return DummyProviderAdapter()


@pytest.mark.asyncio
async def test_base_provider_adapter_contract(dummy_adapter: DummyProviderAdapter):
    """Verify BaseProviderAdapter property and default method behaviors."""
    assert dummy_adapter.provider_name == "dummy"
    assert dummy_adapter.supports_model("dummy/model-v1") is True
    assert dummy_adapter.supports_model("nonexistent/model") is False

    # Verify default quota check returns True while Redis is deferred
    quota_available = await dummy_adapter.check_quota_available("dummy/model-v1")
    assert quota_available is True

    # Verify streaming generator output
    collected_tokens = []
    async for chunk in dummy_adapter.generate_response("test prompt", "dummy/model-v1"):
        collected_tokens.append(chunk)

    assert len(collected_tokens) == 3
    assert "".join(collected_tokens) == "Hello, prompt 'test prompt' received for dummy/model-v1."


def test_model_registry_registration_and_lookup(
    registry: ModelRegistry, dummy_adapter: DummyProviderAdapter
):
    """Verify model and adapter registration, retrieval, and filtering."""
    registry.register_adapter_with_models(dummy_adapter)

    # Lookup valid model
    model = registry.get_model("dummy/model-v1")
    assert model.id == "dummy/model-v1"
    assert model.name == "Dummy Model V1"
    assert model.provider == "dummy"

    # Lookup adapter for valid model
    adapter = registry.get_adapter_for_model("dummy/model-v1")
    assert adapter is dummy_adapter
    assert adapter.provider_name == "dummy"


def test_model_registry_errors(registry: ModelRegistry, dummy_adapter: DummyProviderAdapter):
    """Verify AppError exceptions raised for invalid models or missing adapters."""
    # Lookup non-existent model
    with pytest.raises(ModelNotFoundError) as exc_info:
        registry.get_model("unknown/model")
    assert exc_info.value.code == "MODEL_NOT_FOUND"
    assert exc_info.value.status_code == 404
    assert exc_info.value.details == {"model_id": "unknown/model"}

    # Register model without its adapter
    lonely_model = ModelInfo(
        id="orphan/model",
        name="Orphan Model",
        provider="orphan_provider",
    )
    registry.register_model(lonely_model)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        registry.get_adapter_for_model("orphan/model")
    assert exc_info.value.code == "PROVIDER_UNAVAILABLE"
    assert exc_info.value.status_code == 503
    assert exc_info.value.details == {"provider": "orphan_provider"}


def test_model_registry_listing_and_filtering(
    registry: ModelRegistry, dummy_adapter: DummyProviderAdapter
):
    """Verify listing models with provider and active filters."""
    registry.register_adapter_with_models(dummy_adapter)

    # Active models only (default)
    active_models = registry.list_models()
    assert len(active_models) == 1
    assert active_models[0].id == "dummy/model-v1"

    # All models including inactive
    all_models = registry.list_models(active_only=False)
    assert len(all_models) == 2

    # Provider filter
    dummy_models = registry.list_models(provider="dummy", active_only=False)
    assert len(dummy_models) == 2

    other_provider_models = registry.list_models(provider="other_provider")
    assert len(other_provider_models) == 0


def test_model_registry_unregister_and_clear(
    registry: ModelRegistry, dummy_adapter: DummyProviderAdapter
):
    """Verify unregistering a model and clearing the registry."""
    registry.register_adapter_with_models(dummy_adapter)

    registry.unregister_model("dummy/model-v1")
    assert len(registry.list_models(active_only=False)) == 1

    with pytest.raises(ModelNotFoundError):
        registry.get_model("dummy/model-v1")

    registry.clear()
    assert len(registry.list_models(active_only=False)) == 0


def test_model_schema_validation():
    """Verify Pydantic v2 schemas and response envelope structure."""
    model_info = ModelInfo(
        id="google/gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        provider="google",
    )
    response = ModelListResponse(
        success=True,
        models=[model_info],
        count=1,
    )
    assert response.success is True
    assert response.count == 1
    assert response.models[0].id == "google/gemini-2.5-flash"
