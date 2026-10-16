import psutil
import time
import csv
import os
from datetime import datetime

METRICS_FILE = "data/metrics.csv"

request_count = 0
error_count = 0
response_times = []

last_rps_time = time.time()
last_request_count = 0
current_rps = 0


def init_csv():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "rps", "cpu_percent", "ram_percent",
                "network_bytes", "response_time_ms", "error_rate"
            ])


def record_request(response_time_ms: float, is_error: bool):
    global request_count, error_count
    request_count += 1
    if is_error:
        error_count += 1
    response_times.append(response_time_ms)
    if len(response_times) > 100:
        response_times.pop(0)


def get_metrics():
    global last_rps_time, last_request_count, current_rps

    now = time.time()
    elapsed = now - last_rps_time

    if elapsed >= 1.0:
        current_rps = (request_count - last_request_count) / elapsed
        last_request_count = request_count
        last_rps_time = now

    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent

    net = psutil.net_io_counters()
    network_bytes = net.bytes_sent + net.bytes_recv

    avg_response = sum(response_times) / len(response_times) if response_times else 0
    err_rate = (error_count / request_count) if request_count > 0 else 0

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "rps": round(current_rps, 2),
        "cpu_percent": cpu,
        "ram_percent": ram,
        "network_bytes": network_bytes,
        "response_time_ms": round(avg_response, 2),
        "error_rate": round(err_rate, 4),
    }


def save_metrics_to_csv(metrics: dict):
    with open(METRICS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            metrics["timestamp"],
            metrics["rps"],
            metrics["cpu_percent"],
            metrics["ram_percent"],
            metrics["network_bytes"],
            metrics["response_time_ms"],
            metrics["error_rate"],
        ])