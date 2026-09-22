from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.battle import BattleCreateRequest, BattleResponse, BattleStreamChunk
from app.services.battle_service import BattleService
from app.core.errors import BattleNotFoundError

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
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Stream the parallel responses from Model A and Model B using Server-Sent Events.
    """
    # Verify the battle exists
    try:
        battle = await battle_service.get_battle(db=db, battle_id=battle_id)
    except BattleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    async def sse_generator():
        async for chunk in battle_service.run_battle_inference(
            prompt=battle.prompt,
            model_a_id=battle.model_a_id,
            model_b_id=battle.model_b_id,
        ):
            # Format according to Server-Sent Events spec
            data = chunk.model_dump_json()
            yield f"data: {data}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream"
    )
