import argparse
import json
import re
import sys

import pandas as pd
from kubernetes import client, config

RESULT_RE = re.compile(r"RESULT_JSON:(\{.*\})")


def collect(job_name, namespace="default"):
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=f"job-name={job_name}")

    rows = []
    for pod in pods.items:
        pod_name = pod.metadata.name
        try:
            logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        except client.exceptions.ApiException as e:
            print(f"could not read logs for {pod_name}: {e.reason}", file=sys.stderr)
            continue
        match = RESULT_RE.search(logs)
        if not match:
            print(f"no RESULT_JSON in {pod_name} yet", file=sys.stderr)
            continue
        result = json.loads(match.group(1))
        result["invalid_reasons"] = json.dumps(result["invalid_reasons"])
        result["pod_phase"] = pod.status.phase
        rows.append(result)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("completion_index").reset_index(drop=True)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-name", default="shard-validation")
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--truth", default="data/shards/ground_truth.json")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    df = collect(args.job_name, args.namespace)
    if df.empty:
        print("No results collected.")
        raise SystemExit(1)

    pd.set_option("display.width", 160)
    print(df[["completion_index", "shard", "rows_total", "rows_invalid",
              "validate_seconds", "pod_name", "node_name"]].to_string(index=False))

    print("\nTotal invalid rows across all shards:", int(df["rows_invalid"].sum()))
    print("Distinct nodes that ran work:", sorted(df["node_name"].unique()))

    with open(args.truth) as fh:
        truth = json.load(fh)
    mismatches = [
        (r.shard, r.rows_invalid, truth[r.shard.replace(".csv", "")]["invalid"])
        for r in df.itertuples()
        if r.rows_invalid != truth[r.shard.replace(".csv", "")]["invalid"]
    ]
    print("Ground-truth check:", "ALL MATCH" if not mismatches else mismatches)

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"wrote {args.out}")
