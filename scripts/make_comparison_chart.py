"""
Generate a comprehensive comparison chart for the mitigation test results.
Produces a 2x2 grid covering all rows of the comparison table.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─── Data from the 4 clean tests ───
tests = ['Test 1\nNormal\n(10 users)', 'Test 2\nFlood OFF\n(100 users)',
         'Test 3\nFlood ON ⭐\n(100 users)', 'Test 4\nExtreme ON\n(200 users)']
short   = ['Test 1\nNormal', 'Test 2\nFlood OFF', 'Test 3\nFlood ON', 'Test 4\nExtreme ON']
attempted  = [10.1, 472, 853, 845]
achieved   = [10.1, 472, 31.6, 34.7]
rejected   = [0, 0, 24266, 47838]
rejection_rate = [0.0, 0.0, 96.2, 95.8]
latency    = [4, 180, 73, 180]
load_redux = [1.0, 1.0, 14.9, 13.6]

# ─── Style ───
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.dpi': 100,
})

COLORS = {
    'achieved': '#2ECC71',   # green
    'rejected': '#E74C3C',   # red
    'attempted': '#3498DB',  # blue
    'highlight': '#F39C12',  # orange
    'neutral':   '#95A5A6',  # gray
}

fig = plt.figure(figsize=(16, 10))
fig.suptitle('Adaptive Mitigation: Volumetric Traffic Test Results',
             fontsize=16, fontweight='bold', y=0.995)

x = np.arange(len(short))
width = 0.35

# ─────────────────────────────────────────────
# PANEL 1 (top-left): Attempted vs Achieved RPS
# ─────────────────────────────────────────────
ax1 = fig.add_subplot(2, 2, 1)

bars1 = ax1.bar(x - width/2, attempted, width, label='Attempted RPS (attacker)', color=COLORS['attempted'], edgecolor='black', linewidth=0.8)
bars2 = ax1.bar(x + width/2, achieved,  width, label='Achieved RPS (server serving)', color=COLORS['achieved'], edgecolor='black', linewidth=0.8)

# Annotate bars
for i, (a, s) in enumerate(zip(attempted, achieved)):
    ax1.text(i - width/2, a + 15, f'{a:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax1.text(i + width/2, s + 15, f'{s:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1E8449')

# Highlight the "money" comparison (Test 2 vs Test 3)
ax1.annotate('', xy=(2 + width/2, 472), xytext=(2 + width/2, 31.6),
             arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=2))
ax1.text(2 + width/2 + 0.15, (472 + 31.6)/2, '14.9×\nreduction',
         color='#E74C3C', fontweight='bold', fontsize=10, ha='left', va='center')

ax1.set_xticks(x)
ax1.set_xticklabels(short, fontsize=9)
ax1.set_ylabel('Requests per second')
ax1.set_title('Attempted vs Achieved RPS')
ax1.set_ylim(0, max(attempted) * 1.25)
ax1.legend(loc='upper left', fontsize=9, framealpha=0.95)

# ─────────────────────────────────────────────
# PANEL 2 (top-right): Rejection Rate
# ─────────────────────────────────────────────
ax2 = fig.add_subplot(2, 2, 2)

bar_colors = [COLORS['neutral'] if r == 0 else COLORS['rejected'] for r in rejection_rate]
bars = ax2.bar(x, rejection_rate, color=bar_colors, edgecolor='black', linewidth=0.8)

for i, r in enumerate(rejection_rate):
    if r > 0:
        ax2.text(i, r + 2, f'{r:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold', color='#C0392B')
    else:
        ax2.text(i, 2, '0%', ha='center', va='bottom', fontsize=11, fontweight='bold', color='gray')

ax2.axhline(y=50, color='black', linestyle=':', alpha=0.4, lw=1)
ax2.text(3.4, 51, '50%', fontsize=8, color='gray')

ax2.set_xticks(x)
ax2.set_xticklabels(short, fontsize=9)
ax2.set_ylabel('Rejection rate (%)')
ax2.set_title('Attack Traffic Rejection Rate')
ax2.set_ylim(0, 110)

# ─────────────────────────────────────────────
# PANEL 3 (bottom-left): Latency (Median)
# ─────────────────────────────────────────────
ax3 = fig.add_subplot(2, 2, 3)

lat_colors = [COLORS['achieved'] if i == 2 else COLORS['neutral'] for i in range(len(latency))]
bars = ax3.bar(x, latency, color=lat_colors, edgecolor='black', linewidth=0.8)

for i, l in enumerate(latency):
    ax3.text(i, l + 4, f'{l} ms', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Show the "interesting" note: latency IMPROVES under mitigation
ax3.annotate('Latency improves\nunder mitigation\n(180ms → 73ms)',
             xy=(2, 73), xytext=(0.6, 140),
             arrowprops=dict(arrowstyle='->', color='#1E8449', lw=2),
             fontsize=9, color='#1E8449', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#D5F5E3', edgecolor='#1E8449', alpha=0.9))

ax3.set_xticks(x)
ax3.set_xticklabels(short, fontsize=9)
ax3.set_ylabel('Median response time (ms)')
ax3.set_title('Median Latency per Test')
ax3.set_ylim(0, max(latency) * 1.6)

# ─────────────────────────────────────────────
# PANEL 4 (bottom-right): Load Reduction Factor
# ─────────────────────────────────────────────
ax4 = fig.add_subplot(2, 2, 4)

redux_colors = [COLORS['neutral'], COLORS['neutral'], COLORS['achieved'], COLORS['achieved']]
bars = ax4.bar(x, load_redux, color=redux_colors, edgecolor='black', linewidth=0.8)

for i, r in enumerate(load_redux):
    label = 'baseline' if r == 1.0 else f'{r:.1f}×'
    ax4.text(i, r + 0.4, label, ha='center', va='bottom', fontsize=11, fontweight='bold')
    if r > 1:
        ax4.text(i, r - 0.6, f'472 → {achieved[i]:.0f} RPS',
                 ha='center', va='top', fontsize=8, color='white', fontweight='bold')

ax4.axhline(y=1, color='black', linestyle='--', alpha=0.5, lw=1)
ax4.text(3.4, 1.3, 'no mitigation\n(1×)', fontsize=8, color='gray', ha='center')

ax4.set_xticks(x)
ax4.set_xticklabels(short, fontsize=9)
ax4.set_ylabel('Load reduction factor')
ax4.set_title('Load Reduction Under Mitigation')
ax4.set_ylim(0, max(load_redux) * 1.35)

# ─────────────────────────────────────────────
# Footer note
# ─────────────────────────────────────────────
fig.text(0.5, 0.01,
         'Mitigation reduces effective attack throughput by 14.9× — 96.2% of attack traffic rejected with HTTP 429',
         ha='center', fontsize=11, fontweight='bold', style='italic',
         color='#2C3E50')

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig('results/comparison_chart.png', dpi=150, bbox_inches='tight', facecolor='white')
print('✅ Chart saved: results/comparison_chart.png')

# Also save a vertical "poster" version — single column, easier to read in reports
fig2, axes = plt.subplots(4, 1, figsize=(10, 14))
fig2.suptitle('Adaptive Mitigation — Volumetric Test Results',
              fontsize=15, fontweight='bold')

# Panel A: Attempted vs Achieved
axes[0].bar(x - width/2, attempted, width, label='Attempted RPS', color=COLORS['attempted'], edgecolor='black')
axes[0].bar(x + width/2, achieved,  width, label='Achieved RPS', color=COLORS['achieved'], edgecolor='black')
for i, (a, s) in enumerate(zip(attempted, achieved)):
    axes[0].text(i - width/2, a + 15, f'{a:.0f}', ha='center', fontsize=9, fontweight='bold')
    axes[0].text(i + width/2, s + 15, f'{s:.0f}', ha='center', fontsize=9, fontweight='bold')
axes[0].set_xticks(x); axes[0].set_xticklabels(short)
axes[0].set_ylabel('RPS'); axes[0].set_title('A. Attempted vs Achieved RPS')
axes[0].legend(loc='upper left'); axes[0].grid(alpha=0.3)
axes[0].set_ylim(0, max(attempted)*1.2)

# Panel B: Rejection rate
axes[1].bar(x, rejection_rate, color=bar_colors, edgecolor='black')
for i, r in enumerate(rejection_rate):
    axes[1].text(i, r + 2, f'{r:.1f}%', ha='center', fontsize=11, fontweight='bold')
axes[1].set_xticks(x); axes[1].set_xticklabels(short)
axes[1].set_ylabel('%'); axes[1].set_title('B. Attack Traffic Rejection Rate')
axes[1].set_ylim(0, 110); axes[1].grid(alpha=0.3)

# Panel C: Latency
axes[2].bar(x, latency, color=lat_colors, edgecolor='black')
for i, l in enumerate(latency):
    axes[2].text(i, l + 4, f'{l} ms', ha='center', fontsize=11, fontweight='bold')
axes[2].set_xticks(x); axes[2].set_xticklabels(short)
axes[2].set_ylabel('ms'); axes[2].set_title('C. Median Latency')
axes[2].set_ylim(0, max(latency)*1.4); axes[2].grid(alpha=0.3)

# Panel D: Load reduction
axes[3].bar(x, load_redux, color=redux_colors, edgecolor='black')
for i, r in enumerate(load_redux):
    label = 'baseline' if r == 1.0 else f'{r:.1f}×'
    axes[3].text(i, r + 0.4, label, ha='center', fontsize=11, fontweight='bold')
axes[3].axhline(y=1, color='black', linestyle='--', alpha=0.4)
axes[3].set_xticks(x); axes[3].set_xticklabels(short)
axes[3].set_ylabel('×'); axes[3].set_title('D. Load Reduction Factor')
axes[3].set_ylim(0, max(load_redux)*1.3); axes[3].grid(alpha=0.3)

fig2.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig('results/comparison_chart_poster.png', dpi=150, bbox_inches='tight', facecolor='white')
print('✅ Poster saved: results/comparison_chart_poster.png')
