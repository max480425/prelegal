"""AI chat routes: greeting + conversational turn (public, stateless).

Chat is public and every turn spends OpenRouter credit, so /message is
rate-limited per IP and bounded in size (message count via the schema,
total characters here).
"""

import time

from fastapi import APIRouter, HTTPException, Request, status

from backend.schemas.chat import ChatMessageRequest, ChatTurnResponse
from backend.services.chat_service import (
    ChatConfigError,
    ChatOutputError,
    ChatService,
    ChatUpstreamError,
)
from backend.utils.config import get_settings

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()

# Per-IP fixed-window counter: {ip: (window_epoch_seconds, request_count)}.
_rate_buckets: dict = {}
_MAX_TRACKED_IPS = 1000
_HISTORY_CHAR_BUDGET = 32_000
_RATE_WINDOW_SECONDS = 60


def _enforce_rate_limit(ip: str) -> None:
    """Raise 429 when this IP exceeds CHAT_RATE_LIMIT requests/minute."""
    limit = get_settings().CHAT_RATE_LIMIT
    if limit <= 0:
        return
    now = time.time()
    if len(_rate_buckets) > _MAX_TRACKED_IPS:
        # Drop expired windows so a flood of unique IPs cannot grow unbounded.
        for key in [k for k, (start, _) in _rate_buckets.items() if now - start >= _RATE_WINDOW_SECONDS]:
            del _rate_buckets[key]
    window_start, count = _rate_buckets.get(ip, (now, 0))
    if now - window_start >= _RATE_WINDOW_SECONDS:
        window_start, count = now, 0
    count += 1
    _rate_buckets[ip] = (window_start, count)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many chat requests — try again in a minute",
        )


@router.get("/greeting", response_model=ChatTurnResponse)
async def greeting():
    """Static AI greeting (no LLM call; same shape as a chat turn)."""
    return chat_service.greeting()


@router.post("/message", response_model=ChatTurnResponse)
async def message(request: ChatMessageRequest, http_request: Request):
    """Run one conversational turn: AI reply + extracted document fields."""
    client = http_request.client
    _enforce_rate_limit(client.host if client else "unknown")

    total_chars = sum(len(m.content) for m in request.messages)
    if total_chars > _HISTORY_CHAR_BUDGET:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Conversation history is too long — start a new document",
        )

    try:
        return await chat_service.chat(
            [m.model_dump() for m in request.messages],
            request.fields,
        )
    except ChatConfigError as exc:
        # Not configured / key rejected (e.g. container without a valid key).
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ChatUpstreamError as exc:
        # Provider unreachable / rate-limited / timed out.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except ChatOutputError as exc:
        # Unusable model output after the service's one retry.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    # Anything else becomes FastAPI's generic 500 — no internal details leak.
