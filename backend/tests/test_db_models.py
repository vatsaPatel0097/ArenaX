import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.db.base import Base
from app.db.models import Battle, EloRating, Model, Vote, VoteResult
from app.db.session import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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


@pytest.mark.asyncio
async def test_model_creation(db_session: AsyncSession):
    """Test creating and querying a Model entry."""
    model = Model(
        id="google/gemini-2.5-flash",
        provider="google",
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        is_active=True,
    )
    db_session.add(model)
    await db_session.commit()

    stmt = select(Model).where(Model.id == "google/gemini-2.5-flash")
    result = await db_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.id == "google/gemini-2.5-flash"
    assert retrieved.provider == "google"
    assert retrieved.model_id == "gemini-2.5-flash"
    assert retrieved.display_name == "Gemini 2.5 Flash"
    assert retrieved.is_active is True
    assert repr(retrieved) == "<Model(id='google/gemini-2.5-flash', provider='google', model_id='gemini-2.5-flash')>"


@pytest.mark.asyncio
async def test_battle_and_relationships(db_session: AsyncSession):
    """Test creating a Battle instance linked to two models."""
    model_a = Model(
        id="google/gemini-2.5-flash",
        provider="google",
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
    )
    model_b = Model(
        id="groq/llama-3.3-70b",
        provider="groq",
        model_id="llama-3.3-70b",
        display_name="Llama 3.3 70B",
    )
    db_session.add_all([model_a, model_b])
    await db_session.commit()

    battle = Battle(
        prompt="Explain quantum computing in simple terms.",
        model_a_id=model_a.id,
        model_b_id=model_b.id,
        response_a="Quantum computing uses qubits...",
        response_b="Unlike classical computers...",
    )
    db_session.add(battle)
    await db_session.commit()

    stmt = select(Battle).where(Battle.id == battle.id)
    result = await db_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.prompt == "Explain quantum computing in simple terms."
    assert retrieved.model_a_id == model_a.id
    assert retrieved.model_b_id == model_b.id
    assert retrieved.model_a.display_name == "Gemini 2.5 Flash"
    assert retrieved.model_b.display_name == "Llama 3.3 70B"


@pytest.mark.asyncio
async def test_vote_creation_and_enum(db_session: AsyncSession):
    """Test casting a vote with VoteResult enum values."""
    model_a = Model(id="m1", provider="p1", model_id="m1", display_name="M1")
    model_b = Model(id="m2", provider="p2", model_id="m2", display_name="M2")
    battle = Battle(prompt="Test", model_a_id="m1", model_b_id="m2")
    db_session.add_all([model_a, model_b, battle])
    await db_session.commit()

    vote = Vote(
        battle_id=battle.id,
        result=VoteResult.MODEL_A,
    )
    db_session.add(vote)
    await db_session.commit()

    stmt = select(Vote).where(Vote.battle_id == battle.id)
    result = await db_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.result == VoteResult.MODEL_A
    assert retrieved.battle.prompt == "Test"


@pytest.mark.asyncio
async def test_elo_rating_model(db_session: AsyncSession):
    """Test EloRating model creation, defaults, and model relationship."""
    model = Model(id="cerebras/llama-3.3-70b", provider="cerebras", model_id="llama-3.3-70b", display_name="Cerebras Llama")
    db_session.add(model)
    await db_session.commit()

    elo = EloRating(
        model_id=model.id,
        rating=1200.5,
        games_played=10,
        wins=7,
        losses=2,
        ties=1,
    )
    db_session.add(elo)
    await db_session.commit()

    stmt = select(EloRating).where(EloRating.model_id == model.id)
    result = await db_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.rating == 1200.5
    assert retrieved.games_played == 10
    assert retrieved.wins == 7
    assert retrieved.losses == 2
    assert retrieved.ties == 1
    assert retrieved.model.display_name == "Cerebras Llama"


@pytest.mark.asyncio
async def test_get_db_generator():
    """Test get_db async generator dependency behavior."""
    gen = get_db()
    session = await anext(gen)
    assert isinstance(session, AsyncSession)
    await gen.aclose()
