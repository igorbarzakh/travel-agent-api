from app.schemas.error import ErrorResponse


RECOMMENDATION_RESPONSES = {
    502: {
        "model": ErrorResponse,
        "description": "Failed to get a response from the LLM",
    },
}


STREAM_RECOMMENDATION_RESPONSES = {
    200: {
        "description": "SSE stream with recommendation events",
        "content": {
            "text/event-stream": {
                "schema": {
                    "type": "string",
                },
            },
        },
    },
    **RECOMMENDATION_RESPONSES
}