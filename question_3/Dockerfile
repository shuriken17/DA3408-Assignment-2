FROM python:3.10-slim

WORKDIR /app

COPY validate_shard.py ./
COPY data/shards/ ./data/shards/

ENV SHARD_DIR=/app/data/shards  PYTHONUNBUFFERED=1

CMD ["python", "validate_shard.py"]
