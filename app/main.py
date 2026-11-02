from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
import time

import monitor
from middleware import MonitoringMiddleware
from mitigation_middleware import MitigationMiddleware
from mitigation import choose_level, state
from detector import detect

from mitigation import is_enabled, set_enabled, LEVELS

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

@app.get("/detection")
async def detection_status():
    metrics = monitor.get_metrics()
    return detect(metrics)

@app.get("/mitigation/status")
async def mitigation_status():
    level, reason = state.get()

    return {
        "enabled": is_enabled(),
        "level": level,
        "reason": reason,
        "rate_limit": LEVELS[level]["rate_limit"],
        "last_updated": state.last_updated
    }

from fastapi import Request, HTTPException

def require_local_request(request: Request):
    """Allow mitigation controls only from local machine."""
    if request.client is None or request.client.host not in (
        "127.0.0.1", "::1"
    ):
        raise HTTPException(
            status_code=403,
            detail="Mitigation controls are restricted to localhost"
        )


@app.post("/mitigation/enable")
async def enable_mitigation(request: Request):
    require_local_request(request)

    set_enabled(True)

    return {
        "success": True,
        "enabled": is_enabled(),
        "message": "Mitigation enabled"
    }


@app.post("/mitigation/disable")
async def disable_mitigation(request: Request):
    require_local_request(request)

    set_enabled(False)

    return {
        "success": True,
        "enabled": is_enabled(),
        "message": "Mitigation disabled"
    }


from pydantic import BaseModel
from simulation import (
    start_simulation,
    stop_simulation,
    get_status,
)


class SimulationRequest(BaseModel):
    mode: str


@app.get("/simulation/status")
async def simulation_status():
    return get_status()


@app.post("/simulation/start")
async def simulation_start(
    body: SimulationRequest,
    request: Request
):
    require_local_request(request)

    try:
        return start_simulation(body.mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/simulation/stop")
async def simulation_stop(request: Request):
    require_local_request(request)
    return stop_simulation()
