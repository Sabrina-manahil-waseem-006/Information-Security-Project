from detector_config import THRESHOLDS        # ✅

def detect(metrics: dict) -> dict:
    score = 0
    reasons = []

    rps = metrics.get("rps", 0)
    cpu = metrics.get("cpu_percent", 0)
    ram = metrics.get("ram_percent", 0)
    latency = metrics.get("response_time_ms", 0) 
    err = metrics.get("error_rate", 0)

    if rps > THRESHOLDS["rps_critical"]:
        score += 3; reasons.append(f"RPS critical ({rps:.0f})")
    elif rps > THRESHOLDS["rps_high"]:
        score += 2; reasons.append(f"RPS high ({rps:.0f})")

    if cpu > THRESHOLDS["cpu_critical"]:
        score += 3; reasons.append(f"CPU critical ({cpu:.0f}%)")
    elif cpu > THRESHOLDS["cpu_high"]:
        score += 2; reasons.append(f"CPU high ({cpu:.0f}%)")

    if ram > THRESHOLDS["ram_high"]:
        score += 1; reasons.append(f"RAM high ({ram:.0f}%)")

    if latency > THRESHOLDS["latency_high"]:
        score += 2; reasons.append(f"Latency high ({latency:.0f}ms)")

    if err > THRESHOLDS["error_rate_high"]:
        score += 2; reasons.append(f"Error rate high ({err:.2f})")

    if rps > THRESHOLDS["rps_high"] and cpu > THRESHOLDS["cpu_high"]:
        score += 2; reasons.append("Combined RPS+CPU spike")

    if score == 0:
        return {"status": "normal", "severity": "low", "reason": "All metrics normal"}
    
    if score <= 2:
        severity = "low"
    elif score <= 5:
        severity = "medium"
    else:
        severity = "high"

    return {"status": "attack", "severity": severity, "reason": "; ".join(reasons)}