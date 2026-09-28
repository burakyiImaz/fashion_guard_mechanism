"""Run the benchmark cases against an already-constructed FashionGuard.

Kept separate from model loading so it has no torch/GPU dependency itself and
can be fully exercised offline with a fake model (see
``tests/test_benchmark_runner.py``). Intended Kaggle usage, once ``guard``,
``SELECTED_MODEL`` and ``MODEL_NAME`` already exist in the notebook session::

    from benchmark.cases import build_cases
    from benchmark.runner import run_benchmark, write_results

    records = run_benchmark(guard, SELECTED_MODEL, MODEL_NAME)
    write_results(OUTPUT_DIR / f"benchmark_v3_results_{SELECTED_MODEL}.csv", records)

Known, intentional scope limit: for the six guard-supported languages, cases
still pass ``session_language`` explicitly (matching the prior benchmark's
scope of measuring intent classification, not language detection).
``unsupported_language`` cases deliberately do NOT pass ``session_language``,
so the guard's own ``LanguageDetector`` must recognise the language is
unsupported by itself; the previous benchmark never exercised this path.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from fashion_guard_deployment.fashion_guard.language import SUPPORTED_LANGUAGES

DEFAULT_CASES_PATH = Path(__file__).with_name("cases.jsonl")
RESULT_FIELDS = [
    "case_id", "language", "category", "difficulty", "query", "expected_intent",
    "expected_route", "expected_resolution_path", "requires_expert_review",
    "intent", "route", "language_detected", "latency_ms", "raw_output",
    "model_key", "model_name",
]


def load_cases(path: Path = DEFAULT_CASES_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _route_name(intent: str, route_or_response: str) -> str:
    if route_or_response == "SEARCH":
        return "SEARCH"
    return "NEEDS_MORE_DETAIL" if intent == "nothing_to_search" else "REJECT"


def run_benchmark(guard, model_key: str, model_name: str, cases: list[dict] | None = None) -> list[dict]:
    cases = cases if cases is not None else load_cases()
    records = []
    for case in cases:
        if not case.get("query"):
            continue  # policy-only placeholders (no query text) cannot be run
        session_language = case["language"] if case["language"] in SUPPORTED_LANGUAGES else None
        context = [case["context"]] if case.get("context") else None
        started = time.perf_counter()
        route_or_response, result = guard.route(
            case["query"],
            context=context,
            session_language=session_language,
            awaiting_clarification=bool(case.get("awaiting_clarification")),
            request_id=case["case_id"],
            session_id="benchmark-v3",
        )
        elapsed_ms = getattr(result, "latency_ms", None)
        if elapsed_ms is None:
            elapsed_ms = (time.perf_counter() - started) * 1000
        records.append({
            "case_id": case["case_id"],
            "language": case["language"],
            "category": case["category"],
            "difficulty": case.get("difficulty", ""),
            "query": case["query"],
            "expected_intent": case.get("expected_intent") or "",
            "expected_route": case.get("expected_route") or "",
            "expected_resolution_path": case.get("expected_resolution_path") or "",
            "requires_expert_review": bool(case.get("requires_expert_review")),
            "intent": result.intent,
            "route": _route_name(result.intent, route_or_response),
            "language_detected": result.language,
            "latency_ms": round(elapsed_ms, 2),
            "raw_output": result.raw_output,
            "model_key": model_key,
            "model_name": model_name,
        })
    return records


def write_results(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(records)
