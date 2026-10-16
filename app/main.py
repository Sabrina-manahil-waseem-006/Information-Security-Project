from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
import time

from app import monitor
from app.middleware import MonitoringMiddleware

app = FastAPI(title="Resource-Aware DDoS Mitigation Service")

# Middleware add karo
app.add_middleware(MonitoringMiddleware)

# Startup pe CSV initialize karo
@app.on_event("startup")
async def startup():
    monitor.init_csv()
    asyncio.create_task(background_metrics_logger())


async def background_metrics_logger():
    """Har 1 second metrics CSV mein likho"""
    while True:
        metrics = monitor.get_metrics()
        monitor.save_metrics_to_csv(metrics)
        await asyncio.sleep(1)


@app.get("/")
async def root():
    return {"message": "Service is running", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/metrics")
async def metrics():
    """Latest metrics JSON mein return karo"""
    return JSONResponse(monitor.get_metrics())