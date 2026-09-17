import argparse
import json
import statistics
import time

import requests

TEMPLATES = [
    "WIN a FREE iPhone now! Click here: bit.ly/xyz123 ref={i}",
    "Hey, are we still meeting for lunch on Friday? note={i}",
    "URGENT: Your account will be suspended. Verify at win-now.co/claim id={i}",
    "Thanks for helping with the project meeting yesterday, item {i}",
]


def run_phase(url, messages, label):
    handler_ms, statuses = [], {"HIT": 0, "MISS": 0, "OFF": 0}
    for msg in messages:
        r = requests.post(url, json={"text": msg}, timeout=10)
        r.raise_for_status()
        statuses[r.headers.get("X-Cache", "OFF")] += 1
        handler_ms.append(float(r.headers["X-Handler-Ms"]))

    summary = {
        "phase": label,
        "n": len(messages),
        "cache_header_counts": statuses,
        "handler_mean_ms": round(statistics.mean(handler_ms), 4),
        "handler_median_ms": round(statistics.median(handler_ms), 4),
    }
    print(json.dumps(summary, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000/predict")
    p.add_argument("--n", type=int, default=200)
    args = p.parse_args()

    messages = [TEMPLATES[i % len(TEMPLATES)].format(i=i) for i in range(args.n)]

    requests.post(args.url, json={"text": "warmup"}, timeout=10)

    print("\nPHASE A - cold cache, every request a MISS")
    miss = run_phase(args.url, messages, "miss")

    print("\nPHASE B - warm cache, every request a HIT")
    hit = run_phase(args.url, messages, "hit")

    print("\nRESULT")
    print(f"handler median: {miss['handler_median_ms']} ms (miss) "
          f"vs {hit['handler_median_ms']} ms (hit) "
          f"= {miss['handler_median_ms'] / hit['handler_median_ms']:.2f}x faster")


if __name__ == "__main__":
    main()
