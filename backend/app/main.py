from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analytics,
    backoffice,
    chat,
    classifications,
    classify,
    configs,
    conversations,
    evaluate,
    feedbacks,
    imports,
    learned_rules,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import async_session
    from app.services.config_management import ensure_default_config

    async with async_session() as db:
        await ensure_default_config(db)
    yield


app = FastAPI(
    title="AlloClass",
    description="LLM-powered classification system for subtle categories",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(configs.router)
app.include_router(classify.router)
app.include_router(feedbacks.router)
app.include_router(classifications.router)
app.include_router(backoffice.router)
app.include_router(analytics.router)
app.include_router(evaluate.router)
app.include_router(imports.router)
app.include_router(learned_rules.router)
