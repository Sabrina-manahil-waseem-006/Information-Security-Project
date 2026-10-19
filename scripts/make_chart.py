import csv
import matplotlib.pyplot as plt

def read_history(path):
    times, rps, fails = [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            times.append(float(row['Timestamp']))
            rps.append(float(row['Requests/s']))
            fails.append(float(row['Failures/s']))
    start = times[0] if times else 0
    return [t - start for t in times], rps, fails

fig, ax = plt.subplots(figsize=(12, 6))

# Test 2 (mit off)
t, rps, fails = read_history('results/02_flood_mitoff_stats_history.csv')
achieved = [r - f for r, f in zip(rps, fails)]
ax.plot(t, rps, label='Test 2: Flood (mit OFF) — attempted = achieved',
        color='red', linewidth=2)

# Test 3 (mit on)
t, rps, fails = read_history('results/03_flood_miton_stats_history.csv')
achieved = [r - f for r, f in zip(rps, fails)]
ax.plot(t, rps, label='Test 3: Flood (mit ON) — attempted',
        color='orange', linewidth=2, linestyle='--')
ax.plot(t, achieved, label='Test 3: Flood (mit ON) — achieved (200s)',
        color='green', linewidth=2)

ax.axhline(y=50, color='blue', linestyle=':', alpha=0.5, label='light limit (50 req/s)')
ax.axhline(y=20, color='purple', linestyle=':', alpha=0.5, label='moderate limit (20 req/s)')
ax.axhline(y=5, color='black', linestyle=':', alpha=0.5, label='aggressive limit (5 req/s)')

ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Requests per second')
ax.set_title('Mitigation Effect: Attempted vs Achieved RPS Under Volumetric Flood')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('results/mitigation_chart.png', dpi=150)
print('✅ Chart saved to results/mitigation_chart.png')
