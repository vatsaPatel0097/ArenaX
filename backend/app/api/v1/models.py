from typing import Any
from fastapi import APIRouter

from app.schemas.model import ModelListResponse
from app.services.model_registry import model_registry

router = APIRouter()

@router.get("/", response_model=ModelListResponse)
async def get_models() -> Any:
    """
    Retrieve a list of active LLM models from the registry.

    Includes a check for provider quota status.
    Models for which the provider quota is currently exhausted will be excluded from the returned list.
    """
    import asyncio
    active_models = model_registry.list_models(active_only=True)

    async def check_quota(model):
        adapter = model_registry.get_adapter_for_model(model.id)
        has_quota = await adapter.check_quota_available(model.id)
        return model if has_quota else None

    results = await asyncio.gather(*(check_quota(model) for model in active_models))
    available_models = [m for m in results if m is not None]

    return ModelListResponse(
        success=True,
        models=available_models,
        count=len(available_models)
    )
