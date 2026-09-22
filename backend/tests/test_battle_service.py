import asyncio
from typing import AsyncGenerator, List, Optional
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.adapters.base import BaseProviderAdapter
from app.core.errors import (
    BattleNotFoundError,
    ModelNotFoundError,
    ProviderQuotaExceededError,
    ProviderUnavailableError,
)
from app.db.base import Base
from app.db.models import Model
from app.schemas.model import ModelInfo
from app.services.battle_service import BattleService
from app.services.model_registry import ModelRegistry

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class MockAdapter(BaseProviderAdapter):
    """Mock adapter for testing BattleService parallel streaming behavior."""

    def __init__(
        self,
        name: str,
        models: List[ModelInfo],
        chunks: Optional[List[str]] = None,
        fail_stream: bool = False,
        quota_available: bool = True,
    ) -> None:
        self._name = name
        self._models = models
        self.chunks = chunks or ["Hello ", "world!"]
        self.fail_stream = fail_stream
        self.quota_available = quota_available

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate_response(
        self, prompt: str, model_id: str
    ) -> AsyncGenerator[str, None]:
        for chunk in self.chunks:
            await asyncio.sleep(0.01)
            if self.fail_stream:
                raise ProviderUnavailableError(
                    provider=self._name, message=f"Stream error for {model_id}"
                )
            yield chunk

    async def check_quota_available(self, model_id: str) -> bool:
        return self.quota_available

    def get_supported_models(self) -> List[ModelInfo]:
        return self._models


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def mock_registry():
    registry = ModelRegistry()
    m1 = ModelInfo(
        id="provider_a/model-1",
        name="Model A",
        provider="provider_a",
    )
    m2 = ModelInfo(
        id="provider_b/model-2",
        name="Model B",
        provider="provider_b",
    )
    adapter_a = MockAdapter("provider_a", [m1], chunks=["A1 ", "A2 "])
    adapter_b = MockAdapter("provider_b", [m2], chunks=["B1 ", "B2 "])
    registry.register_adapter_with_models(adapter_a)
    registry.register_adapter_with_models(adapter_b)
    return registry, adapter_a, adapter_b


@pytest.mark.asyncio
async def test_run_battle_inference_success(mock_registry):
    registry, _, _ = mock_registry
    battle_service = BattleService(registry=registry)

    chunks_a = []
    chunks_b = []
    done_count = 0

    async for event in battle_service.run_battle_inference(
        prompt="Compare quantum physics",
        model_a_id="provider_a/model-1",
        model_b_id="provider_b/model-2",
    ):
        if event.is_done:
            done_count += 1
            assert event.error is None
        elif event.slot == "model_a":
            chunks_a.append(event.content)
        elif event.slot == "model_b":
            chunks_b.append(event.content)

    assert "".join(chunks_a) == "A1 A2 "
    assert "".join(chunks_b) == "B1 B2 "
    assert done_count == 2


@pytest.mark.asyncio
async def test_run_battle_inference_invalid_model_a(mock_registry):
    registry, _, _ = mock_registry
    battle_service = BattleService(registry=registry)

    with pytest.raises(ModelNotFoundError) as exc_info:
        async for _ in battle_service.run_battle_inference(
            prompt="Hello",
            model_a_id="nonexistent/model",
            model_b_id="provider_b/model-2",
        ):
            pass
    assert exc_info.value.code == "MODEL_NOT_FOUND"


@pytest.mark.asyncio
async def test_run_battle_inference_invalid_model_b(mock_registry):
    registry, _, _ = mock_registry
    battle_service = BattleService(registry=registry)

    with pytest.raises(ModelNotFoundError) as exc_info:
        async for _ in battle_service.run_battle_inference(
            prompt="Hello",
            model_a_id="provider_a/model-1",
            model_b_id="nonexistent/model",
        ):
            pass
    assert exc_info.value.code == "MODEL_NOT_FOUND"


@pytest.mark.asyncio
async def test_run_battle_inference_quota_exceeded(mock_registry):
    registry, adapter_a, _ = mock_registry
    adapter_a.quota_available = False
    battle_service = BattleService(registry=registry)

    with pytest.raises(ProviderQuotaExceededError) as exc_info:
        async for _ in battle_service.run_battle_inference(
            prompt="Hello",
            model_a_id="provider_a/model-1",
            model_b_id="provider_b/model-2",
        ):
            pass
    assert exc_info.value.code == "PROVIDER_QUOTA_EXHAUSTED"


@pytest.mark.asyncio
async def test_run_battle_inference_partial_failure(mock_registry):
    registry, adapter_a, _ = mock_registry
    adapter_a.fail_stream = True
    battle_service = BattleService(registry=registry)

    chunks_b = []
    error_events = []
    done_count = 0

    async for event in battle_service.run_battle_inference(
        prompt="Hello",
        model_a_id="provider_a/model-1",
        model_b_id="provider_b/model-2",
    ):
        if event.is_done:
            done_count += 1
        if event.error is not None:
            error_events.append(event)
        elif event.slot == "model_b" and not event.is_done:
            chunks_b.append(event.content)

    # Slot A should have produced 1 error chunk and finished
    assert len(error_events) == 1
    assert error_events[0].slot == "model_a"
    assert "Stream error for provider_a/model-1" in error_events[0].error
    # Slot B should complete normally despite Slot A failure
    assert "".join(chunks_b) == "B1 B2 "
    assert done_count == 2


@pytest.mark.asyncio
async def test_create_and_get_battle(db_session: AsyncSession, mock_registry):
    registry, _, _ = mock_registry
    battle_service = BattleService(registry=registry)

    # First add models into DB so FK constraint passes
    m1_db = Model(
        id="provider_a/model-1",
        provider="provider_a",
        model_id="model-1",
        display_name="Model A",
    )
    m2_db = Model(
        id="provider_b/model-2",
        provider="provider_b",
        model_id="model-2",
        display_name="Model B",
    )
    db_session.add_all([m1_db, m2_db])
    await db_session.commit()

    created_battle = await battle_service.create_battle(
        db=db_session,
        prompt="What is AI?",
        model_a_id="provider_a/model-1",
        model_b_id="provider_b/model-2",
        response_a="AI is artificial intelligence.",
        response_b="AI stands for Artificial Intelligence.",
    )

    assert created_battle.id is not None
    assert created_battle.prompt == "What is AI?"
    assert created_battle.response_a == "AI is artificial intelligence."
    assert created_battle.response_b == "AI stands for Artificial Intelligence."

    fetched_battle = await battle_service.get_battle(db=db_session, battle_id=created_battle.id)
    assert fetched_battle.id == created_battle.id
    assert fetched_battle.prompt == "What is AI?"


@pytest.mark.asyncio
async def test_get_battle_not_found(db_session: AsyncSession):
    battle_service = BattleService()
    with pytest.raises(BattleNotFoundError) as exc_info:
        await battle_service.get_battle(db=db_session, battle_id="nonexistent-uuid")
    assert exc_info.value.code == "BATTLE_NOT_FOUND"
