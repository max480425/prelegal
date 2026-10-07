"""Tests for the AI chat API (PL-5).

The LLM seam (`chat_service._call_llm`) is monkeypatched in every test that
posts /message — no test ever touches the network (repo convention: no
HTTP-mocking libraries).
"""

import asyncio

import pytest

from backend.api import chat_routes
from backend.api.chat_routes import chat_service
from backend.services import chat_prompts
from backend.services.chat_service import (
    ChatConfigError,
    ChatOutputError,
    ChatUpstreamError,
    coerce_field,
    parse_llm_content,
)
from backend.tests.conftest import NDA_FIELDS
from backend.utils.config import get_settings
from backend.utils.template_parser import TemplateParser


def _patch_llm(monkeypatch, payload=None, error=None):
    """Replace the network seam with a fake async function."""
    calls = []

    async def fake(messages):
        calls.append(messages)
        if error is not None:
            raise error
        return payload if payload is not None else _payload({})

    monkeypatch.setattr(chat_service, "_call_llm", fake)
    return calls


def _payload(fields, reply="Got it — and when should the agreement take effect?"):
    # Mirrors the real structured-output contract: reply + fields only
    # (the server computes `complete` itself).
    return {"reply": reply, "fields": fields}


def _post(client, text="We are evaluating a partnership.", fields=None):
    return client.post(
        "/api/chat/message",
        json={
            "messages": [{"role": "user", "content": text}],
            "fields": fields or {},
        },
    )


class TestGreeting:
    def test_greeting_shape_and_static_fields(self, client):
        response = client.get("/api/chat/greeting")
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"reply", "fields", "complete"}
        assert body["reply"]
        assert body["complete"] is False
        assert set(body["fields"]) == set(chat_prompts.required_field_names())
        assert all(value == "" for value in body["fields"].values())

    def test_greeting_makes_no_llm_call(self, client, monkeypatch):
        async def boom(messages):
            raise AssertionError("greeting must not call the LLM")

        monkeypatch.setattr(chat_service, "_call_llm", boom)
        assert client.get("/api/chat/greeting").status_code == 200


class TestMessage:
    def test_partial_fields_not_complete(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({"Purpose": "Partnership evaluation"}))
        body = _post(client).json()
        assert body["complete"] is False
        # Always every template key, never a partial dict.
        assert set(body["fields"]) == set(chat_prompts.required_field_names())
        assert body["fields"]["Purpose"] == "Partnership evaluation"
        assert body["fields"]["Effective Date"] == ""

    def test_all_fields_complete(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload(NDA_FIELDS))
        body = _post(client).json()
        assert body["complete"] is True
        assert body["fields"]["Governing Law"] == "California"

    def test_merge_keeps_client_value_when_model_returns_empty(
        self, client, monkeypatch
    ):
        _patch_llm(monkeypatch, _payload({name: "" for name in NDA_FIELDS}))
        body = _post(client, fields=NDA_FIELDS).json()
        assert body["fields"] == NDA_FIELDS
        assert body["complete"] is True

    def test_merge_model_value_overwrites_client(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({"Purpose": "Revised purpose"}))
        body = _post(client, fields={"Purpose": "Old purpose"}).json()
        assert body["fields"]["Purpose"] == "Revised purpose"

    def test_values_are_stripped(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({"Purpose": "  padded value  "}))
        body = _post(client).json()
        assert body["fields"]["Purpose"] == "padded value"

    def test_empty_reply_falls_back(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({}, reply="   "))
        body = _post(client).json()
        assert body["reply"].strip()

    def test_unknown_client_field_keys_are_dropped(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({}))
        response = _post(client, fields={"Not A Field": "junk"})
        assert response.status_code == 200
        assert "Not A Field" not in response.json()["fields"]

    def test_system_prompt_and_history_reach_the_llm(self, client, monkeypatch):
        calls = _patch_llm(monkeypatch, _payload({}))
        _post(client, text="We are evaluating a partnership.")
        assert len(calls) == 1
        messages = calls[0]
        assert messages[0]["role"] == "system"
        for name in chat_prompts.required_field_names():
            assert name in messages[0]["content"]
        assert {"role": "user", "content": "We are evaluating a partnership."} in messages

    def test_known_fields_are_injected_into_the_prompt(self, client, monkeypatch):
        calls = _patch_llm(monkeypatch, _payload({}))
        _post(client, fields={"Purpose": "Partnership evaluation"})
        system = calls[0][0]["content"]
        assert "Known fields so far" in system
        assert "Purpose: Partnership evaluation" in system

    def test_long_model_values_are_capped(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({"Purpose": "x" * 1500}))
        body = _post(client).json()
        assert len(body["fields"]["Purpose"]) == 1000

    def test_message_works_without_auth(self, client, monkeypatch):
        # The client fixture is signed out — chat is public by design.
        _patch_llm(monkeypatch, _payload({}))
        assert _post(client).status_code == 200


class TestCoercion:
    """Values the prompt only *advises* are enforced server-side (M3)."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("France", "Other"),
            ("california", "California"),
            ("NEW YORK", "New York"),
            ("Texas", "Texas"),
            ("", ""),
        ],
    )
    def test_governing_law_enforces_options(self, raw, expected):
        assert coerce_field("Governing Law", raw) == expected

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("2026-10-07", "2026-10-07"),   # ISO passes through
            ("May 1, 2026", "2026-05-01"),  # parseable → ISO
            ("ASAP", ""),                   # unparseable → must re-ask
            ("", ""),
        ],
    )
    def test_effective_date_normalization(self, raw, expected):
        assert coerce_field("Effective Date", raw) == expected

    def test_garbage_model_date_does_not_blank_known_value(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({"Effective Date": "ASAP"}))
        body = _post(client, fields={"Effective Date": "2024-01-15"}).json()
        assert body["fields"]["Effective Date"] == "2024-01-15"

    def test_garbage_model_date_without_known_value_stays_empty(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({"Effective Date": "ASAP"}))
        body = _post(client).json()
        assert body["fields"]["Effective Date"] == ""


class TestValidation:
    def test_empty_messages_422(self, client):
        response = client.post("/api/chat/message", json={"messages": []})
        assert response.status_code == 422

    def test_system_role_422(self, client):
        response = client.post(
            "/api/chat/message",
            json={"messages": [{"role": "system", "content": "hi"}]},
        )
        assert response.status_code == 422

    def test_empty_content_422(self, client):
        response = client.post(
            "/api/chat/message",
            json={"messages": [{"role": "user", "content": ""}]},
        )
        assert response.status_code == 422

    def test_history_count_capped_at_40(self, client):
        messages = [{"role": "user", "content": "x"} for _ in range(41)]
        response = client.post("/api/chat/message", json={"messages": messages})
        assert response.status_code == 422

    def test_history_character_budget_enforced(self, client):
        # 5 × 8000 chars = 40k > the 32k per-request budget (422 before the LLM).
        messages = [{"role": "user", "content": "x" * 8000} for _ in range(5)]
        response = client.post("/api/chat/message", json={"messages": messages})
        assert response.status_code == 422


class TestRateLimit:
    def test_rate_limit_returns_429(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({}))
        monkeypatch.setattr(chat_service.settings, "CHAT_RATE_LIMIT", 2)
        chat_routes._rate_buckets.clear()
        try:
            assert _post(client).status_code == 200
            assert _post(client).status_code == 200
            assert _post(client).status_code == 429
        finally:
            chat_routes._rate_buckets.clear()

    def test_zero_limit_disables_the_limiter(self, client, monkeypatch):
        _patch_llm(monkeypatch, _payload({}))
        assert get_settings().CHAT_RATE_LIMIT == 0  # set by conftest
        chat_routes._rate_buckets.clear()
        try:
            for _ in range(5):
                assert _post(client).status_code == 200
        finally:
            chat_routes._rate_buckets.clear()


class TestErrors:
    def test_config_error_503(self, client, monkeypatch):
        _patch_llm(monkeypatch, error=ChatConfigError("missing OPENROUTER_API_KEY"))
        assert _post(client).status_code == 503

    def test_upstream_error_502(self, client, monkeypatch):
        _patch_llm(monkeypatch, error=ChatUpstreamError("provider down"))
        assert _post(client).status_code == 502

    def test_output_error_502_after_one_retry(self, client, monkeypatch):
        calls = _patch_llm(monkeypatch, error=ChatOutputError("bad JSON"))
        assert _post(client).status_code == 502
        assert len(calls) == 2  # exactly one retry

    def test_retry_recovers_from_bad_output(self, client, monkeypatch):
        attempts = {"n": 0}

        async def flaky(messages):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise ChatOutputError("bad JSON")
            return _payload({"Purpose": "Recovered"})

        monkeypatch.setattr(chat_service, "_call_llm", flaky)
        response = _post(client)
        assert response.status_code == 200
        assert response.json()["fields"]["Purpose"] == "Recovered"

    def test_missing_api_key_raises_config_error(self, monkeypatch):
        # The REAL seam (not patched): empty key must fail fast, no network.
        monkeypatch.setattr(chat_service.settings, "OPENROUTER_API_KEY", "")
        with pytest.raises(ChatConfigError):
            asyncio.run(chat_service._call_llm([{"role": "user", "content": "hi"}]))

    def test_rejected_api_key_maps_to_config_error(self, monkeypatch):
        # OpenRouter 401 (key present but invalid) is a config problem → 503.
        import litellm

        def fake_completion(**kwargs):
            raise litellm.exceptions.AuthenticationError(
                "User not found.",
                llm_provider="openrouter",
                model="openrouter/openai/gpt-oss-120b",
            )

        monkeypatch.setattr(litellm, "completion", fake_completion)
        with pytest.raises(ChatConfigError):
            asyncio.run(chat_service._call_llm([{"role": "user", "content": "hi"}]))

    def test_empty_choices_is_an_output_error(self, monkeypatch):
        # Provider refusal → choices: [] must be a retriable 502, not a 500.
        import litellm

        class Refused:
            choices = []

        monkeypatch.setattr(litellm, "completion", lambda **kwargs: Refused())
        with pytest.raises(ChatOutputError):
            asyncio.run(chat_service._call_llm([{"role": "user", "content": "hi"}]))

    def test_upstream_failures_do_not_leak_details(self, monkeypatch):
        # Raw provider bodies stay in the server log; the client sees a
        # generic message.
        import litellm

        def explode(**kwargs):
            raise RuntimeError("https://internal.example/secret-body")

        monkeypatch.setattr(litellm, "completion", explode)
        with pytest.raises(ChatUpstreamError) as exc_info:
            asyncio.run(chat_service._call_llm([{"role": "user", "content": "hi"}]))
        assert "secret-body" not in str(exc_info.value)
        assert "could not complete" in str(exc_info.value)


class TestDriftGuards:
    """The prompt, JSON schema, and template must never disagree on fields."""

    def test_output_schema_keys_match_predefined_fields(self):
        schema = chat_prompts.build_output_schema()
        assert list(schema["properties"]["fields"]["properties"]) == list(
            TemplateParser.PREDEFINED_FIELDS
        )
        assert schema["properties"]["fields"]["required"] == list(
            TemplateParser.PREDEFINED_FIELDS
        )

    def test_template_spans_match_predefined_fields(self):
        content = TemplateParser.load_template(
            get_settings().templates_path / "Mutual-NDA.md"
        )
        spans = list(dict.fromkeys(TemplateParser.extract_fields(content)))
        assert spans == list(TemplateParser.PREDEFINED_FIELDS)

    def test_system_prompt_mentions_every_field(self):
        prompt = chat_prompts.build_system_prompt()
        for name in TemplateParser.PREDEFINED_FIELDS:
            assert name in prompt


class TestParseLlmContent:
    def test_valid_dict_passes_through(self):
        data = {"reply": "hello", "fields": {}}
        assert parse_llm_content(data) is data

    def test_valid_json_string_parses(self):
        assert parse_llm_content('{"reply": "hi", "fields": {}}') == {
            "reply": "hi",
            "fields": {},
        }

    @pytest.mark.parametrize("content", ["", "not json", "{truncated", None])
    def test_invalid_json_raises(self, content):
        with pytest.raises(ChatOutputError):
            parse_llm_content(content)

    @pytest.mark.parametrize(
        "content",
        [
            {"reply": 42, "fields": {}},      # reply not a string
            {"reply": "hi", "fields": []},    # fields not a dict
            {"reply": "hi"},                  # missing fields
            {"fields": {}},                   # missing reply
            ["not", "an", "object"],
        ],
    )
    def test_wrong_shape_raises(self, content):
        with pytest.raises(ChatOutputError):
            parse_llm_content(content)
