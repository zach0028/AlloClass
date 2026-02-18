from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


async def load_conversation_history(
    config_id: UUID,
    db: AsyncSession,
    limit: int = 20,
    conversation_id: UUID | None = None,
) -> list[dict]:
    query = select(ChatMessage)

    if conversation_id:
        query = query.where(ChatMessage.conversation_id == conversation_id)
    else:
        query = query.where(ChatMessage.config_id == config_id)

    result = await db.execute(
        query.order_by(ChatMessage.created_at.desc()).limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()

    return [{"role": row.role, "content": row.content} for row in rows]
