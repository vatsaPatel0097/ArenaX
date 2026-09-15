import json
import logging
from typing import AsyncGenerator, List, Optional

import httpx
from app.adapters.base import BaseProviderAdapter
from app.core.config import settings
from app.core.errors import (
    ModelNotFoundError,
    ProviderQuotaExceededError,
    ProviderUnavailableError,
)
from app.schemas.model import ModelInfo

logger = logging.getLogger(__name__)

GOOGLE_DEFAULT_MODELS = [
    ModelInfo(
        id="gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="google",
        tier="free",
        context_length=1048576,
        description="Google's next-gen high speed multimodal model.",
        is_active=True,
    ),
    ModelInfo(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        tier="free",
        context_length=2097152,
        description="Google's premier complex reasoning model with 2M token context window.",
        is_active=True,
    ),
    ModelInfo(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        tier="free",
        context_length=1048576,
        description="Google's fast and cost-efficient multimodal model.",
        is_active=True,
    ),
]


class GoogleAdapter(BaseProviderAdapter):
    """Adapter for Google AI Studio Gemini API."""

    def __init__(self, api_key: Optional[str] = None, api_base: str = "https://generativelanguage.googleapis.com/v1beta"):
        self._api_key = api_key
        self.api_base = api_base.rstrip("/")

    @property
    def api_key(self) -> str:
        return self._api_key or settings.GEMINI_API_KEY or ""

    @property
    def provider_name(self) -> str:
        return "google"

    def get_supported_models(self) -> List[ModelInfo]:
        return GOOGLE_DEFAULT_MODELS

    async def generate_response(
        self, prompt: str, model_id: str
    ) -> AsyncGenerator[str, None]:
        if not self.supports_model(model_id):
            raise ModelNotFoundError(model_id=model_id)

        key = self.api_key
        if not key:
            raise ProviderUnavailableError(
                provider=self.provider_name,
                message="Google Gemini API key is not configured.",
            )

        url = f"{self.api_base}/models/{model_id}:streamGenerateContent?alt=sse&key={key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 429:
                        raise ProviderQuotaExceededError(
                            provider=self.provider_name,
                            message=f"Google Gemini rate limit or quota exceeded for model {model_id}.",
                        )
                    if response.status_code == 404:
                        raise ModelNotFoundError(model_id=model_id)
                    if response.status_code != 200:
                        body_text = await response.aread()
                        raise ProviderUnavailableError(
                            provider=self.provider_name,
                            message=f"Google Gemini API returned HTTP status {response.status_code}: {body_text.decode('utf-8', errors='ignore')}",
                        )

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()
                        if not data_str:
                            continue

                        try:
                            data_json = json.loads(data_str)
                            candidates = data_json.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                for part in parts:
                                    text_chunk = part.get("text")
                                    if text_chunk:
                                        yield text_chunk
                        except json.JSONDecodeError:
                            continue

        except (ProviderQuotaExceededError, ModelNotFoundError, ProviderUnavailableError):
            raise
        except Exception as exc:
            logger.error("Google Gemini request failed: %s", exc)
            raise ProviderUnavailableError(
                provider=self.provider_name,
                message=f"Google provider error: {str(exc)}",
            ) from exc
