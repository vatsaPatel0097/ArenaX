from typing import List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Pydantic v2 schema representing an LLM model's metadata in ArenaX."""

    id: str = Field(..., description="Unique model identifier (e.g. 'google/gemini-2.5-flash')")
    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(..., description="Provider identifier (e.g. 'google', 'groq', 'openrouter')")
    tier: str = Field(default="free", description="Subscription or access tier required ('free', 'pro')")
    context_length: int = Field(default=4096, description="Context window token capacity")
    description: str = Field(default="", description="Short description of model capabilities")
    is_active: bool = Field(default=True, description="Whether the model is currently active and selectable")


class ModelListResponse(BaseModel):
    """Standardized API response container for listing models."""

    success: bool = Field(default=True)
    models: List[ModelInfo] = Field(default_factory=list)
    count: int = Field(default=0)
