"""AI chat service: the only module that talks to the LLM.

All LLM concerns live behind two test seams:
  - `_call_llm` (instance method) — monkeypatched in route tests so no test
    ever touches the network (repo convention: no HTTP-mocking libraries).
  - `parse_llm_content` (pure function) — unit-tested directly.

Statelessness: the client sends full history + its accumulated fields each
turn; the model returns deltas; the server coerces and merges them and
computes `complete` from the actual template via TemplateParser.validate_fields,
so the model can never gate the download, blank a known value, or push
invalid data (bad dates, non-option governing law) into the document.
"""

import asyncio
import json
import logging
import re
from typing import Dict

import litellm
from dateutil import parser as date_parser

from backend.services import chat_prompts
from backend.utils.config import get_settings
from backend.utils.template_parser import TemplateParser, FieldType

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"
# Per-field cap on merged values: bounds prompt/output size so the strict
# schema re-emission always fits the token budget (prevents a truncation
# loop where a huge value makes every turn fail with invalid JSON).
MAX_FIELD_CHARS = 1000
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ChatError(Exception):
    """Base class for chat domain errors."""


class ChatConfigError(ChatError):
    """The chat feature is not configured (missing/rejected OPENROUTER_API_KEY)."""


class ChatUpstreamError(ChatError):
    """The LLM provider failed (transport, rate limit, timeout)."""


class ChatOutputError(ChatError):
    """The LLM returned unusable output (bad JSON / wrong shape)."""


def parse_llm_content(content) -> dict:
    """Parse and shape-check the model's structured output.

    Accepts a dict (some providers return parsed objects) or a JSON string.
    Raises ChatOutputError for anything that isn't {reply: str, fields: dict}.
    """
    if isinstance(content, dict):
        data = content
    else:
        try:
            data = json.loads(content or "")
        except (TypeError, json.JSONDecodeError) as exc:
            raise ChatOutputError("AI returned invalid JSON") from exc

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("reply"), str)
        or not isinstance(data.get("fields"), dict)
    ):
        raise ChatOutputError("AI returned an unexpected response shape")
    return data


def coerce_field(name: str, value) -> str:
    """Normalize one field value: strip, cap length, and enforce the rules
    the prompt only advises (so garbage never reaches the PDF).

    - Governing Law: any non-option value (e.g. 'France') → 'Other'.
    - Effective Date: ISO kept as-is; other parseable dates → YYYY-MM-DD;
      unparseable values → '' (the AI must ask again).
    """
    text = str(value or "").strip()[:MAX_FIELD_CHARS]
    if not text:
        return ""

    spec = TemplateParser.PREDEFINED_FIELDS.get(name, {})
    if name == "Governing Law":
        options = spec.get("options") or []
        if text not in options:
            match = next((o for o in options if o.lower() == text.lower()), None)
            return match or "Other"
        return text

    if spec.get("type") == FieldType.DATE and not _ISO_DATE.match(text):
        try:
            parsed = date_parser.parse(text)
        except (ValueError, OverflowError, TypeError):
            return ""
        if parsed is None or not (2020 <= parsed.year <= 2099):
            return ""
        return parsed.strftime("%Y-%m-%d")
    return text


def coerce_fields(raw: Dict) -> Dict[str, str]:
    """Coerce a fields dict down to exactly the template's field names."""
    return {
        name: coerce_field(name, (raw or {}).get(name))
        for name in chat_prompts.required_field_names()
    }


class ChatService:
    """Conversation turn handling for the Mutual NDA chat."""

    def __init__(self):
        self.settings = get_settings()

    def greeting(self) -> dict:
        """Static greeting — same response shape as a chat turn."""
        return {
            "reply": chat_prompts.GREETING,
            "fields": {name: "" for name in chat_prompts.required_field_names()},
            "complete": False,
        }

    async def chat(self, history: list, client_fields: dict) -> dict:
        """Run one conversational turn and return {reply, fields, complete}.

        `history` is the full client-side conversation as plain dicts;
        `client_fields` is the client's accumulated field values.
        """
        known = coerce_fields(client_fields)
        messages = [
            {"role": "system", "content": chat_prompts.build_system_prompt(known)},
            *history,
        ]

        # One automatic retry absorbs a rare malformed structured output
        # before surfacing 502 to the user.
        for attempt in range(2):
            try:
                raw = await self._call_llm(messages)
                break
            except ChatOutputError:
                if attempt == 1:
                    raise

        reply = str(raw.get("reply") or "").strip()
        if not reply:
            reply = "Sorry, could you rephrase that?"

        # Model deltas are coerced BEFORE merging: a delta that normalizes to
        # '' (garbage date, etc.) keeps the known value instead of blanking it.
        deltas = coerce_fields(raw.get("fields") or {})
        fields = {name: deltas[name] or known[name] for name in known}
        complete, _ = TemplateParser.validate_fields(self._template_content(), fields)
        return {"reply": reply, "fields": fields, "complete": complete}

    def _template_content(self) -> str:
        """The Mutual NDA template text (source of truth for completeness)."""
        return TemplateParser.load_template(
            self.settings.templates_path / "Mutual-NDA.md"
        )

    async def _call_llm(self, messages: list) -> dict:
        """THE network seam. Returns the parsed structured-output dict."""
        api_key = self.settings.OPENROUTER_API_KEY
        if not api_key:
            raise ChatConfigError("AI chat is not configured (missing OPENROUTER_API_KEY)")
        try:
            # Sync completion off the event loop: litellm's async transport
            # (aiohttp) hits DNS resolver failures on some Windows setups,
            # while the sync path is reliable — and the thread keeps the
            # route non-blocking either way.
            completion = await asyncio.to_thread(
                litellm.completion,
                model=MODEL,
                api_key=api_key,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "nda_chat_turn",
                        "strict": True,
                        "schema": chat_prompts.build_output_schema(),
                    },
                },
                # Prefer Cerebras as the inference provider; fall back to
                # other OpenRouter providers if it is unavailable.
                extra_body={"provider": {"order": ["cerebras"], "allow_fallbacks": True}},
                temperature=0.2,
                # Budget for the reply PLUS a full strict-schema re-emission
                # of all six fields (short, capped at MAX_FIELD_CHARS each).
                max_tokens=4096,
                timeout=30.0,
            )
        except litellm.exceptions.AuthenticationError as exc:
            # Key present but rejected by OpenRouter → configuration problem.
            logger.warning("OpenRouter rejected the API key: %s", exc)
            raise ChatConfigError(
                "AI chat is not configured correctly (OpenRouter rejected the API key)"
            ) from exc
        except Exception as exc:  # litellm.APIError, Timeout, RateLimit, ...
            # Full detail stays in the server log; the client gets a generic
            # message so provider response bodies never leak to callers.
            logger.warning("LLM request failed: %s", exc)
            raise ChatUpstreamError("The AI provider could not complete the request") from exc

        if not completion.choices:
            raise ChatOutputError("AI returned no choices")
        return parse_llm_content(completion.choices[0].message.content)
