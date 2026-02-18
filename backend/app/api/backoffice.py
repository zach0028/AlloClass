from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.classification_result import ClassificationResult
from app.schemas.backoffice import (
    DeleteTicketsRequest,
    DripFeedStartRequest,
    DripFeedStatusResponse,
    GenerateRequest,
    GeneratedTicketResponse,
    ScenarioResponse,
)
from app.services.scenario_loader import get_all_scenarios, get_scenario

router = APIRouter(prefix="/api/backoffice", tags=["Backoffice"])


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios():
    return [
        ScenarioResponse(
            id=s["id"],
            name=s["name"],
            description=s["description"],
            icon=s.get("icon", "zap"),
            strategy=s.get("strategy", "blind"),
            difficulty_bias=s.get("difficulty_bias", "balanced"),
        )
        for s in get_all_scenarios()
    ]


@router.post("/generate", response_model=list[GeneratedTicketResponse], status_code=201)
async def generate_tickets(
    request: GenerateRequest, db: AsyncSession = Depends(get_db)
):
    from app.services.blind_ticket_generator import generate_blind_tickets
    from app.services.classification_pipeline import classify_batch
    from app.services.config_management import get_config_with_relations
    from app.services.exam_builder import generate_adversarial_cases

    try:
        config = await get_config_with_relations(request.config_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="Config non trouvee")

    scenario = get_scenario(request.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' non trouve")

    if scenario.get("strategy") == "adversarial":
        cases = await generate_adversarial_cases(config, count=request.count)
        texts = []
        for c in cases:
            t = c.get("text") or c.get("ticket") or c.get("content") or c.get("message") or ""
            if t.strip():
                texts.append(t.strip())
    else:
        texts = await generate_blind_tickets(
            config, count=request.count, scenario_id=request.scenario_id
        )

    if not texts:
        return []

    classifications = await classify_batch(texts, config, db)
    return [
        GeneratedTicketResponse(
            id=c.id,
            input_text=c.input_text,
            overall_confidence=c.overall_confidence,
            was_challenged=c.was_challenged,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in classifications
    ]


@router.delete("/tickets/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClassificationResult).where(ClassificationResult.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouve")
    await db.delete(ticket)
    await db.commit()


@router.post("/tickets/delete-batch", status_code=204)
async def delete_tickets_batch(
    request: DeleteTicketsRequest, db: AsyncSession = Depends(get_db)
):
    await db.execute(
        delete(ClassificationResult).where(ClassificationResult.id.in_(request.ids))
    )
    await db.commit()


@router.post("/drip-feed/start", response_model=DripFeedStatusResponse)
async def start_drip_feed(request: DripFeedStartRequest):
    from app.services.blind_ticket_generator import drip_feed_manager

    scenario = get_scenario(request.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' non trouve")

    if scenario.get("strategy") == "adversarial":
        raise HTTPException(
            status_code=400,
            detail="Le drip-feed n'est pas compatible avec les scenarios adversarial",
        )

    await drip_feed_manager.start(
        request.config_id,
        request.interval_seconds,
        request.total_count,
        scenario_id=request.scenario_id,
    )
    return drip_feed_manager.get_status()


@router.post("/drip-feed/stop", response_model=DripFeedStatusResponse)
async def stop_drip_feed():
    from app.services.blind_ticket_generator import drip_feed_manager

    await drip_feed_manager.stop()
    return drip_feed_manager.get_status()


@router.get("/status", response_model=DripFeedStatusResponse)
async def get_drip_feed_status():
    from app.services.blind_ticket_generator import drip_feed_manager

    return drip_feed_manager.get_status()
