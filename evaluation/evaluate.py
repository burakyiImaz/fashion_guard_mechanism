import argparse
import json
from collections import Counter
from pathlib import Path

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

EVALUATION_LABELS = ("IN_DOMAIN", "OUT_OF_DOMAIN", "UNCERTAIN")


def evaluate(rows: list[dict], predictions: list[str]) -> dict:
    truth = [row["label"] for row in rows]
    binary_truth = [label == "IN_DOMAIN" for label in truth]
    binary_pred = [label == "IN_DOMAIN" for label in predictions]
    matrix = confusion_matrix(binary_truth, binary_pred, labels=[False, True]).tolist()
    fashion = sum(binary_truth)
    rejected_fashion = sum(t and p == "OUT_OF_DOMAIN" for t, p in zip(binary_truth, predictions))
    out_predictions = sum(p == "OUT_OF_DOMAIN" for p in predictions)
    return {
        "accuracy": accuracy_score(truth, predictions),
        "macro_f1": f1_score(truth, predictions, labels=EVALUATION_LABELS, average="macro", zero_division=0),
        "fashion_recall": recall_score(binary_truth, binary_pred, zero_division=0),
        "ood_precision": precision_score([not value for value in binary_truth], [not value for value in binary_pred], zero_division=0),
        "false_rejection_rate": rejected_fashion / fashion if fashion else 0,
        "uncertain_rate": sum(p == "UNCERTAIN" for p in predictions) / len(predictions),
        "confusion_matrix": matrix,
        "label_counts": dict(Counter(predictions)),
        "rows": len(rows),
        "out_decision_rate": out_predictions / len(predictions),
    }


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate saved JSON predictions.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path, default=Path("evaluation/metrics.json"))
    args = parser.parse_args()
    result = evaluate(load_jsonl(args.dataset), [json.loads(line)["label"] for line in args.predictions.read_text().splitlines()])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
