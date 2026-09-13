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

GROQ_DEFAULT_MODELS = [
    ModelInfo(
        id="llama-3.3-70b-versatile",
        name="Llama 3.3 70B Versatile",
        provider="groq",
        tier="free",
        context_length=128000,
        description="Meta Llama 3.3 70B served with ultra-low latency LPUs on Groq Cloud.",
        is_active=True,
    ),
    ModelInfo(
        id="llama-3.1-8b-instant",
        name="Llama 3.1 8B Instant",
        provider="groq",
        tier="free",
        context_length=128000,
        description="Fastest Llama 8B model running on Groq hardware.",
        is_active=True,
    ),
    ModelInfo(
        id="mixtral-8x7b-32768",
        name="Mixtral 8x7B Instruct",
        provider="groq",
        tier="free",
        context_length=32768,
        description="Mistral AI MoE model served at blazingly high speed.",
        is_active=True,
    ),
    ModelInfo(
        id="gemma2-9b-it",
        name="Gemma 2 9B IT",
        provider="groq",
        tier="free",
        context_length=8192,
        description="Google Gemma 2 9B instruction tuned model via Groq.",
        is_active=True,
    ),
]


class GroqAdapter(BaseProviderAdapter):
    """Adapter for Groq Cloud ultra-fast inference API."""

    def __init__(self, api_key: Optional[str] = None, api_base: str = "https://api.groq.com/openai/v1"):
        self._api_key = api_key
        self.api_base = api_base.rstrip("/")

    @property
    def api_key(self) -> str:
        return self._api_key or settings.GROQ_API_KEY or ""

    @property
    def provider_name(self) -> str:
        return "groq"

    def get_supported_models(self) -> List[ModelInfo]:
        return GROQ_DEFAULT_MODELS

    async def generate_response(
        self, prompt: str, model_id: str
    ) -> AsyncGenerator[str, None]:
        if not self.supports_model(model_id):
            raise ModelNotFoundError(model_id=model_id)

        key = self.api_key
        if not key:
            raise ProviderUnavailableError(
                provider=self.provider_name,
                message="Groq API key is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 429:
                        raise ProviderQuotaExceededError(
                            provider=self.provider_name,
                            message=f"Groq rate limit or quota exceeded for model {model_id}.",
                        )
                    if response.status_code == 404:
                        raise ModelNotFoundError(model_id=model_id)
                    if response.status_code != 200:
                        body_text = await response.aread()
                        raise ProviderUnavailableError(
                            provider=self.provider_name,
                            message=f"Groq API returned HTTP status {response.status_code}: {body_text.decode('utf-8', errors='ignore')}",
                        )

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            data_json = json.loads(data_str)
                            choices = data_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except (ProviderQuotaExceededError, ModelNotFoundError, ProviderUnavailableError):
            raise
        except Exception as exc:
            logger.error("Groq request failed: %s", exc)
            raise ProviderUnavailableError(
                provider=self.provider_name,
                message=f"Groq provider error: {str(exc)}",
            ) from exc
