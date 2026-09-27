import argparse
import json
import statistics
import time
from pathlib import Path


def benchmark(guard, queries: list[str], repeats: int = 1) -> dict:
    values = []
    for _ in range(repeats):
        for query in queries:
            started = time.perf_counter()
            guard.classify(query)
            values.append((time.perf_counter() - started) * 1000)
    values.sort()
    percentile = lambda p: values[min(len(values) - 1, int(len(values) * p))]
    return {"count": len(values), "mean_ms": statistics.mean(values), "p50_ms": percentile(.50), "p95_ms": percentile(.95), "p99_ms": percentile(.99)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use benchmark(guard, queries) from an initialized application.")
    parser.parse_args()
    parser.error("Initialize FashionGuard in application code and call benchmark().")
