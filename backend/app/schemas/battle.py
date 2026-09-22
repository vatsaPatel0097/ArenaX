from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class BattleCreateRequest(BaseModel):
    """Pydantic v2 schema for initiating a side-by-side battle session."""

    prompt: str = Field(..., min_length=1, description="User prompt for dual model inference")
    model_a_id: str = Field(..., description="Model ID for Model A (slot A)")
    model_b_id: str = Field(..., description="Model ID for Model B (slot B)")


class BattleStreamChunk(BaseModel):
    """Pydantic v2 schema for real-time SSE streaming events from battle inference."""

    slot: Literal["model_a", "model_b"] = Field(
        ..., description="Target model slot in the side-by-side battle"
    )
    model_id: str = Field(..., description="Model ID active in this slot")
    content: str = Field(default="", description="Text token/chunk received from provider")
    error: Optional[str] = Field(
        default=None, description="Error message if this provider stream failed"
    )
    is_done: bool = Field(
        default=False, description="Whether inference for this slot has finished"
    )


class BattleResponse(BaseModel):
    """Pydantic v2 schema representing a persisted battle record."""

    id: str = Field(..., description="Unique battle UUID")
    prompt: str = Field(..., description="Original user prompt")
    model_a_id: str = Field(..., description="Model ID for Model A")
    model_b_id: str = Field(..., description="Model ID for Model B")
    response_a: Optional[str] = Field(default=None, description="Full aggregated output for Model A")
    response_b: Optional[str] = Field(default=None, description="Full aggregated output for Model B")
    created_at: datetime = Field(..., description="Timestamp when battle was created")
