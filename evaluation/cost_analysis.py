import argparse
import json


def compare(total_requests: int, fashion_rate: float, guard_cost: float, agent_cost: float, guard_fashion_recall: float = 1.0) -> dict:
    without_guard = total_requests * agent_cost
    routed_to_agent = total_requests * (fashion_rate * guard_fashion_recall + (1 - fashion_rate) * 0)
    with_guard = total_requests * guard_cost + routed_to_agent * agent_cost
    return {"total_requests": total_requests, "fashion_rate": fashion_rate, "without_guard_cost": without_guard, "with_guard_cost": with_guard, "saving_percent": (without_guard - with_guard) / without_guard * 100 if without_guard else 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=10000)
    parser.add_argument("--fashion-rate", type=float, default=.8)
    parser.add_argument("--guard-cost", type=float, default=1.)
    parser.add_argument("--agent-cost", type=float, default=10.)
    args = parser.parse_args()
    print(json.dumps(compare(args.requests, args.fashion_rate, args.guard_cost, args.agent_cost), indent=2))
