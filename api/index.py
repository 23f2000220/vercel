from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from statistics import mean
from pathlib import Path
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

telemetry_path = Path(__file__).resolve().parent.parent / "data" / "telemetry.json"
with open(telemetry_path, "r") as f:
    telemetry = json.load(f)

@app.post("/")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 0)

    result = {}

    for region in regions:
        records = telemetry.get(region, [])
        latencies = [r["latency"] for r in records]
        uptimes = [r["uptime"] for r in records]

        if latencies:
            sorted_latencies = sorted(latencies)
            p95_index = max(0, int(0.95 * len(sorted_latencies)) - 1)
            p95_latency = sorted_latencies[p95_index]
            avg_latency = mean(latencies)
            avg_uptime = mean(uptimes)
        else:
            p95_latency = None
            avg_latency = None
            avg_uptime = None

        breaches = sum(1 for r in records if r["latency"] > threshold_ms)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
# @app.get("/")
# def read_root():
#     return {"message": "Hello mighty World!"}


