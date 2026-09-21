from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services.travel_assistant import TravelAssistantService

from app.api.recommendations import router as recommendations_router
from app.api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    service = TravelAssistantService()
    app.state.travel_service = service

    try:
        yield
    finally:
        await service.close()


app = FastAPI(
    title="AI Travel Assistant API",
    description="AI-powered travel assistant API",
    version="0.0.1",
    lifespan=lifespan,
)

app.include_router(recommendations_router)
app.include_router(health_router)
