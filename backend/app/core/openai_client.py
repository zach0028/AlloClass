from openai import AsyncOpenAI

from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    max_retries=3,
    timeout=120.0,
)
