from typing import Any
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.schemas.battle import BattleCreateRequest, BattleResponse, BattleStreamChunk
from app.services.battle_service import BattleService
from app.core.errors import BattleAlreadyStreamedError

router = APIRouter()
battle_service = BattleService()

@router.post("/", response_model=BattleResponse)
async def create_battle(
    request: BattleCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new battle instance to evaluate Model A vs Model B.
    """
    battle = await battle_service.create_battle(
        db=db,
        prompt=request.prompt,
        model_a_id=request.model_a_id,
        model_b_id=request.model_b_id,
    )

    return BattleResponse(
        id=battle.id,
        prompt=battle.prompt,
        model_a_id=battle.model_a_id,
        model_b_id=battle.model_b_id,
        response_a=battle.response_a,
        response_b=battle.response_b,
        created_at=battle.created_at,
    )

@router.get("/{battle_id}/stream")
async def stream_battle(
    battle_id: str,
) -> StreamingResponse:
    """
    Stream the parallel responses from Model A and Model B using Server-Sent Events.
    """
    async with AsyncSessionLocal() as db:
        # Verify the battle exists
        battle = await battle_service.get_battle(db=db, battle_id=battle_id)

        # Enforce single-use stream state per battle
        if battle.has_streamed:
            raise BattleAlreadyStreamedError(battle_id=battle_id)

        battle.has_streamed = True
        await db.commit()

        # Extract fields to local variables before the DB session is closed
        prompt = battle.prompt
        model_a_id = battle.model_a_id
        model_b_id = battle.model_b_id

    async def sse_generator():
        async for chunk in battle_service.run_battle_inference(
            prompt=prompt,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
        ):
            # Format according to Server-Sent Events spec
            data = chunk.model_dump_json()
            yield f"data: {data}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream"
    )
