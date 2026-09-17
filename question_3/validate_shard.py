import csv
import json
import os
import re
import socket
import sys
import time

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
REQUIRED_FIELDS = ["user_id", "email", "signup_date", "country"]


def row_problems(row):
    problems = []
    for field in REQUIRED_FIELDS:
        if not (row.get(field) or "").strip():
            problems.append(f"missing:{field}")
    email = (row.get("email") or "").strip()
    if email and not EMAIL_RE.match(email):
        problems.append("bad_email")
    return problems


def main():
    index = int(os.environ.get("JOB_COMPLETION_INDEX", "0"))
    shard_dir = os.environ.get("SHARD_DIR", "/app/data/shards")
    pod_name = os.environ.get("POD_NAME", socket.gethostname())
    node_name = os.environ.get("NODE_NAME", "unknown")
    hold = float(os.environ.get("HOLD_SECONDS", "20"))

    shard_path = os.path.join(shard_dir, f"shard_{index:02d}.csv")
    print(f"pod {index} on {node_name} validating {shard_path}", flush=True)

    if not os.path.exists(shard_path):
        print(f"FATAL: {shard_path} not found", file=sys.stderr, flush=True)
        sys.exit(1)

    started = time.time()
    total = invalid = 0
    reasons = {}

    with open(shard_path, newline="") as fh:
        for row in csv.DictReader(fh):
            total += 1
            problems = row_problems(row)
            if problems:
                invalid += 1
                for prob in problems:
                    reasons[prob] = reasons.get(prob, 0) + 1

    result = {
        "completion_index": index,
        "shard": os.path.basename(shard_path),
        "rows_total": total,
        "rows_invalid": invalid,
        "invalid_reasons": reasons,
        "validate_seconds": round(time.time() - started, 3),
        "pod_name": pod_name,
        "node_name": node_name,
    }
    print("RESULT_JSON:" + json.dumps(result), flush=True)

    if hold > 0:
        time.sleep(hold)
    print(f"pod {index} done", flush=True)


if __name__ == "__main__":
    main()
