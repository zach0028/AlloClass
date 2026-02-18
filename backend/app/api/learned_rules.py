from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.learned_rule import LearnedRule


router = APIRouter(prefix="/api/learned-rules", tags=["Learned Rules"])


class LearnedRuleCreate(BaseModel):
    config_id: UUID
    axis_id: UUID | None = None
    rule_text: str
    source_feedback_count: int = 0


class LearnedRuleUpdate(BaseModel):
    validated_by_user: bool | None = None
    active: bool | None = None


class LearnedRuleResponse(BaseModel):
    id: UUID
    config_id: UUID
    axis_id: UUID | None
    rule_text: str
    source_feedback_count: int
    validated_by_user: bool
    active: bool
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[LearnedRuleResponse])
async def list_learned_rules(config_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LearnedRule)
        .where(LearnedRule.config_id == config_id)
        .order_by(LearnedRule.created_at.desc())
    )
    rules = list(result.scalars().all())
    return [
        LearnedRuleResponse(
            id=r.id,
            config_id=r.config_id,
            axis_id=r.axis_id,
            rule_text=r.rule_text,
            source_feedback_count=r.source_feedback_count,
            validated_by_user=r.validated_by_user,
            active=r.active,
            created_at=str(r.created_at),
        )
        for r in rules
    ]


@router.post("", response_model=LearnedRuleResponse, status_code=201)
async def create_learned_rule(
    body: LearnedRuleCreate, db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(LearnedRule).where(
            and_(
                LearnedRule.config_id == body.config_id,
                LearnedRule.rule_text == body.rule_text,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Cette regle existe deja.")

    rule = LearnedRule(
        config_id=body.config_id,
        axis_id=body.axis_id,
        rule_text=body.rule_text,
        source_feedback_count=body.source_feedback_count,
        validated_by_user=True,
        active=True,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return LearnedRuleResponse(
        id=rule.id,
        config_id=rule.config_id,
        axis_id=rule.axis_id,
        rule_text=rule.rule_text,
        source_feedback_count=rule.source_feedback_count,
        validated_by_user=rule.validated_by_user,
        active=rule.active,
        created_at=str(rule.created_at),
    )


@router.patch("/{rule_id}", response_model=LearnedRuleResponse)
async def update_learned_rule(
    rule_id: UUID, body: LearnedRuleUpdate, db: AsyncSession = Depends(get_db)
):
    rule = await db.get(LearnedRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regle non trouvee.")

    if body.validated_by_user is not None:
        rule.validated_by_user = body.validated_by_user
    if body.active is not None:
        rule.active = body.active

    await db.commit()
    await db.refresh(rule)

    return LearnedRuleResponse(
        id=rule.id,
        config_id=rule.config_id,
        axis_id=rule.axis_id,
        rule_text=rule.rule_text,
        source_feedback_count=rule.source_feedback_count,
        validated_by_user=rule.validated_by_user,
        active=rule.active,
        created_at=str(rule.created_at),
    )


@router.delete("/{rule_id}", status_code=204)
async def delete_learned_rule(
    rule_id: UUID, db: AsyncSession = Depends(get_db)
):
    rule = await db.get(LearnedRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regle non trouvee.")

    await db.delete(rule)
    await db.commit()
