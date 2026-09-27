import argparse
import json
import statistics
import time
from pathlib import Path

from fashion_guard_deployment.fashion_guard import FashionGuard
from fashion_guard_deployment.fashion_guard.model import QwenGuardModel


def load_queries(path: Path, limit: int | None = None) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[:limit] if limit else rows


def run(dataset: Path, output: Path, model_name: str, limit: int | None = None) -> dict:
    guard = FashionGuard(model=QwenGuardModel(model_name))
    rows = load_queries(dataset, limit)
    latencies = []
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            started = time.perf_counter()
            result = guard.classify(row["query"])
            latencies.append((time.perf_counter() - started) * 1000)
            handle.write(json.dumps({"id": row["id"], "label": result.label, "language": result.language, "latency_ms": result.latency_ms, "raw_output": result.raw_output}, ensure_ascii=False) + "\n")
    if not latencies:
        return {"rows": 0, "model": model_name, "mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
    latencies.sort()
    percentile = lambda p: latencies[min(len(latencies) - 1, int(len(latencies) * p))]
    return {"rows": len(rows), "model": model_name, "mean_ms": statistics.mean(latencies), "p50_ms": percentile(.50), "p95_ms": percentile(.95), "p99_ms": percentile(.99)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/synthetic_dataset.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/predictions.jsonl"))
    parser.add_argument("--model-name", default="Qwen/Qwen3-4B-Instruct-2507")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(json.dumps(run(args.dataset, args.output, args.model_name, args.limit), indent=2))
