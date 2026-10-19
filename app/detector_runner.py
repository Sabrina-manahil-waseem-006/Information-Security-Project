import time
import requests
import csv
import os
from datetime import datetime
from detector import detect          # ✅

METRICS_URL = "http://localhost:8000/metrics"
LOG_FILE = "data/detections.csv"

def run_detector():
    os.makedirs("data", exist_ok=True)
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "status", "severity", "reason", "rps", "cpu", "ram", "latency", "error_rate"])

        print("Detector chal raha hai... (Ctrl+C se band karein)")
        
        while True:
            try:
                response = requests.get(METRICS_URL, timeout=2)
                metrics = response.json()
                
                result = detect(metrics)
                
                writer.writerow([
                    datetime.now().isoformat(),
                    result["status"], result["severity"], result["reason"],
                    metrics.get("rps", 0), metrics.get("cpu_percent", 0),
                    metrics.get("ram_percent", 0), metrics.get("avg_response_time_ms", 0),
                    metrics.get("error_rate", 0),
                ])
                f.flush()
                
                print(f"[{result['status'].upper()}] Severity: {result['severity']} | {result['reason']}")
                
            except Exception as e:
                print(f"Error fetching metrics: {e}")
            
            time.sleep(1)

if __name__ == "__main__":
    run_detector()