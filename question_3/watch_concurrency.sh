#!/usr/bin/env bash
set -u
JOB="shard-validation"
OUT="concurrency.txt"

MAX=0
BEST=""
: > "$OUT"

for _ in $(seq 1 400); do
  SNAP=$(kubectl get pods -l job-name="$JOB" -o wide --no-headers 2>/dev/null)
  [ -z "$SNAP" ] && { sleep 0.5; continue; }

  RUNNING=$(printf '%s\n' "$SNAP" | grep -c 'Running')
  DONE=$(printf '%s\n' "$SNAP" | grep -c 'Completed')
  printf '%s  running=%s completed=%s\n' "$(date +%T)" "$RUNNING" "$DONE" | tee -a "$OUT"

  if [ "$RUNNING" -gt "$MAX" ]; then MAX="$RUNNING"; BEST="$SNAP"; fi
  [ "$DONE" -ge 8 ] && break
  sleep 0.5
done

{
  echo
  echo "MAX CONCURRENT Running pods observed: $MAX"
  echo "$BEST"
} | tee -a "$OUT"
