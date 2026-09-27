import json
import re
from typing import Literal

GuardIntent = Literal[
    "product_search",
    "clarify_answer",
    "out_of_scope",
    "styling_request",
    "unsupported_language",
    "blocked_topic",
    "nothing_to_search",
    "customer_service",
    "price_or_discount",
    "unsafe_or_injection",
]
VALID_INTENTS = {
    "product_search",
    "clarify_answer",
    "out_of_scope",
    "styling_request",
    "unsupported_language",
    "blocked_topic",
    "nothing_to_search",
    "customer_service",
    "price_or_discount",
    "unsafe_or_injection",
}


def parse_guard_output(text: str) -> GuardIntent:
    """Parse strict JSON, tolerating a single fenced/embedded JSON object."""
    if not isinstance(text, str):
        return "nothing_to_search"
    candidates = [text.strip()]
    candidates.extend(re.findall(r"\{[^{}]*\}", text))
    for candidate in candidates:
        try:
            intent = json.loads(candidate).get("intent")
        except (json.JSONDecodeError, AttributeError):
            continue
        if intent in VALID_INTENTS:
            return intent
    return "nothing_to_search"
