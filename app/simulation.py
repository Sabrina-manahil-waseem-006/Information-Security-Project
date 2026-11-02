
import subprocess
import sys
import os
from pathlib import Path
from threading import Lock

_lock = Lock()
_process = None
_mode = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCUST_FILE = PROJECT_ROOT / "locust" / "locustfile.py"

CLASSES = {
    "normal": "NormalUser",
    "ddos": "VolumetricFlood",
}


def get_status():
    global _process, _mode

    with _lock:
        if _process is not None and _process.poll() is not None:
            _process = None
            _mode = None

        return {
            "running": _process is not None,
            "mode": _mode,
        }


def start_simulation(mode):
    global _process, _mode

    if mode not in CLASSES:
        raise ValueError("Invalid simulation mode")

    with _lock:
        if _process is not None and _process.poll() is None:
            raise RuntimeError("Simulation already running")

        command = [
            sys.executable, "-m", "locust",
            "-f", str(LOCUST_FILE),
            CLASSES[mode],
            "--headless",
            "--host", "http://127.0.0.1:8000",
            "--users", "1",
            "--spawn-rate", "1",
            "--run-time", "30s",
            "--stop-timeout", "2",
            "--only-summary",
        ]

        _process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        _mode = mode

        return {"running": True, "mode": mode}


def stop_simulation():
    global _process, _mode

    with _lock:
        if _process is not None and _process.poll() is None:
            _process.terminate()

            try:
                _process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _process.kill()
                _process.wait()

        _process = None
        _mode = None

        return {"running": False, "mode": None}
