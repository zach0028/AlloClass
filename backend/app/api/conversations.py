from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.chat_message import ChatMessage
from app.models.conversation import Conversation
from app.schemas.chat import (
    ChatMessageResponse,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
)

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    conv = Conversation(config_id=body.config_id, title=body.title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        config_id=conv.config_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
        last_message=None,
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    last_msg_sub = (
        select(
            ChatMessage.conversation_id,
            func.count().label("msg_count"),
            func.max(
                case((ChatMessage.role == "user", ChatMessage.content), else_=None)
            ).label("last_user_msg"),
        )
        .where(ChatMessage.conversation_id.isnot(None))
        .group_by(ChatMessage.conversation_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Conversation,
            func.coalesce(last_msg_sub.c.msg_count, 0).label("msg_count"),
            last_msg_sub.c.last_user_msg,
        )
        .outerjoin(last_msg_sub, Conversation.id == last_msg_sub.c.conversation_id)
        .where(Conversation.config_id == config_id)
        .order_by(Conversation.updated_at.desc())
    )

    items = []
    for row in result.all():
        conv = row[0]
        items.append(
            ConversationResponse(
                id=conv.id,
                config_id=conv.config_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=row[1],
                last_message=row[2],
            )
        )
    return ConversationListResponse(items=items)


@router.get("/{conversation_id}/messages", response_model=list[ChatMessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvee")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )
    return list(result.scalars().all())


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    title: str,
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvee")

    conv.title = title
    await db.commit()
    await db.refresh(conv)

    msg_count = await db.scalar(
        select(func.count()).where(ChatMessage.conversation_id == conversation_id)
    )

    return ConversationResponse(
        id=conv.id,
        config_id=conv.config_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=msg_count or 0,
        last_message=None,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvee")

    await db.delete(conv)
    await db.commit()
