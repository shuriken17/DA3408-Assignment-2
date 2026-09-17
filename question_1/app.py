import os
import socket
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, Response
from pydantic import BaseModel

MODEL_PATH = os.environ.get("MODEL_PATH", "/app/model.joblib")
STATE = {"model": None, "ready": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE["model"] = joblib.load(MODEL_PATH)
    STATE["ready"] = True
    print(f"[startup] model loaded from {MODEL_PATH}", flush=True)
    yield
    STATE["ready"] = False


app = FastAPI(title="spam-detection-api", lifespan=lifespan)


class PredictRequest(BaseModel):
    text: str


@app.get("/healthz")
def healthz(response: Response):
    if not STATE["ready"]:
        response.status_code = 503
        return {"status": "loading"}
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    label = str(STATE["model"].predict([req.text])[0])
    return {"label": label}
