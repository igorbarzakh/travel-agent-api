from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.exception_handlers import internal_server_error_handler

from app.services.travel_assistant import TravelAssistantService

from app.api.auth import router as auth_router
from app.api.recommendations import router as recommendations_router
from app.api.health import router as health_router
from app.api.conversations import router as conversations_router


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

app.add_exception_handler(
    Exception,
    internal_server_error_handler,
)

app.include_router(auth_router)
app.include_router(recommendations_router)
app.include_router(health_router)
app.include_router(conversations_router)
