"""
Generate all required performance plots for P28 K-Means project.
Reads CSVs from results/raw/, saves PNGs to results/plots/.
"""
import os, csv, collections
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs("results/plots", exist_ok=True)

# ---- load all CSVs ----
all_rows = []
raw_dir = "results/raw"
for fname in sorted(os.listdir(raw_dir)):
    if not fname.endswith(".csv"): continue
    with open(os.path.join(raw_dir, fname)) as f:
        for r in csv.DictReader(f):
            all_rows.append(r)

def fget(r, col):
    try: return float(r.get(col, 0) or 0)
    except: return 0.0

def by_impl(rows, dataset_filter=None):
    d = collections.defaultdict(list)
    for r in rows:
        if dataset_filter and r['dataset'] != dataset_filter: continue
        d[r['implementation']].append(fget(r, 'total_ms'))
    return d

IMPLS  = ['sequential','omp_private','omp_atomic','omp_critical','omp_simd','pthreads']
LABELS = ['Sequential','OMP Private','OMP Atomic','OMP Critical','OMP SIMD','Pthreads']
COLORS = ['#555555','#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd']

DATASETS = ['N10000_d2_k8.bin','N100000_d2_k8.bin','N100000_d16_k8.bin',
            'N100000_d2_k64.bin','N1000000_d2_k8.bin']
DS_LABELS= ['N=10k\nd=2 k=8','N=100k\nd=2 k=8','N=100k\nd=16 k=8',
            'N=100k\nd=2 k=64','N=1M\nd=2 k=8']

def mean_ms(d, impl):
    vals = d.get(impl, [])
    return float(np.mean(vals)) if vals else 0.0

def std_ms(d, impl):
    vals = d.get(impl, [])
    return float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0

# Reference dataset for per-implementation charts
REF = 'N100000_d2_k8.bin'
ref_d = by_impl(all_rows, REF)
seq_ref = mean_ms(ref_d, 'sequential') or 1.0

# ------------------------------------------------------------------
# Fig 1 – Execution time by implementation (N=100k, d=2, k=8)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
ms  = [mean_ms(ref_d, i) for i in IMPLS]
sds = [std_ms(ref_d, i)  for i in IMPLS]
ax.bar(LABELS, ms, yerr=sds, capsize=5, color=COLORS, edgecolor='black', linewidth=0.7)
ax.set_title('Execution Time by Implementation (N=100 k, d=2, k=8, 8 threads)')
ax.set_ylabel('Mean Time (ms)'); ax.set_xlabel('Implementation')
plt.xticks(rotation=15, ha='right'); plt.tight_layout()
plt.savefig('results/plots/fig1_time_by_impl.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 2 – Speedup
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
speedups = [(seq_ref / mean_ms(ref_d, i)) if mean_ms(ref_d, i) else 1 for i in IMPLS]
ax.bar(LABELS, speedups, color=COLORS, edgecolor='black', linewidth=0.7)
ax.axhline(1.0, color='black', linestyle='--', linewidth=0.8, label='Baseline 1×')
ax.set_title('Speedup over Sequential Baseline (N=100 k, d=2, k=8, 8 threads)')
ax.set_ylabel('Speedup (×)'); ax.set_xlabel('Implementation')
ax.legend(); plt.xticks(rotation=15, ha='right'); plt.tight_layout()
plt.savefig('results/plots/fig2_speedup.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 3 – Parallel efficiency (threads=8)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
n_threads = 8
eff = [s / n_threads for s in speedups]
ax.bar(LABELS, eff, color=COLORS, edgecolor='black', linewidth=0.7)
ax.axhline(1.0, color='black', linestyle='--', linewidth=0.8, label='Perfect efficiency')
ax.set_title('Parallel Efficiency (N=100 k, d=2, k=8, 8 threads)')
ax.set_ylabel('Efficiency = Speedup / Threads'); ax.set_xlabel('Implementation')
ax.legend(); plt.xticks(rotation=15, ha='right'); plt.tight_layout()
plt.savefig('results/plots/fig3_efficiency.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 4 – Execution time vs N (log-log)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
n_map = [('N10000_d2_k8.bin',10000),('N100000_d2_k8.bin',100000),('N1000000_d2_k8.bin',1000000)]
plot_impls = [('sequential','Sequential','#555555'),
              ('omp_private','OMP Private','#1f77b4'),
              ('omp_simd','OMP SIMD','#d62728'),
              ('pthreads','Pthreads','#9467bd')]
for impl, label, color in plot_impls:
    xs, ys = [], []
    for fname, N in n_map:
        d = by_impl(all_rows, fname)
        m = mean_ms(d, impl)
        if m > 0: xs.append(N); ys.append(m)
    if xs: ax.plot(xs, ys, marker='o', label=label, color=color)
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_title('Execution Time vs Dataset Size (d=2, k=8, 8 threads)')
ax.set_xlabel('N (number of points)'); ax.set_ylabel('Mean Time (ms)')
ax.legend(); ax.grid(True, which='both', linestyle='--', alpha=0.5)
plt.tight_layout(); plt.savefig('results/plots/fig4_time_vs_N.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 5 – OpenMP sync strategy comparison
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8,5))
omp_i = ['omp_private','omp_atomic','omp_critical']
omp_l = ['OMP Private','OMP Atomic','OMP Critical']
omp_c = ['#1f77b4','#ff7f0e','#2ca02c']
ms2 = [mean_ms(ref_d, i) for i in omp_i]
sd2 = [std_ms(ref_d, i)  for i in omp_i]
ax.bar(omp_l, ms2, yerr=sd2, capsize=5, color=omp_c, edgecolor='black', linewidth=0.7)
ax.set_title('OpenMP Synchronisation Strategy Comparison (N=100 k, d=2, k=8, 8 threads)')
ax.set_ylabel('Mean Time (ms)'); ax.set_xlabel('Synchronisation Strategy')
plt.tight_layout(); plt.savefig('results/plots/fig5_omp_sync.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 6 – SIMD vs non-SIMD across datasets
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
x = np.arange(len(DATASETS)); w = 0.35
priv_ms = [mean_ms(by_impl(all_rows, ds), 'omp_private') for ds in DATASETS]
simd_ms = [mean_ms(by_impl(all_rows, ds), 'omp_simd')    for ds in DATASETS]
ax.bar(x-w/2, priv_ms, w, label='OMP Private', color='#1f77b4', edgecolor='black')
ax.bar(x+w/2, simd_ms, w, label='OMP SIMD',    color='#d62728', edgecolor='black')
ax.set_xticks(x); ax.set_xticklabels(DS_LABELS, fontsize=8)
ax.set_title('SIMD vs Non-SIMD Distance Computation (8 threads)')
ax.set_ylabel('Mean Time (ms)'); ax.legend()
plt.tight_layout(); plt.savefig('results/plots/fig6_simd_vs_nonsimd.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 7 – Pthreads vs OMP Private across datasets
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
pth_ms = [mean_ms(by_impl(all_rows, ds), 'pthreads')    for ds in DATASETS]
omp_ms = [mean_ms(by_impl(all_rows, ds), 'omp_private') for ds in DATASETS]
ax.bar(x-w/2, omp_ms, w, label='OpenMP Private', color='#1f77b4', edgecolor='black')
ax.bar(x+w/2, pth_ms, w, label='Pthreads',       color='#9467bd', edgecolor='black')
ax.set_xticks(x); ax.set_xticklabels(DS_LABELS, fontsize=8)
ax.set_title('Pthreads vs OpenMP Private (8 threads)')
ax.set_ylabel('Mean Time (ms)'); ax.legend()
plt.tight_layout(); plt.savefig('results/plots/fig7_pthreads_vs_omp.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 8 – Performance vs k
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8,5))
k_map = {8: by_impl(all_rows,'N100000_d2_k8.bin'), 64: by_impl(all_rows,'N100000_d2_k64.bin')}
for impl, label, color in plot_impls:
    ks = sorted(k_map.keys())
    ms_k = [mean_ms(k_map[k], impl) for k in ks]
    ax.plot(ks, ms_k, marker='o', label=label, color=color)
ax.set_title('Performance vs k (N=100 k, d=2, 8 threads)')
ax.set_xlabel('k (clusters)'); ax.set_ylabel('Mean Time (ms)')
ax.legend(); ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout(); plt.savefig('results/plots/fig8_perf_vs_k.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 9 – Performance vs d
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8,5))
d_map = {2: by_impl(all_rows,'N100000_d2_k8.bin'), 16: by_impl(all_rows,'N100000_d16_k8.bin')}
for impl, label, color in plot_impls:
    dims = sorted(d_map.keys())
    ms_d = [mean_ms(d_map[dim], impl) for dim in dims]
    ax.plot(dims, ms_d, marker='s', label=label, color=color)
ax.set_title('Performance vs Dimensionality d (N=100 k, k=8, 8 threads)')
ax.set_xlabel('Dimensionality d'); ax.set_ylabel('Mean Time (ms)')
ax.legend(); ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout(); plt.savefig('results/plots/fig9_perf_vs_d.png', dpi=150); plt.close()

# ------------------------------------------------------------------
# Fig 10 – Throughput (Mpts/s)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9,5))
tpt = []
for i in IMPLS:
    m = mean_ms(ref_d, i)
    tpt.append((100000.0 / (m/1000.0)) / 1e6 if m > 0 else 0)
ax.bar(LABELS, tpt, color=COLORS, edgecolor='black', linewidth=0.7)
ax.set_title('Throughput (N=100 k, d=2, k=8, 8 threads)')
ax.set_ylabel('Throughput (million pts/s)'); ax.set_xlabel('Implementation')
plt.xticks(rotation=15, ha='right'); plt.tight_layout()
plt.savefig('results/plots/fig10_throughput.png', dpi=150); plt.close()

print("Saved:", sorted(os.listdir('results/plots')))
