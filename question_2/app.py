import hashlib
import os
import time
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, Response
from pydantic import BaseModel

MODEL_PATH = os.environ.get("MODEL_PATH", "/app/model.joblib")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))

STATE = {"model": None, "cache": None, "ready": False}


def connect_cache():
    if not REDIS_HOST:
        print("[startup] REDIS_HOST not set - running without cache", flush=True)
        return None
    try:
        import redis
        client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True,
            socket_connect_timeout=2, socket_timeout=2,
        )
        client.ping()
        print(f"[startup] cache connected: {REDIS_HOST}:{REDIS_PORT}", flush=True)
        return client
    except Exception as exc:
        print(f"[startup] cache unavailable ({exc}) - continuing without it", flush=True)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE["model"] = joblib.load(MODEL_PATH)
    STATE["cache"] = connect_cache()
    STATE["ready"] = True
    print(f"[startup] model loaded from {MODEL_PATH}", flush=True)
    yield
    STATE["ready"] = False


app = FastAPI(title="spam-detection-api", lifespan=lifespan)


class PredictRequest(BaseModel):
    text: str


def cache_key(text):
    return "pred:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@app.get("/healthz")
def healthz(response: Response):
    if not STATE["ready"]:
        response.status_code = 503
        return {"status": "loading"}
    return {"status": "ok", "cache": "on" if STATE["cache"] else "off"}


@app.post("/predict")
def predict(req: PredictRequest, response: Response):
    started = time.perf_counter()
    cache = STATE["cache"]
    key = cache_key(req.text)

    if cache is not None:
        try:
            cached = cache.get(key)
        except Exception:
            cached = None
        if cached is not None:
            elapsed = (time.perf_counter() - started) * 1000
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Handler-Ms"] = f"{elapsed:.3f}"
            return {"label": cached}

    label = str(STATE["model"].predict([req.text])[0])

    if cache is not None:
        try:
            cache.setex(key, CACHE_TTL, label)
        except Exception:
            pass

    elapsed = (time.perf_counter() - started) * 1000
    response.headers["X-Cache"] = "MISS" if cache else "OFF"
    response.headers["X-Handler-Ms"] = f"{elapsed:.3f}"
    return {"label": label}
