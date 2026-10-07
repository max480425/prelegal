from pydantic import BaseModel, Field
from typing import Dict, List, Literal


class ChatMessage(BaseModel):
    """A single conversational turn sent by the client."""
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatMessageRequest(BaseModel):
    """POST /api/chat/message payload.

    The conversation is stateless on the server: the client sends the full
    history plus its accumulated `fields`, so the model only has to return
    deltas and can never blank a value it forgets to restate.

    History is capped (public endpoint — unbounded history would mean
    unbounded LLM cost); the route additionally bounds total characters.
    """
    messages: List[ChatMessage] = Field(min_length=1, max_length=40)
    fields: Dict[str, str] = Field(default_factory=dict)


class ChatTurnResponse(BaseModel):
    """Response for both GET /api/chat/greeting and POST /api/chat/message.

    `fields` always carries every template field key ("" when not yet known),
    `complete` is computed server-side from the template's required fields.
    """
    reply: str
    fields: Dict[str, str]
    complete: bool
