from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
import time

import monitor
from middleware import MonitoringMiddleware
from mitigation_middleware import MitigationMiddleware
from mitigation import choose_level, state
from detector import detect

app = FastAPI(title="Resource-Aware DDoS Mitigation Service")

# Order matters: LAST added = FIRST to run on each request.
# Request flow:  Mitigation → Monitoring → endpoint
#                 ↑ rejects 429    ↑ times request
app.add_middleware(MonitoringMiddleware)
app.add_middleware(MitigationMiddleware)


@app.on_event("startup")
async def startup():
    monitor.init_csv()
    asyncio.create_task(background_metrics_logger())
    asyncio.create_task(mitigation_loop())


async def background_metrics_logger():
    """Sabrina's existing loop — writes one row to metrics.csv per second."""
    while True:
        metrics = monitor.get_metrics()
        monitor.save_metrics_to_csv(metrics)
        await asyncio.sleep(1)


async def mitigation_loop():
    """
    Abeeha's loop — runs once per second:
      1. Read latest metrics (direct call, no HTTP)
      2. Run Sania's detect() to classify
      3. Run choose_level() to pick next mitigation level
      4. Update shared state that MitigationMiddleware reads
    """
    while True:
        try:
            metrics = monitor.get_metrics()
            detection = detect(metrics)
            level, reason = choose_level(detection, metrics)
            state.set(level, reason)
        except Exception as e:
            # Never let a bad tick kill the loop
            print(f"[mitigation_loop] error: {e}")
        await asyncio.sleep(1)


@app.get("/")
async def root():
    return {"message": "Service is running", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/metrics")
async def metrics():
    return JSONResponse(monitor.get_metrics())