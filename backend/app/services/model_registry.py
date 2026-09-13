from typing import Dict, List, Optional

from app.adapters.base import BaseProviderAdapter
from app.core.errors import ModelNotFoundError, ProviderUnavailableError
from app.schemas.model import ModelInfo


class ModelRegistry:
    """Central registry manager for dynamic LLM models and provider adapters in ArenaX.

    Provides registration, resolution, listing, and dynamic query capabilities for all models
    and their underlying provider adapters.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, BaseProviderAdapter] = {}
        self._models: Dict[str, ModelInfo] = {}

    def register_adapter(self, adapter: BaseProviderAdapter) -> None:
        """Register a provider adapter instance.

        Args:
            adapter: Instance of BaseProviderAdapter.
        """
        self._adapters[adapter.provider_name] = adapter

    def register_model(self, model_info: ModelInfo) -> None:
        """Register or update a model specification.

        Args:
            model_info: ModelInfo schema instance.
        """
        self._models[model_info.id] = model_info

    def register_adapter_with_models(self, adapter: BaseProviderAdapter) -> None:
        """Register an adapter and automatically register all models it supports.

        Args:
            adapter: Instance of BaseProviderAdapter.
        """
        self.register_adapter(adapter)
        for model in adapter.get_supported_models():
            self.register_model(model)

    def get_model(self, model_id: str) -> ModelInfo:
        """Retrieve model metadata by model ID.

        Args:
            model_id: Unique model identifier.

        Returns:
            ModelInfo instance.

        Raises:
            ModelNotFoundError: If model_id is not registered.
        """
        if model_id not in self._models:
            raise ModelNotFoundError(model_id=model_id)
        return self._models[model_id]

    def get_adapter_for_model(self, model_id: str) -> BaseProviderAdapter:
        """Retrieve the provider adapter responsible for the given model ID.

        Args:
            model_id: Unique model identifier.

        Returns:
            BaseProviderAdapter instance.

        Raises:
            ModelNotFoundError: If model_id is not registered.
            ProviderUnavailableError: If provider adapter for model is not registered.
        """
        model_info = self.get_model(model_id)
        provider = model_info.provider
        if provider not in self._adapters:
            raise ProviderUnavailableError(
                provider=provider,
                message=f"Provider adapter '{provider}' for model '{model_id}' is not registered.",
            )
        return self._adapters[provider]

    def list_models(
        self, provider: Optional[str] = None, active_only: bool = True
    ) -> List[ModelInfo]:
        """List registered models, optionally filtered by provider and active status.

        Args:
            provider: Optional provider name filter.
            active_only: If True, returns only models marked as active.

        Returns:
            List of ModelInfo instances.
        """
        models = list(self._models.values())
        if active_only:
            models = [m for m in models if m.is_active]
        if provider:
            models = [m for m in models if m.provider == provider]
        return models

    def unregister_model(self, model_id: str) -> None:
        """Remove a model from the registry.

        Args:
            model_id: Unique model identifier to remove.

        Raises:
            ModelNotFoundError: If model_id is not registered.
        """
        if model_id not in self._models:
            raise ModelNotFoundError(model_id=model_id)
        del self._models[model_id]

    def clear(self) -> None:
        """Reset all registered adapters and models."""
        self._adapters.clear()
        self._models.clear()


# Global singleton instance for app-wide model registry access
model_registry = ModelRegistry()
