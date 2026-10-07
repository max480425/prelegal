"""AI chat service: the only module that talks to the LLM.

All LLM concerns live behind two test seams:
  - `_call_llm` (instance method) — monkeypatched in route tests so no test
    ever touches the network (repo convention: no HTTP-mocking libraries).
  - `parse_llm_content` (pure function) — unit-tested directly.

Statelessness: the client sends full history + its accumulated fields each
turn; the model returns deltas; the server merges and computes `complete`
from the actual template via TemplateParser.validate_fields, so the model
can never gate the download or blank a known value.
"""

import asyncio
import json

import litellm

from backend.services import chat_prompts
from backend.utils.config import get_settings
from backend.utils.template_parser import TemplateParser

MODEL = "openrouter/openai/gpt-oss-120b"


class ChatError(Exception):
    """Base class for chat domain errors."""


class ChatConfigError(ChatError):
    """The chat feature is not configured (missing OPENROUTER_API_KEY)."""


class ChatUpstreamError(ChatError):
    """The LLM provider failed (transport, auth, rate limit, timeout)."""


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
        messages = [
            {"role": "system", "content": chat_prompts.build_system_prompt()},
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

        fields = self._merge_fields(client_fields, raw.get("fields") or {})
        complete, _ = TemplateParser.validate_fields(self._template_content(), fields)
        return {"reply": reply, "fields": fields, "complete": complete}

    def _template_content(self) -> str:
        """The Mutual NDA template text (source of truth for completeness)."""
        return TemplateParser.load_template(
            self.settings.templates_path / "Mutual-NDA.md"
        )

    @staticmethod
    def _merge_fields(client_fields: dict, model_fields: dict) -> dict:
        """Merge model deltas over client values; always all 6 keys, stripped.

        A non-empty model value overwrites (allows corrections); an empty or
        missing model value keeps the client's known value (never blanks).
        """
        merged = {}
        for name in chat_prompts.required_field_names():
            current = str(client_fields.get(name) or "").strip()
            incoming = str(model_fields.get(name) or "").strip()
            merged[name] = incoming or current
        return merged

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
                max_tokens=1024,
                timeout=30.0,
            )
        except litellm.exceptions.AuthenticationError as exc:
            # Key present but rejected by OpenRouter → configuration problem.
            raise ChatConfigError(
                "AI chat is not configured correctly (OpenRouter rejected the API key)"
            ) from exc
        except Exception as exc:  # litellm.APIError, Timeout, RateLimit, ...
            raise ChatUpstreamError(f"AI request failed: {exc}") from exc

        return parse_llm_content(completion.choices[0].message.content)
