#!/bin/bash
set -e
mkdir -p results

log() { echo ""; echo "=== $* ==="; }

restart_app() {
    local mode=$1
    docker compose down app >/dev/null 2>&1 || true
    MITIGATION_ENABLED=$mode docker compose up -d app >/dev/null
    sleep 5
    local actual=$(docker compose exec app printenv MITIGATION_ENABLED)
    echo "  App restarted: MITIGATION_ENABLED=$actual"
    if [ "$actual" != "$mode" ]; then
        echo "  ❌ MISMATCH — expected $mode, got $actual"
        exit 1
    fi
    # Sanity: mitigation level should be none
    curl -D - http://localhost:8000/ -o /dev/null 2>/dev/null | grep -i mitigation || true
    sleep 3
}

log "TEST 1: Normal (mit ON, low traffic)"
restart_app true
locust -f locust/locustfile.py --headless --host http://localhost:8000 \
  -u 10 -r 5 -t 30s --csv results/01_normal NormalUser 2>&1 | tail -6
echo "Waiting 5s before next test..."
sleep 5

log "TEST 2: Volumetric Flood (mit OFF)"
restart_app false
locust -f locust/locustfile.py --headless --host http://localhost:8000 \
  -u 100 -r 20 -t 30s --csv results/02_flood_mitoff VolumetricFlood 2>&1 | tail -6
echo "Waiting 5s before next test..."
sleep 5

log "TEST 3: Volumetric Flood (mit ON) ⭐"
restart_app true
locust -f locust/locustfile.py --headless --host http://localhost:8000 \
  -u 100 -r 20 -t 30s --csv results/03_flood_miton VolumetricFlood 2>&1 | tail -6
echo "Waiting 5s before next test..."
sleep 5

log "TEST 4: Extreme Flood (mit ON)"
locust -f locust/locustfile.py --headless --host http://localhost:8000 \
  -u 200 -r 40 -t 60s --csv results/04_extreme_miton VolumetricFlood 2>&1 | tail -6

log "ALL TESTS COMPLETE"
ls -la results/
