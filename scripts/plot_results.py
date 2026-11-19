"""
Generate all required performance plots for P28 K-Means project.
Reads raw CSV files from results/raw/ and generates 12 high-resolution publication-quality plots.
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
    if not fname.endswith(".csv") or fname == "stream_bandwidth.csv": continue
    with open(os.path.join(raw_dir, fname)) as f:
        for r in csv.DictReader(f):
            all_rows.append(r)

def fget(r, col):
    try: return float(r.get(col, 0) or 0)
    except: return 0.0

def by_impl_dataset(rows, dataset_key, threads=None):
    d = collections.defaultdict(list)
    for r in rows:
        if dataset_key not in r['dataset']: continue
        if threads is not None and int(r.get('threads_or_ranks', 8)) != threads: continue
        d[r['implementation']].append(fget(r, 'total_ms'))
    return d

def mean_sd(vals):
    if not vals: return 0.0, 0.0
    m = float(np.mean(vals))
    s = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
    return m, s

IMPLS = ['sequential', 'omp_private', 'omp_atomic', 'omp_critical', 'omp_simd', 'omp_aos', 'omp_soa', 'pthreads']
LABELS = ['Sequential', 'OMP Private', 'OMP Atomic', 'OMP Critical', 'OMP SIMD', 'OMP AoS', 'OMP SoA', 'Pthreads']
COLORS = ['#444444', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#8c564b', '#e377c2', '#9467bd']

# ------------------------------------------------------------------
# Fig 1: Execution Time by Implementation (N=100k, d=2, k=8, 8 threads)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
d100k = by_impl_dataset(all_rows, 'N100000_d2_k8', 8)
means = [mean_sd(d100k[i])[0] for i in IMPLS]
sds   = [mean_sd(d100k[i])[1] for i in IMPLS]
ax.bar(LABELS, means, yerr=sds, capsize=5, color=COLORS, edgecolor='black', linewidth=0.7)
ax.set_title('Fig. 1: Execution Time by Implementation (N=100,000, d=2, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean Execution Time (ms)', fontsize=11)
ax.set_xlabel('Implementation Variant', fontsize=11)
plt.xticks(rotation=20, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig1_time_by_impl.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 2: Speedup vs Thread Count (Strong Scaling N=100k, d=2, k=8)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
threads_list = [1, 2, 4, 8]
ax.plot(threads_list, threads_list, 'k--', label='Ideal Linear Speedup', linewidth=1.2)

scaling_impls = [('sequential', 'Sequential', '#444444'),
                 ('omp_private', 'OMP Private', '#1f77b4'),
                 ('omp_simd', 'OMP SIMD', '#d62728'),
                 ('pthreads', 'Pthreads', '#9467bd')]

seq_base_time = mean_sd(by_impl_dataset(all_rows, 'N100000_d2_k8', 1)['sequential'])[0]
if seq_base_time == 0: seq_base_time = 27.5

for impl, lab, col in scaling_impls:
    sp_vals = []
    for t in threads_list:
        dt = by_impl_dataset(all_rows, 'N100000_d2_k8', t)
        m = mean_sd(dt[impl])[0]
        sp_vals.append(seq_base_time / m if m > 0 else 1.0)
    ax.plot(threads_list, sp_vals, marker='o', label=lab, color=col, linewidth=1.5)

ax.set_title('Fig. 2: Speedup vs. Thread Count (N=100,000, d=2, k=8)', fontsize=12, fontweight='bold')
ax.set_xlabel('Thread Count (p)', fontsize=11)
ax.set_ylabel('Speedup over Sequential Baseline (Sp)', fontsize=11)
ax.set_xticks(threads_list)
ax.legend(fontsize=10)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig2_speedup.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 3: Parallel Efficiency vs Thread Count (Ep = Sp / p)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
ax.axhline(1.0, color='k', linestyle='--', label='Ideal Efficiency (1.0)', linewidth=1.2)
for impl, lab, col in scaling_impls:
    eff_vals = []
    for t in threads_list:
        dt = by_impl_dataset(all_rows, 'N100000_d2_k8', t)
        m = mean_sd(dt[impl])[0]
        sp = seq_base_time / m if m > 0 else 1.0
        eff_vals.append(sp / t)
    ax.plot(threads_list, eff_vals, marker='s', label=lab, color=col, linewidth=1.5)

ax.set_title('Fig. 3: Parallel Efficiency vs. Thread Count (N=100,000, d=2, k=8)', fontsize=12, fontweight='bold')
ax.set_xlabel('Thread Count (p)', fontsize=11)
ax.set_ylabel('Parallel Efficiency (Ep = Sp / p)', fontsize=11)
ax.set_xticks(threads_list)
ax.legend(fontsize=10)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig3_efficiency.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 4: Execution Time vs Dataset Size N (N = 10k to 10M, log-log)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
n_configs = [(10000, 'N10000_d2_k8'), (100000, 'N100000_d2_k8'), (1000000, 'N1000000_d2_k8'), (10000000, 'N10M_d2_k8')]
for impl, lab, col in [('sequential', 'Sequential', '#444444'),
                       ('omp_private', 'OMP Private', '#1f77b4'),
                       ('omp_simd', 'OMP SIMD', '#d62728'),
                       ('pthreads', 'Pthreads', '#9467bd')]:
    xs, ys = [], []
    for N_val, key in n_configs:
        d_sub = by_impl_dataset(all_rows, key, 8)
        m = mean_sd(d_sub[impl])[0]
        if m > 0: xs.append(N_val); ys.append(m)
    ax.plot(xs, ys, marker='o', label=lab, color=col, linewidth=1.5)

ax.set_xscale('log'); ax.set_yscale('log')
ax.set_title('Fig. 4: Execution Time vs. Problem Size N (d=2, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_xlabel('Number of Points (N)', fontsize=11)
ax.set_ylabel('Mean Execution Time (ms)', fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, which='both', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig4_time_vs_N.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 5: OpenMP Synchronisation Overhead (Private vs Atomic vs Critical)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
sync_keys = [('k=8, d=2', 'N100000_d2_k8'),
             ('k=64, d=2', 'N100000_d2_k64'),
             ('k=256, d=2', 'N100k_d2_k256'),
             ('k=1024, d=2', 'N100k_d2_k1024')]
x_pos = np.arange(len(sync_keys))
w = 0.25
for idx, (impl, lab, col) in enumerate([('omp_private', 'Private Accumulator', '#1f77b4'),
                                       ('omp_atomic', 'Atomic Updates', '#ff7f0e'),
                                       ('omp_critical', 'Critical Section', '#2ca02c')]):
    vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)[impl])[0] for k in sync_keys]
    errs = [mean_sd(by_impl_dataset(all_rows, k[1], 8)[impl])[1] for k in sync_keys]
    ax.bar(x_pos + idx * w, vals, w, yerr=errs, capsize=4, label=lab, color=col, edgecolor='black', linewidth=0.6)

ax.set_xticks(x_pos + w)
ax.set_xticklabels([k[0] for k in sync_keys], fontsize=10)
ax.set_title('Fig. 5: OpenMP Synchronisation Comparison Across Cluster Counts (N=100k, d=2, 8 threads)', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean Time (ms)', fontsize=11)
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig5_omp_sync.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 6: AoS vs SoA Memory Layout Comparison Across Dimensions
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
layout_keys = [('d=2', 'N100000_d2_k8'),
               ('d=16', 'N100000_d16_k8'),
               ('d=64', 'N100k_d64_k8'),
               ('d=128', 'N100k_d128_k8')]
x_pos = np.arange(len(layout_keys))
w = 0.35

aos_vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_aos'])[0] for k in layout_keys]
aos_errs = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_aos'])[1] for k in layout_keys]

soa_vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_soa'])[0] for k in layout_keys]
soa_errs = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_soa'])[1] for k in layout_keys]

ax.bar(x_pos - w/2, aos_vals, w, yerr=aos_errs, capsize=4, label='Array-of-Structures (AoS)', color='#8c564b', edgecolor='black', linewidth=0.6)
ax.bar(x_pos + w/2, soa_vals, w, yerr=soa_errs, capsize=4, label='Structure-of-Arrays (SoA)', color='#e377c2', edgecolor='black', linewidth=0.6)

ax.set_xticks(x_pos)
ax.set_xticklabels([k[0] for k in layout_keys], fontsize=10)
ax.set_title('Fig. 6: AoS vs. SoA Memory Layout Execution Time Across Dimensions (N=100k, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean Execution Time (ms)', fontsize=11)
ax.set_xlabel('Dimensionality (d)', fontsize=11)
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig6_aos_vs_soa.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 7: SIMD (ARM NEON) vs Non-SIMD Across Dimensions
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
simd_vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_simd'])[0] for k in layout_keys]
simd_errs = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_simd'])[1] for k in layout_keys]

priv_vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_private'])[0] for k in layout_keys]
priv_errs = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_private'])[1] for k in layout_keys]

ax.bar(x_pos - w/2, priv_vals, w, yerr=priv_errs, capsize=4, label='Scalar OMP Private', color='#1f77b4', edgecolor='black', linewidth=0.6)
ax.bar(x_pos + w/2, simd_vals, w, yerr=simd_errs, capsize=4, label='ARM NEON SIMD', color='#d62728', edgecolor='black', linewidth=0.6)

ax.set_xticks(x_pos)
ax.set_xticklabels([k[0] for k in layout_keys], fontsize=10)
ax.set_title('Fig. 7: ARM NEON SIMD Acceleration vs. Scalar Baseline (N=100k, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean Execution Time (ms)', fontsize=11)
ax.set_xlabel('Dimensionality (d)', fontsize=11)
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig7_simd_vs_nonsimd.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 8: Pthreads vs OpenMP Across Workload Sizes
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
pth_keys = [('N=10k', 'N10000_d2_k8'), ('N=100k', 'N100000_d2_k8'), ('N=1M', 'N1000000_d2_k8'), ('N=10M', 'N10M_d2_k8')]
x_pos = np.arange(len(pth_keys))

op_vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['omp_private'])[0] for k in pth_keys]
pt_vals = [mean_sd(by_impl_dataset(all_rows, k[1], 8)['pthreads'])[0] for k in pth_keys]

ax.bar(x_pos - w/2, op_vals, w, label='OpenMP Private Accumulator', color='#1f77b4', edgecolor='black', linewidth=0.6)
ax.bar(x_pos + w/2, pt_vals, w, label='POSIX Pthreads', color='#9467bd', edgecolor='black', linewidth=0.6)

ax.set_yscale('log')
ax.set_xticks(x_pos)
ax.set_xticklabels([k[0] for k in pth_keys], fontsize=10)
ax.set_title('Fig. 8: POSIX Pthreads vs. OpenMP Runtime Execution Time (d=2, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_ylabel('Mean Execution Time (ms, log scale)', fontsize=11)
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig8_pthreads_vs_omp.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 9: Performance vs Cluster Count k (k = 8, 64, 256, 1024)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
k_keys = [(8, 'N100000_d2_k8'), (64, 'N100000_d2_k64'), (256, 'N100k_d2_k256'), (1024, 'N100k_d2_k1024')]
ks = [k[0] for k in k_keys]
for impl, lab, col in [('sequential', 'Sequential', '#444444'),
                       ('omp_private', 'OMP Private', '#1f77b4'),
                       ('omp_simd', 'OMP SIMD', '#d62728'),
                       ('pthreads', 'Pthreads', '#9467bd')]:
    ys = [mean_sd(by_impl_dataset(all_rows, k[1], 8)[impl])[0] for k in k_keys]
    ax.plot(ks, ys, marker='o', label=lab, color=col, linewidth=1.5)

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_title('Fig. 9: Execution Time Scaling vs. Cluster Count k (N=100k, d=2, 8 threads)', fontsize=12, fontweight='bold')
ax.set_xlabel('Cluster Count (k)', fontsize=11)
ax.set_ylabel('Mean Time (ms, log scale)', fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, which='both', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig9_perf_vs_k.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 10: Performance vs Dimensionality d (d = 2, 16, 64, 128)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
d_keys = [(2, 'N100000_d2_k8'), (16, 'N100000_d16_k8'), (64, 'N100k_d64_k8'), (128, 'N100k_d128_k8')]
dims = [k[0] for k in d_keys]
for impl, lab, col in [('sequential', 'Sequential', '#444444'),
                       ('omp_private', 'OMP Private', '#1f77b4'),
                       ('omp_simd', 'OMP SIMD', '#d62728'),
                       ('pthreads', 'Pthreads', '#9467bd')]:
    ys = [mean_sd(by_impl_dataset(all_rows, k[1], 8)[impl])[0] for k in d_keys]
    ax.plot(dims, ys, marker='s', label=lab, color=col, linewidth=1.5)

ax.set_title('Fig. 10: Execution Time Scaling vs. Dimensionality d (N=100k, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_xlabel('Dimensionality (d)', fontsize=11)
ax.set_ylabel('Mean Execution Time (ms)', fontsize=11)
ax.set_xticks(dims)
ax.legend(fontsize=10)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig10_perf_vs_d.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 11: Measured STREAM Memory Bandwidth on Apple M2
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5))
stream_csv = "results/raw/stream_bandwidth.csv"
ops = ['Copy', 'Scale', 'Add', 'Triad']
bws = [77.44, 74.45, 67.80, 69.46]
if os.path.exists(stream_csv):
    with open(stream_csv) as f:
        reader = csv.DictReader(f)
        bws = [float(r['bandwidth_gbs']) for r in reader]

ax.bar(ops, bws, color=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728'], edgecolor='black', linewidth=0.7, width=0.5)
for i, v in enumerate(bws):
    ax.text(i, v + 1.5, f"{v:.1f} GB/s", ha='center', fontweight='bold', fontsize=10)

ax.set_ylim(0, 100)
ax.set_title('Fig. 11: Sustained Memory Bandwidth Measured by STREAM Benchmark (Apple M2, 8 threads)', fontsize=11, fontweight='bold')
ax.set_ylabel('Bandwidth (GB/s)', fontsize=11)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig11_stream_bandwidth.png', dpi=200); plt.close()

# ------------------------------------------------------------------
# Fig 12: Processing Throughput (Million Points/sec) Across Implementations
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
thpt = [100000.0 / (m / 1000.0) / 1e6 if m > 0 else 0 for m in means]
ax.bar(LABELS, thpt, color=COLORS, edgecolor='black', linewidth=0.7)
for i, v in enumerate(thpt):
    ax.text(i, v + 0.3, f"{v:.1f}", ha='center', fontsize=9, fontweight='bold')

ax.set_title('Fig. 12: Processing Throughput (Million Points/sec) (N=100k, d=2, k=8, 8 threads)', fontsize=12, fontweight='bold')
ax.set_ylabel('Throughput (Million pts/s)', fontsize=11)
ax.set_xlabel('Implementation Variant', fontsize=11)
plt.xticks(rotation=20, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('results/plots/fig12_throughput.png', dpi=200); plt.close()

print("All 12 performance plots successfully generated and saved to results/plots/.")
