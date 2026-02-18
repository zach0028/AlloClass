from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.openai_client import client as openai_client


async def compute_embedding(text_input: str) -> list[float]:
    response = await openai_client.embeddings.create(
        model=settings.embedding_model,
        input=text_input,
    )
    return response.data[0].embedding


async def search_similar_feedbacks(
    embedding: list[float],
    config_id: UUID,
    db: AsyncSession,
    top_k: int = settings.few_shot_top_k,
) -> list[dict]:
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

    query = text("""
        SELECT
            cr.input_text,
            cr.results,
            uf.corrected_category_id,
            uf.axis_id,
            uf.reasoning_feedback,
            ac.name AS corrected_category_name,
            ax.name AS axis_name,
            cr.embedding <=> :embedding AS distance
        FROM classification_results cr
        JOIN user_feedbacks uf ON uf.classification_id = cr.id
        JOIN axes_categories ac ON ac.id = uf.corrected_category_id
        JOIN axes ax ON ax.id = uf.axis_id
        WHERE cr.config_id = :config_id
            AND cr.embedding IS NOT NULL
            AND uf.active = true
            AND uf.corrected_category_id IS NOT NULL
        ORDER BY cr.embedding <=> :embedding
        LIMIT :top_k
    """)

    result = await db.execute(
        query,
        {
            "embedding": embedding_str,
            "config_id": str(config_id),
            "top_k": top_k,
        },
    )
    rows = result.fetchall()

    return [
        {
            "input_text": row.input_text,
            "corrected_category": row.corrected_category_name,
            "axis_name": row.axis_name,
            "reasoning": row.reasoning_feedback or "",
            "similarity": round(1 - row.distance, 4),
        }
        for row in rows
    ]
