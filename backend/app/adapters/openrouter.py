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

OPENROUTER_DEFAULT_MODELS = [
    ModelInfo(
        id="meta-llama/llama-3.3-70b-instruct:free",
        name="Llama 3.3 70B Instruct (Free)",
        provider="openrouter",
        tier="free",
        context_length=131072,
        description="Meta's flagship 70B open weights model via OpenRouter Free Tier.",
        is_active=True,
    ),
    ModelInfo(
        id="google/gemini-2.0-flash-exp:free",
        name="Gemini 2.0 Flash Exp (Free)",
        provider="openrouter",
        tier="free",
        context_length=1048576,
        description="Google Gemini 2.0 Flash experimental model via OpenRouter Free Tier.",
        is_active=True,
    ),
    ModelInfo(
        id="deepseek/deepseek-r1:free",
        name="DeepSeek R1 (Free)",
        provider="openrouter",
        tier="free",
        context_length=65536,
        description="DeepSeek's premier reasoning model via OpenRouter Free Tier.",
        is_active=True,
    ),
    ModelInfo(
        id="qwen/qwen-2.5-coder-32b-instruct:free",
        name="Qwen 2.5 Coder 32B (Free)",
        provider="openrouter",
        tier="free",
        context_length=32768,
        description="Alibaba Qwen 2.5 specialized coding model via OpenRouter Free Tier.",
        is_active=True,
    ),
]


class OpenRouterAdapter(BaseProviderAdapter):
    """Adapter for OpenRouter LLM Aggregator API."""

    def __init__(self, api_key: Optional[str] = None, api_base: str = "https://openrouter.ai/api/v1"):
        self._api_key = api_key
        self.api_base = api_base.rstrip("/")

    @property
    def api_key(self) -> str:
        return self._api_key or settings.OPENROUTER_API_KEY or ""

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def get_supported_models(self) -> List[ModelInfo]:
        return OPENROUTER_DEFAULT_MODELS

    async def generate_response(
        self, prompt: str, model_id: str
    ) -> AsyncGenerator[str, None]:
        if not self.supports_model(model_id):
            raise ModelNotFoundError(model_id=model_id)

        key = self.api_key
        if not key:
            raise ProviderUnavailableError(
                provider=self.provider_name,
                message="OpenRouter API key is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://arenax.app",
            "X-Title": "ArenaX LLM Benchmark",
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
                            message=f"OpenRouter rate limit or quota exceeded for model {model_id}.",
                        )
                    if response.status_code == 404:
                        raise ModelNotFoundError(model_id=model_id)
                    if response.status_code != 200:
                        body_text = await response.aread()
                        raise ProviderUnavailableError(
                            provider=self.provider_name,
                            message=f"OpenRouter API returned HTTP status {response.status_code}: {body_text.decode('utf-8', errors='ignore')}",
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
            logger.error("OpenRouter request failed: %s", exc)
            raise ProviderUnavailableError(
                provider=self.provider_name,
                message=f"OpenRouter provider error: {str(exc)}",
            ) from exc
