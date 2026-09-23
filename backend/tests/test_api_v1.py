import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.model import ModelInfo
from app.db.models import Battle
from datetime import datetime
from app.schemas.battle import BattleStreamChunk
from typing import AsyncGenerator

client = TestClient(app)

@pytest.fixture
def mock_model_registry():
    with patch("app.api.v1.models.model_registry") as mock_registry:
        yield mock_registry

@pytest.fixture
def mock_battle_service():
    with patch("app.api.v1.battles.battle_service") as mock_service:
        yield mock_service

def test_get_models(mock_model_registry):
    # Setup mock models
    model1 = ModelInfo(id="model1", name="Model 1", provider="provider1")
    model2 = ModelInfo(id="model2", name="Model 2", provider="provider2")
    mock_model_registry.list_models.return_value = [model1, model2]

    # Mock the adapter for each model
    mock_adapter1 = MagicMock()
    mock_adapter1.check_quota_available = AsyncMock(return_value=True)

    mock_adapter2 = MagicMock()
    mock_adapter2.check_quota_available = AsyncMock(return_value=False)

    def side_effect(model_id):
        if model_id == "model1":
            return mock_adapter1
        return mock_adapter2

    mock_model_registry.get_adapter_for_model.side_effect = side_effect

    # We need to make sure the endpoint runs the async code correctly.
    # With FastAPI TestClient, async endpoints are run synchronously using anyio.
    response = client.get("/api/v1/models/")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Only model1 should be available due to quota
    assert data["count"] == 1
    assert data["models"][0]["id"] == "model1"


def test_create_battle(mock_battle_service):
    # Define mock response for create_battle
    mock_battle = MagicMock(spec=Battle)
    mock_battle.id = "test-uuid"
    mock_battle.prompt = "test prompt"
    mock_battle.model_a_id = "model_a"
    mock_battle.model_b_id = "model_b"
    mock_battle.response_a = None
    mock_battle.response_b = None
    mock_battle.created_at = datetime.utcnow()

    mock_battle_service.create_battle = AsyncMock(return_value=mock_battle)

    request_data = {
        "prompt": "test prompt",
        "model_a_id": "model_a",
        "model_b_id": "model_b"
    }

    response = client.post("/api/v1/battles/", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-uuid"
    assert data["prompt"] == "test prompt"
    assert data["model_a_id"] == "model_a"
    assert data["model_b_id"] == "model_b"

@pytest.fixture
def mock_async_session_local():
    with patch("app.api.v1.battles.AsyncSessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()
        mock_session.return_value.__aenter__.return_value = mock_db
        yield mock_db

def test_battle_stream(mock_battle_service, mock_async_session_local):
    # Setup mock battle object
    # We use a real Battle instance so SQLAlchemy can map it when db.add() is called
    mock_battle = Battle(
        id="test-uuid",
        prompt="test prompt",
        model_a_id="model_a",
        model_b_id="model_b",
        has_streamed=False
    )

    mock_battle_service.get_battle = AsyncMock(return_value=mock_battle)

    # Setup mock generator for run_battle_inference
    async def mock_generator() -> AsyncGenerator[BattleStreamChunk, None]:
        yield BattleStreamChunk(
            slot="model_a",
            model_id="model_a",
            content="Hello",
            is_done=False
        )
        yield BattleStreamChunk(
            slot="model_a",
            model_id="model_a",
            content="",
            is_done=True
        )

    mock_battle_service.run_battle_inference = MagicMock(return_value=mock_generator())

    # Call streaming endpoint using a with block to handle streaming response
    with client.stream("GET", "/api/v1/battles/test-uuid/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Read the content chunks
        chunks = list(response.iter_lines())

        # iter_lines parses by \n so we will have empty strings for the blank lines
        data_chunks = [c for c in chunks if c.startswith("data: ")]

        # Verify chunks
        assert len(data_chunks) == 2  # data: {...} lines

        first_event = data_chunks[0]
        assert first_event.startswith("data: ")

        data_json = json.loads(first_event[6:])
        assert data_json["slot"] == "model_a"
        assert data_json["content"] == "Hello"
