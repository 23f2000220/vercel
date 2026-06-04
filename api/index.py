from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from statistics import mean
from pathlib import Path
import json
import numpy as np



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

telemetry_path = Path(__file__).resolve().parent / "data" / "telemetry.json"
with open(telemetry_path, "r") as f:
    telemetry = json.load(f)

@app.get("/")
def read_root():
    return {"message": "Hello mighty World!"}

@app.post("/latency")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 0)

    output = []

    for region in regions:
        records = [r for r in telemetry if r.get("region") == region]
        latencies = [r.get("latency_ms") for r in records if r.get("latency_ms") is not None]
        uptimes = [r.get("uptime_pct") for r in records if r.get("uptime_pct") is not None]

        if latencies:
            sorted_latencies = sorted(latencies)
            # p95_index = max(0, int(0.95 * len(sorted_latencies)) - 1)
            p95_latency = float(np.percentile(latencies, 95))
            # p95_latency = sorted_latencies[p95_index]
            avg_latency = mean(latencies)
        else:
            p95_latency = None
            avg_latency = None

        avg_uptime = mean(uptimes) if uptimes else None
        breaches = sum(1 for r in records if r.get("latency_ms", 0) > threshold_ms)

        output.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        })

    return {"regions": output}


from mangum import Mangum
handler = Mangum(app, lifespan="off")