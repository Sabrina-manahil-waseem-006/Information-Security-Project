
"""
Mitigation module.

Responsibilities:
1. Hold the current mitigation level (shared state).
2. Enforce per-IP rate limiting (sliding 1-second window).
3. Decide the next level from detection + resource pressure.
4. Log level changes to data/mitigation_events.csv.
5. Support runtime enable/disable for local testing.
"""

import os
import time
import csv

from collections import defaultdict, deque
from datetime import datetime
from threading import Lock


# ---------------------------------------------------------------
# CONFIG: MITIGATION LEVELS
# ---------------------------------------------------------------

LEVELS = {
    "none": {
        "rate_limit": None,
        "block": False
    },
    "light": {
        "rate_limit": 50,
        "block": False
    },
    "moderate": {
        "rate_limit": 20,
        "block": False
    },
    "aggressive": {
        "rate_limit": 5,
        "block": True
    },
}

LOG_FILE = "data/mitigation_events.csv"


# ---------------------------------------------------------------
# RUNTIME MITIGATION CONTROL
# ---------------------------------------------------------------

_enabled = os.getenv(
    "MITIGATION_ENABLED", "true"
).lower() == "true"

_enabled_lock = Lock()


def is_enabled() -> bool:
    """Return current mitigation enabled state."""
    with _enabled_lock:
        return _enabled


def set_enabled(value: bool) -> bool:
    """
    Enable or disable mitigation at runtime.

    The rate limiter is reset when mitigation is disabled.
    The background loop updates the mitigation level.
    """
    global _enabled

    with _enabled_lock:
        _enabled = bool(value)

    if not value:
        limiter.reset()

    return is_enabled()


# ---------------------------------------------------------------
# MITIGATION LEVEL RANKING
# ---------------------------------------------------------------

def _level_rank(level: str) -> int:
    """Convert mitigation level into severity rank."""
    return {
        "none": 0,
        "light": 1,
        "moderate": 2,
        "aggressive": 3
    }.get(level, 0)


# ---------------------------------------------------------------
# SHARED MITIGATION STATE
# ---------------------------------------------------------------

class MitigationState:

    def __init__(self):
        self.level = "none"
        self.reason = "startup"
        self.last_updated = time.time()
        self.last_escalation_at = 0.0
        self.cooldown_sec = 5.0
        self._lock = Lock()

    def set(self, level: str, reason: str):
        """Update mitigation level with cooldown protection."""

        with self._lock:
            current_rank = _level_rank(self.level)
            new_rank = _level_rank(level)
            now = time.time()

            # Prevent rapid de-escalation
            if new_rank < current_rank:
                if now - self.last_escalation_at < self.cooldown_sec:
                    return

            # Track escalation time
            if new_rank > current_rank:
                self.last_escalation_at = now

            changed = level != self.level

            self.level = level
            self.reason = reason
            self.last_updated = now

        if changed:
            _log_event(level, reason)

    def get(self):
        """Return current mitigation level and reason."""
        with self._lock:
            return self.level, self.reason


# Shared singleton
state = MitigationState()


# ---------------------------------------------------------------
# PER-IP RATE LIMITER
# ---------------------------------------------------------------

class RateLimiter:
    """
    Sliding 1-second rate limiter.

    - Tracks requests per IP.
    - Rejects requests exceeding the current limit.
    - In aggressive mode, blocks abusive IPs for 60 seconds
      after more than 10 violations.
    """

    def __init__(self):
        self.requests = defaultdict(deque)
        self.violations = defaultdict(int)
        self.blocked_until = {}
        self._lock = Lock()

    def check(self, ip: str, limit):
        """Return (allowed, reason)."""

        now = time.time()

        with self._lock:

            # Check existing IP block
            if ip in self.blocked_until:
                if now < self.blocked_until[ip]:
                    return False, "blocked"

            # Maintain 1-second sliding window
            q = self.requests[ip]

            while q and now - q[0] > 1.0:
                q.popleft()

            q.append(now)

            # No rate limit
            if limit is None:
                return True, ""

            # Rate limit exceeded
            if len(q) > limit:

                self.violations[ip] += 1

                if (
                    state.level == "aggressive"
                    and self.violations[ip] > 10
                ):
                    self.blocked_until[ip] = now + 60

                    _log_event(
                        "aggressive",
                        f"IP {ip} blocked for 60s"
                    )

                return False, "rate_limit"

            return True, ""

    def reset(self):
        """Clear all rate-limiter state."""

        with self._lock:
            self.requests.clear()
            self.violations.clear()
            self.blocked_until.clear()


# Shared rate limiter
limiter = RateLimiter()


# ---------------------------------------------------------------
# CPU SMOOTHING
# ---------------------------------------------------------------

_recent_cpu = deque(maxlen=5)


def _smooth_cpu(raw: float) -> float:
    """Average the last five CPU measurements."""

    _recent_cpu.append(raw)

    return sum(_recent_cpu) / len(_recent_cpu)


# ---------------------------------------------------------------
# ADAPTIVE MITIGATION DECISION LOGIC
# ---------------------------------------------------------------

def choose_level(detection: dict, metrics: dict):
    """
    Select mitigation level using:
    - Detection status
    - Detection severity
    - CPU utilization
    - RAM utilization
    """

    status = detection.get("status", "normal")
    severity = detection.get("severity", "low")

    cpu = _smooth_cpu(metrics.get("cpu_percent", 0))
    ram = metrics.get("ram_percent", 0)

    # No attack or mitigation disabled
    if status == "normal" or not is_enabled():
        return "none", "normal / mitigation disabled"

    # Base mitigation level
    if cpu < 50:
        base = "light"

    elif cpu < 80:
        base = "moderate"

    else:
        base = "aggressive"

    reasons = [
        f"detection={severity}",
        f"CPU={cpu:.0f}%"
    ]

    # Increase level for high-severity detection
    if severity == "high":

        if base == "light":
            base = "moderate"
            reasons.append("severity-bump")

        elif base == "moderate":
            base = "aggressive"
            reasons.append("severity-bump")

    # Escalate if RAM utilization is high
    if ram > 85 and base != "aggressive":
        base = "aggressive"
        reasons.append(f"RAM={ram:.0f}%")

    return base, "; ".join(reasons)


# ---------------------------------------------------------------
# CSV EVENT LOGGING
# ---------------------------------------------------------------

def _log_event(level: str, reason: str):
    """Save mitigation level changes to CSV."""

    os.makedirs("data", exist_ok=True)

    exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:

        writer = csv.writer(f)

        if not exists:
            writer.writerow([
                "timestamp",
                "level",
                "reason"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            level,
            reason
        ])
