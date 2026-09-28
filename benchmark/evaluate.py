"""Honest, leakage-aware evaluation for a Fashion Guard model run.

Unlike the previous ad-hoc notebook aggregation, this module:

* Never trusts pre-computed ``*_match`` columns from a results file; it
  recomputes every match from ``expected_intent``/``expected_route`` in the
  case file against the model's own ``intent``/``route`` output.
* Skips every case with ``requires_expert_review`` entirely (reports the
  count separately instead of scoring a guess).
* Splits accuracy into gate-resolved vs. model-resolved using the
  ``expected_resolution_path`` computed by ``benchmark.cases`` from the real
  gate functions, not from parsing ``raw_output`` strings after the fact.
* Flags a run as invalid (and keeps it out of the headline table) when more
  than half of its model-resolved cases are a ``model_error:*`` failure,
  instead of silently averaging a crashed run in with working ones.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

INVALID_RUN_ERROR_THRESHOLD = 0.5


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_results(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        return load_jsonl(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _to_bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


@dataclass
class CaseEvaluation:
    case_id: str
    language: str
    category: str
    expected_intent: str | None
    expected_route: str | None
    expected_resolution_path: str | None
    predicted_intent: str | None
    predicted_route: str | None
    raw_output: str
    latency_ms: float | None
    intent_match: bool | None
    route_match: bool | None
    is_model_error: bool
    skipped_reason: str | None


def evaluate_case(case: dict, result: dict | None) -> CaseEvaluation:
    if case.get("requires_expert_review"):
        return CaseEvaluation(
            case_id=case["case_id"], language=case["language"], category=case["category"],
            expected_intent=None, expected_route=None, expected_resolution_path=None,
            predicted_intent=result.get("intent") if result else None,
            predicted_route=result.get("route") if result else None,
            raw_output=result.get("raw_output", "") if result else "",
            latency_ms=float(result["latency_ms"]) if result and result.get("latency_ms") not in (None, "") else None,
            intent_match=None, route_match=None, is_model_error=False,
            skipped_reason="requires_expert_review",
        )
    if result is None:
        return CaseEvaluation(
            case_id=case["case_id"], language=case["language"], category=case["category"],
            expected_intent=case.get("expected_intent"), expected_route=case.get("expected_route"),
            expected_resolution_path=case.get("expected_resolution_path"),
            predicted_intent=None, predicted_route=None, raw_output="", latency_ms=None,
            intent_match=None, route_match=None, is_model_error=False,
            skipped_reason="missing_result",
        )
    raw_output = str(result.get("raw_output", ""))
    predicted_intent = result.get("intent")
    predicted_route = result.get("route")
    is_model_error = raw_output.startswith("model_error:")
    intent_match = predicted_intent == case.get("expected_intent") if case.get("expected_intent") else None
    route_match = predicted_route == case.get("expected_route") if case.get("expected_route") else None
    latency = result.get("latency_ms")
    return CaseEvaluation(
        case_id=case["case_id"], language=case["language"], category=case["category"],
        expected_intent=case.get("expected_intent"), expected_route=case.get("expected_route"),
        expected_resolution_path=case.get("expected_resolution_path"),
        predicted_intent=predicted_intent, predicted_route=predicted_route,
        raw_output=raw_output, latency_ms=float(latency) if latency not in (None, "") else None,
        intent_match=intent_match, route_match=route_match, is_model_error=is_model_error,
        skipped_reason=None,
    )


def _accuracy(evaluations: list[CaseEvaluation], field: str) -> float | None:
    values = [getattr(evaluation, field) for evaluation in evaluations if getattr(evaluation, field) is not None]
    return round(100 * sum(values) / len(values), 1) if values else None


def summarize(model_key: str, model_name: str, evaluations: list[CaseEvaluation]) -> dict:
    scored = [e for e in evaluations if e.skipped_reason is None]
    pending_expert = [e for e in evaluations if e.skipped_reason == "requires_expert_review"]
    missing = [e for e in evaluations if e.skipped_reason == "missing_result"]
    gate_resolved = [e for e in scored if (e.expected_resolution_path or "").startswith("gate:")]
    model_resolved = [e for e in scored if e.expected_resolution_path == "model"]
    model_errors = [e for e in model_resolved if e.is_model_error]

    error_rate = len(model_errors) / len(model_resolved) if model_resolved else 0.0
    is_invalid = error_rate > INVALID_RUN_ERROR_THRESHOLD

    confusion = Counter((e.expected_intent, e.predicted_intent) for e in model_resolved if not e.is_model_error)

    per_language = defaultdict(list)
    for e in model_resolved:
        per_language[e.language].append(e)
    per_language_accuracy = {
        language: {"n": len(items), "intent_accuracy": _accuracy(items, "intent_match")}
        for language, items in sorted(per_language.items())
    }

    per_category = defaultdict(list)
    for e in scored:
        per_category[e.category].append(e)
    per_category_accuracy = {
        category: {"n": len(items), "route_accuracy": _accuracy(items, "route_match")}
        for category, items in sorted(per_category.items())
    }

    latencies = sorted(e.latency_ms for e in evaluations if e.latency_ms is not None)
    percentile = (lambda p: latencies[min(len(latencies) - 1, int(len(latencies) * p))]) if latencies else (lambda p: None)

    return {
        "model_key": model_key,
        "model_name": model_name,
        "total_cases": len(evaluations),
        "scored_cases": len(scored),
        "pending_expert_review": len(pending_expert),
        "missing_results": len(missing),
        "gate_resolved_cases": len(gate_resolved),
        "model_resolved_cases": len(model_resolved),
        "model_error_cases": len(model_errors),
        "model_error_rate": round(100 * error_rate, 1),
        "is_invalid_run": is_invalid,
        "gate_route_accuracy": _accuracy(gate_resolved, "route_match"),
        "model_route_accuracy": _accuracy(model_resolved, "route_match"),
        "model_intent_accuracy": _accuracy(model_resolved, "intent_match"),
        "overall_route_accuracy": _accuracy(scored, "route_match"),
        "overall_intent_accuracy": _accuracy(scored, "intent_match"),
        "unexpected_search": sum(
            1 for e in scored
            if e.expected_route != "SEARCH" and e.predicted_route == "SEARCH"
        ),
        "per_language_intent_accuracy": per_language_accuracy,
        "per_category_route_accuracy": per_category_accuracy,
        "confusion_matrix": {f"{expected}->{predicted}": count for (expected, predicted), count in confusion.items()},
        "latency_mean_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
        "latency_p50_ms": percentile(0.50),
        "latency_p95_ms": percentile(0.95),
    }


def run(cases_path: Path, results_path: Path) -> dict:
    cases = {case["case_id"]: case for case in load_jsonl(cases_path)}
    results = load_results(results_path)
    results_by_case = {row["case_id"]: row for row in results}
    model_key = results[0].get("model_key", "unknown") if results else "unknown"
    model_name = results[0].get("model_name", "unknown") if results else "unknown"

    unknown_result_ids = set(results_by_case) - set(cases)
    if unknown_result_ids:
        raise ValueError(f"Results reference {len(unknown_result_ids)} case_id(s) absent from {cases_path}")

    evaluations = [evaluate_case(case, results_by_case.get(case_id)) for case_id, case in cases.items()]
    return summarize(model_key, model_name, evaluations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.jsonl"))
    parser.add_argument("--results", type=Path, required=True, help="CSV or JSONL with case_id, intent, route, raw_output, latency_ms")
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON summary")
    args = parser.parse_args()
    summary = run(args.cases, args.results)
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
