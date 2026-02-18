import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.models.conversation import Conversation
from app.schemas.chat import ChatRequest
from app.services.agent import run_agent
from app.services.config_management import get_config_with_relations

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        config = await get_config_with_relations(request.config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")

    conversation_id = request.conversation_id
    if conversation_id:
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation non trouvee")

    async def event_generator():
        try:
            async for item in run_agent(request.message, config, db, conversation_id=conversation_id):
                yield {
                    "event": item["type"],
                    "data": json.dumps(item.get("data", {}), ensure_ascii=False, default=str),
                }
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Erreur interne : {exc}"}, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
