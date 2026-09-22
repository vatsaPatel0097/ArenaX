import asyncio
from typing import AsyncGenerator, Literal, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseProviderAdapter
from app.core.errors import (
    BattleNotFoundError,
    ModelNotFoundError,
    ProviderQuotaExceededError,
)
from app.db.models import Battle
from app.schemas.battle import BattleStreamChunk
from app.services.model_registry import ModelRegistry, model_registry


class BattleService:
    """Service orchestrating side-by-side LLM battle inference and DB persistence.

    Handles concurrent dual-model streaming execution via asyncio tasks, graceful partial
    stream failure handling, and CRUD operations for battle entities in PostgreSQL.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        """Initialize BattleService.

        Args:
            registry: Custom ModelRegistry instance or defaults to global model_registry.
        """
        self.registry = registry or model_registry

    async def run_battle_inference(
        self, prompt: str, model_a_id: str, model_b_id: str
    ) -> AsyncGenerator[BattleStreamChunk, None]:
        """Asynchronously execute inference for prompt across model_a and model_b in parallel.

        Yields real-time BattleStreamChunk objects multiplexed from both adapter streams.
        If a stream for one slot fails, an error chunk is yielded for that slot while the other
        slot continues generating normally.

        Args:
            prompt: User prompt for side-by-side evaluation.
            model_a_id: Model ID for Model A (slot A).
            model_b_id: Model ID for Model B (slot B).

        Yields:
            BattleStreamChunk for slot A or B as text chunks or errors arrive.

        Raises:
            ModelNotFoundError: If model_a_id or model_b_id is not registered.
            ProviderQuotaExceededError: If rate limit / quota for either model's provider is hit.
        """
        # 1. Validate both models exist in registry
        model_a_info = self.registry.get_model(model_a_id)
        model_b_info = self.registry.get_model(model_b_id)

        # 2. Get provider adapters
        adapter_a = self.registry.get_adapter_for_model(model_a_id)
        adapter_b = self.registry.get_adapter_for_model(model_b_id)

        # 3. Check quota availability before initiating streams
        quota_a_ok = await adapter_a.check_quota_available(model_a_id)
        if not quota_a_ok:
            raise ProviderQuotaExceededError(provider=model_a_info.provider)

        quota_b_ok = await adapter_b.check_quota_available(model_b_id)
        if not quota_b_ok:
            raise ProviderQuotaExceededError(provider=model_b_info.provider)

        # 4. Multiplex streams concurrently via asyncio.Queue
        queue: asyncio.Queue[BattleStreamChunk] = asyncio.Queue()

        async def _stream_producer(
            slot: Literal["model_a", "model_b"],
            model_id: str,
            adapter: BaseProviderAdapter,
        ) -> None:
            """Worker task pushing chunks from adapter stream into the queue."""
            try:
                async for chunk in adapter.generate_response(prompt, model_id):
                    await queue.put(
                        BattleStreamChunk(
                            slot=slot,
                            model_id=model_id,
                            content=chunk,
                            error=None,
                            is_done=False,
                        )
                    )
                # Normal completion
                await queue.put(
                    BattleStreamChunk(
                        slot=slot,
                        model_id=model_id,
                        content="",
                        error=None,
                        is_done=True,
                    )
                )
            except Exception as exc:
                # Gracefully catch stream errors (e.g. timeout, provider crash)
                await queue.put(
                    BattleStreamChunk(
                        slot=slot,
                        model_id=model_id,
                        content="",
                        error=str(exc),
                        is_done=True,
                    )
                )

        task_a = asyncio.create_task(_stream_producer("model_a", model_a_id, adapter_a))
        task_b = asyncio.create_task(_stream_producer("model_b", model_b_id, adapter_b))

        active_producers = 2
        try:
            while active_producers > 0 or not queue.empty():
                chunk = await queue.get()
                yield chunk
                if chunk.is_done:
                    active_producers -= 1
        finally:
            # Ensure worker tasks finish cleanly
            await asyncio.gather(task_a, task_b, return_exceptions=True)

    async def create_battle(
        self,
        db: AsyncSession,
        prompt: str,
        model_a_id: str,
        model_b_id: str,
        response_a: Optional[str] = None,
        response_b: Optional[str] = None,
    ) -> Battle:
        """Create and persist a new Battle record in PostgreSQL.

        Args:
            db: AsyncSession database instance.
            prompt: Original prompt text.
            model_a_id: Model ID for slot A.
            model_b_id: Model ID for slot B.
            response_a: Optional full text output for Model A.
            response_b: Optional full text output for Model B.

        Returns:
            Created Battle ORM instance.

        Raises:
            ModelNotFoundError: If model_a_id or model_b_id is not registered.
        """
        # Ensure models exist in registry
        self.registry.get_model(model_a_id)
        self.registry.get_model(model_b_id)

        battle = Battle(
            id=str(uuid.uuid4()),
            prompt=prompt,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            response_a=response_a,
            response_b=response_b,
        )
        db.add(battle)
        await db.commit()
        await db.refresh(battle)
        return battle

    async def get_battle(self, db: AsyncSession, battle_id: str) -> Battle:
        """Fetch a Battle entity by ID from PostgreSQL.

        Args:
            db: AsyncSession database instance.
            battle_id: Unique battle UUID string.

        Returns:
            Battle ORM instance.

        Raises:
            BattleNotFoundError: If no record matching battle_id exists.
        """
        stmt = select(Battle).where(Battle.id == battle_id)
        result = await db.execute(stmt)
        battle = result.scalar_one_or_none()
        if not battle:
            raise BattleNotFoundError(battle_id=battle_id)
        return battle
