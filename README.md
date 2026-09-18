# DA3408 AI Operations — Module 3 Assignment 2

**Prabhav Gupta DA24B018**

This repo has my work for the Module 3 assignment. All four questions are here.

A 2-page write-up covering all four questions is in `DA3408_Assignment_2_Report.pdf` at the root of this repo.

## Setup

- Ubuntu VM with Docker, Docker Compose, minikube and kubectl installed
- Python virtual environment: `python3 -m venv .venv` then `source .venv/bin/activate`
- minikube run as one node with 4 CPUs: `minikube start --cpus 4 --memory 4096 --driver=docker`

## Question 1 — Single-Stage vs. Multi-Stage Docker

**Folder:** `question_1/`

- `app.py`, `generate_dataset.py`, `train_model.py` — the spam API, and the scripts that generate its training data and train the model
- `Dockerfile.naive` — installs everything and trains the model in a single build stage
- `Dockerfile.multistage` — trains the model in a first stage, then copies only the trained model and the runtime packages into a smaller second stage
- `build_naive.log`, `build_multistage.log` — the build output
- `naive_endpoints.txt`, `multistage_endpoints.txt` — curl output showing both images answer `/predict` and `/healthz` correctly
- `size_comparison.txt` — naive is 593 MB, multistage is 129 MB, a 78.24% reduction
- `layer_evidence.txt` — checked inside both images. The naive one has gcc, g++, make and pandas installed. The multistage one has none of these
- `q1_3.txt` — the written explanation for why the multistage image is smaller

**To run:**

```bash
cd question_1
docker build -f Dockerfile.naive -t spam-api:naive .
docker build -f Dockerfile.multistage -t spam-api:v1 .
docker run -d -p 8000:8000 spam-api:v1
curl localhost:8000/healthz
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' -d '{"text":"WIN a FREE iPhone now!"}'
```

## Question 2 — Multi-Container Orchestration with Docker Compose

**Folder:** `question_2/`

- `app.py` — before predicting, checks Redis for the same text. On a miss it computes the prediction and saves it. On a hit it returns the saved answer. Which one happened is shown in the `X-Cache` header
- `docker-compose.yml` — starts the api service and a cache service, Redis, together. The api service can reach Redis just by using the name `cache`
- `bench_cache.py` — sends the same 200 messages to the API twice. The first time none of them are cached, so every request is a miss. The second time all of them are cached, so every request is a hit
- `bench_cache.txt` — result of running `bench_cache.py`. All 200 misses on the first pass, all 200 hits on the second pass, and hits were faster
- `stack_up.txt` — confirms `cache` resolves to a real address from inside the api container
- `redis_keys.txt` — the keys actually stored in Redis
- `q2_4.txt` — the written answer comparing Docker Compose and Kubernetes

**To run:**

```bash
cd question_2
docker compose up -d --build
docker compose logs api
python bench_cache.py --n 200
```

## Question 3 — Kubernetes Indexed Job: Parallel Data Validation

**Folder:** `question_3/`

- `generate_shards.py` — creates 8 CSV files of fake signup records. Each file has a different, fixed number of deliberately broken rows. The correct count for each file is saved in `ground_truth.json`
- `validate_shard.py` — each pod reads its own job index to know which of the 8 files it is responsible for, checks that file, and prints its result
- `Dockerfile` — a single build stage, since the script has no extra dependencies to separate out
- `job_validation.yaml` — the Job manifest. It runs all 8 files to completion, 4 pods at a time. The reason 4 was chosen is explained in `q3_1.txt`
- `watch_concurrency.sh` — checks the running pods and records the highest number seen running at once. It should be started right after the Job is applied
- `collect_results.py` — reads each pod's result through the Kubernetes API instead of a shared file
- `q3_2.txt` — evidence that 4 pods really were running at the same time
- `q3_3.txt` — why a shared volume was not used
- `q3_4.txt` — what changes with 6 CPUs available instead of 4
- `results.csv`, `results_table.txt` — the results collected from all 8 pods, checked against `ground_truth.json`

**To run:**

```bash
cd question_3
python generate_shards.py
docker build -t shard-validator:v1 .
minikube image load shard-validator:v1
kubectl apply -f job_validation.yaml
chmod +x watch_concurrency.sh
./watch_concurrency.sh
python collect_results.py --out results.csv
```

## Question 4 — Kubernetes Deployments: Self-Healing and Rolling Updates

**Folder:** `question_4/`

- `app.py` — the spam API from Question 1, with a version string and the current pod and node name added to `/healthz`
- `deployment.yaml` — runs 2 replicas of the API with a readinessProbe against `/healthz`, and never drops below 2 ready pods while updating
- `service.yaml` — exposes the API on a fixed port
- `q4_1.txt` — the Deployment and Service applied, both endpoints working through the Service
- `q4_2.txt`, `q4_2_explanation.txt` — a running pod was deleted by hand, and a replacement was created automatically. The event log shows this was done by the ReplicaSet controller, not the Deployment directly
- `q4_3.txt`, `q4_3_job_vs_deployment.txt` — the API's health endpoint was checked repeatedly while the image was updated from v1 to v2. Almost all checks got a normal response. The few that did not happened right when the old and new pods were being swapped
- `q4_4.txt` — the final written comparison between how a Deployment and a Job behave

**To run:**

```bash
cd question_4
docker build -f Dockerfile.multistage -t spam-api:v1 .
minikube image load spam-api:v1
kubectl apply -f deployment.yaml -f service.yaml
kubectl rollout status deployment/spam-api
curl http://$(minikube ip):30080/healthz
kubectl get pods -l app=spam-api -o wide
```

Repeating the rolling update test needs two terminals.

In the first terminal, keep checking the health endpoint in a loop:

```bash
URL="http://$(minikube ip):30080"
while true; do
  curl -s $URL/healthz
  echo
  sleep 0.2
done
```

In the second terminal, build a new image, load it into minikube, update the image tag and version together in `deployment.yaml`, and apply it:

```bash
docker build -f Dockerfile.multistage -t spam-api:v2 .
minikube image load spam-api:v2
kubectl apply -f deployment.yaml
kubectl rollout status deployment/spam-api
```

Watching the first terminal while the second one runs shows the version changing from v1 to v2 without the API going down.

## AI usage

Tool used: Claude

Used to write the `.py` files, look up some terminal, Docker and kubectl commands, and debug errors while working through all four questions. Also used to format this README and the write-up.

This repo is private until the deadline and will be made public after, as asked.
