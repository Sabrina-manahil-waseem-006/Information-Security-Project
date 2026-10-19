"""
Mitigation module.

Responsibilities:
1. Hold the current mitigation level (shared state).
2. Enforce per-IP rate limiting (sliding 1-second window).
3. Decide the next level from detection + resource pressure.
4. Log level changes to data/mitigation_events.csv.
"""
import os
import time
import csv
from collections import defaultdict, deque
from datetime import datetime
from threading import Lock

# ---------------------------------------------------------------
# CONFIG: what each level does
# ---------------------------------------------------------------
LEVELS = {
    "none":       {"rate_limit": None, "block": False},   # no limiting
    "light":      {"rate_limit": 50,   "block": False},   # 50 req/s per IP
    "moderate":   {"rate_limit": 20,   "block": False},   # 20 req/s per IP
    "aggressive": {"rate_limit": 5,    "block": True},    # 5 req/s + block abusive IPs
}

LOG_FILE = "data/mitigation_events.csv"

# Global kill switch — lets us A/B test without code changes
_enabled = os.getenv("MITIGATION_ENABLED", "true").lower() == "true"


def is_enabled() -> bool:
    """Read the kill switch env var (read once at import, fine for demo)."""
    return _enabled


# ---------------------------------------------------------------
# SHARED STATE: one instance, updated by loop, read by middleware
# ---------------------------------------------------------------
def _level_rank(level: str) -> int:
    """Map level name to severity rank (higher = more aggressive)."""
    return {"none": 0, "light": 1, "moderate": 2, "aggressive": 3}.get(level, 0)


class MitigationState:
    def __init__(self):
        self.level = "none"
        self.reason = "startup"
        self.last_updated = time.time()
        self.last_escalation_at = 0.0
        self.cooldown_sec = 5.0
        self._lock = Lock()

    def set(self, level: str, reason: str):
        """Update level. Only log if it actually changed."""
        with self._lock:
            current_rank = _level_rank(self.level)
            new_rank = _level_rank(level)
            now = time.time()

            # Block de-escalation within cooldown window
            if new_rank < current_rank:
                if now - self.last_escalation_at < self.cooldown_sec:
                    return

            # Track when we escalate
            if new_rank > current_rank:
                self.last_escalation_at = now

            changed = level != self.level
            self.level = level
            self.reason = reason
            self.last_updated = now
        if changed:
            _log_event(level, reason)

    def get(self):
        with self._lock:
            return self.level, self.reason


# Module-level singleton — imported by main.py and mitigation_middleware.py
state = MitigationState()


# ---------------------------------------------------------------
# PER-IP RATE LIMITER (sliding 1-second window)
# ---------------------------------------------------------------
class RateLimiter:
    """
    For each IP:
      - Track timestamps of recent requests
      - Drop timestamps older than 1 second
      - If count in last 1s > limit → deny
      - In aggressive mode, block IP for 60s after 10 violations
    """
    def __init__(self):
        self.requests = defaultdict(deque)     # ip -> deque of timestamps
        self.violations = defaultdict(int)     # ip -> cumulative violation count
        self.blocked_until = {}                # ip -> unix timestamp when block ends
        self._lock = Lock()

    def check(self, ip: str, limit):
        """Return (allowed: bool, reason: str)."""
        now = time.time()
        with self._lock:
            # 1. Is IP currently blocked?
            if ip in self.blocked_until and now < self.blocked_until[ip]:
                return False, "blocked"

            # 2. Maintain sliding window
            q = self.requests[ip]
            while q and now - q[0] > 1.0:
                q.popleft()          # drop requests older than 1s
            q.append(now)            # record this request

            # 3. No limit configured (level = none) → allow
            if limit is None:
                return True, ""

            # 4. Over limit?
            if len(q) > limit:
                self.violations[ip] += 1

                # In aggressive mode, block after 10 violations
                if state.level == "aggressive" and self.violations[ip] > 10:
                    self.blocked_until[ip] = now + 60
                    _log_event("aggressive", f"IP {ip} blocked for 60s")

                return False, "rate_limit"

            return True, ""

    def reset(self):
        """Clear all state (used in tests)."""
        with self._lock:
            self.requests.clear()
            self.violations.clear()
            self.blocked_until.clear()


# Singleton — imported by middleware
limiter = RateLimiter()


# ---------------------------------------------------------------
# CPU SMOOTHING (fix for host-CPU noise causing oscillation)
# ---------------------------------------------------------------
# psutil.cpu_percent() inside a container without a CPU cgroup limit
# reports HOST CPU, not app CPU. In Codespaces / shared VMs this spikes
# to 100% intermittently due to unrelated workloads, causing the detector
# to misfire and the mitigation level to oscillate every second.
#
# Fix: keep a rolling window of the last N CPU readings and use the
# average. A 1-tick spike gets averaged away; a sustained flood still
# raises the average within a few seconds.
_recent_cpu = deque(maxlen=5)


def _smooth_cpu(raw: float) -> float:
    """Return the average of the last N (max 5) CPU readings."""
    _recent_cpu.append(raw)
    return sum(_recent_cpu) / len(_recent_cpu)


# ---------------------------------------------------------------
# DECISION LOGIC: detection + resources → new level
# ---------------------------------------------------------------
def choose_level(detection: dict, metrics: dict):
    """
    Inputs:
      detection = {"status": "normal"|"attack", "severity": "low"|"medium"|"high", ...}
      metrics   = raw metrics from Sabrina's /metrics (cpu_percent, ram_percent, ...)
    Returns:
      (level, reason)
    """
    status = detection.get("status", "normal")
    severity = detection.get("severity", "low")
    # Smoothed CPU rejects transient host-CPU spikes (see note above)
    cpu = _smooth_cpu(metrics.get("cpu_percent", 0))
    ram = metrics.get("ram_percent", 0)

    # Rule 0: nothing to do
    if status == "normal" or not is_enabled():
        return "none", "normal / mitigation disabled"

    # Rule 1: base level from CPU (matches spec's requested logic)
    if cpu < 50:
        base = "light"
    elif cpu < 80:
        base = "moderate"
    else:
        base = "aggressive"

    reasons = [f"detection={severity}", f"CPU={cpu:.0f}%"]

    # Rule 2: severity bump (one level up if attack is "high")
    if severity == "high":
        if base == "light":
            base = "moderate"
            reasons.append("severity-bump")
        elif base == "moderate":
            base = "aggressive"
            reasons.append("severity-bump")

    # Rule 3: RAM escalation
    if ram > 85 and base != "aggressive":
        base = "aggressive"
        reasons.append(f"RAM={ram:.0f}%")

    return base, "; ".join(reasons)


# ---------------------------------------------------------------
# CSV LOGGING
# ---------------------------------------------------------------
def _log_event(level: str, reason: str):
    """Append one row to mitigation_events.csv. Only called on level change."""
    os.makedirs("data", exist_ok=True)
    exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp", "level", "reason"])
        w.writerow([datetime.now().isoformat(), level, reason])