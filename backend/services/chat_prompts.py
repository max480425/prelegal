"""Everything the LLM sees: greeting, system prompt, structured-output schema.

Pure functions with no I/O and no litellm import. All field metadata is
derived from TemplateParser.PREDEFINED_FIELDS (the same source the template
schema endpoint and PDF validation use) so the prompt, the JSON schema, the
preview keys, and the actual template spans cannot drift apart.
"""

from typing import Dict, List

from backend.utils.template_parser import TemplateParser

# Static greeting: free, instant, deterministic to test, and works even when
# the API key is missing — the model only takes over once the user speaks.
GREETING = (
    "Hi! I'm your AI paralegal. I'll help you put together a Mutual NDA by "
    "asking a few short questions, one at a time, and filling in the document "
    "as we go. To get started: what is the purpose of sharing confidential "
    "information between the parties?"
)

_FIELD_ORDER: List[str] = list(TemplateParser.PREDEFINED_FIELDS)


def _field_line(name: str) -> str:
    """Render one field's guidance for the system prompt / schema description."""
    spec = TemplateParser.PREDEFINED_FIELDS[name]
    parts = [spec.get("description", f"Value for {name}")]
    if spec.get("placeholder"):
        parts.append(f"e.g. '{spec['placeholder']}'")
    if spec.get("options"):
        parts.append(
            "exactly one of: " + " | ".join(spec["options"]) + "; if another "
            "value is given, use 'Other' and say so in your reply"
        )
    if spec.get("type") == "date":
        parts.append("always formatted as YYYY-MM-DD")
    return f"  {name} — " + "; ".join(parts)


def build_system_prompt() -> str:
    """System prompt instructing conversational field extraction."""
    field_lines = "\n".join(_field_line(name) for name in _FIELD_ORDER)
    order = ", ".join(_FIELD_ORDER)
    return (
        "You are a friendly legal assistant helping a user complete a Mutual "
        "Non-Disclosure Agreement (Mutual NDA).\n"
        "Collect these required fields (the exact keys of your `fields` "
        "output; an empty string means not yet known):\n"
        f"{field_lines}\n"
        "Rules:\n"
        f"- Ask about ONE field per turn, in this order: {order}.\n"
        "- Extract everything the user gives you; never re-ask for a field "
        "that already has a value, and never clear a value you already know.\n"
        "- Infer only when unambiguous (relative dates → absolute YYYY-MM-DD); "
        "otherwise ask. Never invent values.\n"
        "- When every field has a value, your reply must briefly confirm the "
        "document is complete and ready to download; ask nothing further.\n"
        "- Keep replies to 1-3 sentences. You draft documents; do not give "
        "legal advice. Politely redirect unrelated requests back to the NDA."
    )


def build_output_schema() -> Dict:
    """Structured-output JSON schema: every field key always present, string
    values with '' for unknown (maximally provider-compatible under
    strict mode — no null unions, no enums that would forbid '')."""
    properties = {}
    for name in _FIELD_ORDER:
        properties[name] = {
            "type": "string",
            "description": _field_line(name).split(" — ", 1)[1],
        }
    return {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": "Conversational reply to the user, 1-3 sentences",
            },
            "fields": {
                "type": "object",
                "properties": properties,
                "required": list(_FIELD_ORDER),
                "additionalProperties": False,
            },
        },
        "required": ["reply", "fields"],
        "additionalProperties": False,
    }


def required_field_names() -> List[str]:
    """The exact template field names, in template order."""
    return list(_FIELD_ORDER)
