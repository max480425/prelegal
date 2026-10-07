"""AI chat routes: greeting + conversational turn (public, stateless)."""

import asyncio

from fastapi import APIRouter, HTTPException, status

from backend.schemas.chat import ChatMessageRequest, ChatTurnResponse
from backend.services.chat_service import (
    ChatConfigError,
    ChatOutputError,
    ChatService,
    ChatUpstreamError,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.get("/greeting", response_model=ChatTurnResponse)
async def greeting():
    """Static AI greeting (no LLM call; same shape as a chat turn)."""
    return chat_service.greeting()


@router.post("/message", response_model=ChatTurnResponse)
async def message(request: ChatMessageRequest):
    """Run one conversational turn: AI reply + extracted document fields."""
    try:
        return await chat_service.chat(
            [m.model_dump() for m in request.messages],
            request.fields,
        )
    except ChatConfigError as exc:
        # Not configured (e.g. container without OPENROUTER_API_KEY).
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ChatUpstreamError as exc:
        # Provider unreachable / rate-limited / timed out.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except ChatOutputError as exc:
        # Unusable model output after the service's one retry.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {exc}",
        )
