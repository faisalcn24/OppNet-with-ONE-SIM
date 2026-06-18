"""Generate README plots from MessageStatsReport files. No deps beyond matplotlib."""
import re, math, pathlib
import matplotlib.pyplot as plt

REPORTS = pathlib.Path(__file__).resolve().parents[1] / "reports"
OUT = pathlib.Path(__file__).resolve().parents[1] / "doc" / "img"
OUT.mkdir(parents=True, exist_ok=True)

PROTOS = [
    ("Epidemic",      "EpidemicRouter",      "#d62728"),
    ("PRoPHET",       "ProphetRouter",       "#ff7f0e"),
    ("Spray & Wait",  "SprayAndWaitRouter",  "#2ca02c"),
]
T95_N10 = 2.262

def load(prefix):
    rows = []
    for seed in range(1, 11):
        f = REPORTS / f"{prefix}-seed{seed}_MessageStatsReport.txt"
        data = {}
        for line in f.read_text().splitlines():
            m = re.match(r"^(\w+):\s*(\S+)", line)
            if m:
                try: data[m.group(1)] = float(m.group(2))
                except ValueError: pass
        rows.append(data)
    return rows

def stat(rows, key):
    vals = [r[key] for r in rows]
    n = len(vals)
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean)**2 for v in vals) / (n - 1))
    return mean, sd, T95_N10 * sd / math.sqrt(n), vals

data = {label: load(prefix) for label, prefix, _ in PROTOS}

# ---- Plot 1: paired bar chart (delivery prob + overhead ratio) ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
labels = [p[0] for p in PROTOS]
colors = [p[2] for p in PROTOS]

means_d = [stat(data[l], "delivery_prob")[0] for l in labels]
cis_d   = [stat(data[l], "delivery_prob")[2] for l in labels]
ax1.bar(labels, means_d, yerr=cis_d, color=colors, capsize=6, edgecolor="black", linewidth=0.5)
ax1.set_ylabel("Delivery probability")
ax1.set_title("Delivery probability (mean ± 95% CI, n=10)")
ax1.set_ylim(0, max(means_d) * 1.25)
for i, (m, c) in enumerate(zip(means_d, cis_d)):
    ax1.text(i, m + c + 0.01, f"{m:.3f}", ha="center", fontsize=9)

means_o = [stat(data[l], "overhead_ratio")[0] for l in labels]
cis_o   = [stat(data[l], "overhead_ratio")[2] for l in labels]
ax2.bar(labels, means_o, yerr=cis_o, color=colors, capsize=6, edgecolor="black", linewidth=0.5)
ax2.set_ylabel("Overhead ratio (relayed / delivered)")
ax2.set_title("Overhead ratio (mean ± 95% CI, n=10)")
ax2.set_ylim(0, max(means_o) * 1.18)
for i, (m, c) in enumerate(zip(means_o, cis_o)):
    ax2.text(i, m + c + max(means_o)*0.015, f"{m:.1f}", ha="center", fontsize=9)

fig.suptitle("DTN routing protocols on the ONE default Helsinki scenario (12 h, 126 hosts)", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "protocol_comparison.png", dpi=130, bbox_inches="tight")
plt.close(fig)

# ---- Plot 2: overhead vs delivery scatter (per-seed) ----
fig, ax = plt.subplots(figsize=(7, 5))
for label, prefix, color in PROTOS:
    rows = data[label]
    xs = [r["overhead_ratio"] for r in rows]
    ys = [r["delivery_prob"] for r in rows]
    ax.scatter(xs, ys, color=color, s=55, alpha=0.65, edgecolor="black", linewidth=0.4, label=label)
    mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
    ax.scatter([mx], [my], color=color, marker="X", s=200, edgecolor="black", linewidth=1.2, zorder=5)
ax.set_xlabel("Overhead ratio  →  worse")
ax.set_ylabel("Delivery probability  →  better")
ax.set_title("Delivery vs overhead — 10 seeds per protocol\n(X marks the mean; ideal is upper-left)")
ax.grid(True, alpha=0.3)
ax.legend(loc="center right")
ax.set_xscale("log")
fig.tight_layout()
fig.savefig(OUT / "delivery_vs_overhead.png", dpi=130, bbox_inches="tight")
plt.close(fig)

# ---- Plot 3: per-seed delivery probability dot plot ----
fig, ax = plt.subplots(figsize=(9, 4.2))
seeds = list(range(1, 11))
for label, prefix, color in PROTOS:
    ys = [r["delivery_prob"] for r in data[label]]
    ax.plot(seeds, ys, "o-", color=color, label=label, markersize=7, linewidth=1.4, alpha=0.9)
ax.set_xlabel("Movement RNG seed")
ax.set_ylabel("Delivery probability")
ax.set_title("Per-seed delivery probability — ranking is consistent across all 10 seeds")
ax.set_xticks(seeds)
ax.grid(True, alpha=0.3)
ax.legend(loc="center right")
fig.tight_layout()
fig.savefig(OUT / "delivery_per_seed.png", dpi=130, bbox_inches="tight")
plt.close(fig)

print("Wrote:")
for f in sorted(OUT.glob("*.png")):
    print(" ", f.relative_to(OUT.parents[1]), f.stat().st_size, "bytes")
