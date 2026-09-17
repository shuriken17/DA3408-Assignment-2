import csv
import json
import os
import random

COUNTRIES = ["IN", "US", "GB", "DE", "SG", "AU"]
DOMAINS = ["example.com", "mail.co.in", "uni.edu", "corp.io"]
FIELDS = ["user_id", "email", "signup_date", "country"]
CORRUPTIONS = ["drop_at", "double_dot", "trailing_dot", "blank_date", "blank_country"]


def invalid_count_for(shard_id):
    return 5 + (shard_id * 7) % 13


def build_shard(shard_id, n_rows):
    rng = random.Random(1000 + shard_id)
    n_invalid = invalid_count_for(shard_id)
    corrupt_at = set(rng.sample(range(n_rows), n_invalid))

    rows = []
    for i in range(n_rows):
        row = {
            "user_id": f"u{shard_id:02d}-{i:06d}",
            "email": f"user{i}@{rng.choice(DOMAINS)}",
            "signup_date": f"2026-{rng.randint(1, 9):02d}-{rng.randint(10, 28)}",
            "country": rng.choice(COUNTRIES),
        }
        if i in corrupt_at:
            kind = rng.choice(CORRUPTIONS)
            if kind == "drop_at":
                row["email"] = row["email"].replace("@", ".")
            elif kind == "double_dot":
                local, domain = row["email"].split("@")
                row["email"] = local + "@" + domain.replace(".", "..", 1)
            elif kind == "trailing_dot":
                row["email"] = row["email"] + "."
            elif kind == "blank_date":
                row["signup_date"] = ""
            else:
                row["country"] = ""
        rows.append(row)
    return rows, n_invalid


def main():
    out_dir = "data/shards"
    n_shards = 8
    n_rows = 5000

    os.makedirs(out_dir, exist_ok=True)
    truth = {}

    for shard_id in range(n_shards):
        rows, n_invalid = build_shard(shard_id, n_rows)
        path = os.path.join(out_dir, f"shard_{shard_id:02d}.csv")
        with open(path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        truth[f"shard_{shard_id:02d}"] = {"rows": n_rows, "invalid": n_invalid}
        print(f"{path}: {n_rows} rows, {n_invalid} deliberately invalid")

    with open(os.path.join(out_dir, "ground_truth.json"), "w") as fh:
        json.dump(truth, fh, indent=2)
    print("wrote ground_truth.json")


if __name__ == "__main__":
    main()
