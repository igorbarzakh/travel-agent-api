from fastapi import Request

from app.services.travel_assistant import TravelAssistantService


def get_travel_service(request: Request) -> TravelAssistantService:
    return request.app.state.travel_service
