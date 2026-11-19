# Shared-Memory K-Means Clustering (P28 – Cluster H)

**Course:** Multicore Architecture and Programming (CS72)  
**Institution:** Ramaiah Institute of Technology, Bengaluru  
**Department:** Department of Computer Science and Engineering  
**Cluster:** H – K-Means Clustering for Data Analytics  
**Problem ID:** P28  
**Platform:** Shared-Memory Multicore CPU (OpenMP & POSIX Pthreads)  
**Academic Year:** 2026-27  

### Team Members
1. **Arman KB** – USN: `1MS23CS030`
2. **Chiranth DV** – USN: `1MS23CS044`

---

## 1. Project Overview & Research Question
This repository contains the complete **pure C (C11)** implementation, empirical benchmarking suite, and performance evaluation for shared-memory parallel K-Means clustering.

The study answers the fundamental research question:
> *"How do synchronisation strategies, memory layout (AoS vs. SoA), SIMD vectorisation (ARM NEON), and thread-level parallelism (OpenMP vs. POSIX Pthreads) affect the performance and scalability of shared-memory K-Means clustering on modern multicore CPU architectures?"*

### Implemented C11 Algorithmic Kernels
1. **Sequential Reference** (`src/sequential/kmeans_sequential.c`): Optimized single-threaded reference compiled with `-std=c11 -O3 -march=armv8.5-a`.
2. **OpenMP Private Accumulator** (`src/openmp/kmeans_private.c`): Thread-local reduction buffers (`k * d` sums + `k` counts) merged in a single critical block, preventing cache-line contention and false sharing.
3. **OpenMP Atomic Updates** (`src/openmp/kmeans_atomic.c`): Concurrent accumulation using hardware `#pragma omp atomic` instructions.
4. **OpenMP Critical Sections** (`src/openmp/kmeans_critical.c`): Scoped `#pragma omp critical` lock synchronisation for contention analysis.
5. **ARM NEON 128-bit SIMD** (`src/openmp/kmeans_simd.c`): Vectorized Euclidean distance using NEON intrinsics (`float64x2_t`, `vld1q_f64`, `vfmaq_f64`, `vaddvq_f64`) processing two FP64 coordinates per clock cycle with scalar fallback.
6. **AoS vs. SoA Memory Layout** (`src/openmp/kmeans_aos_soa.c`): Direct empirical comparison of contiguous Array-of-Structures (`points[N][d]`) against transposed Structure-of-Arrays (`points[d][N]`).
7. **POSIX Pthreads** (`src/pthreads/kmeans_pthreads.c`): Explicit POSIX multithreading featuring contiguous static block-partitioning and mutex-controlled accumulation.
8. **STREAM Memory Benchmark** (`src/benchmark/stream_mem.c`): Native C11 memory bandwidth benchmark measuring sustained RAM throughput (Copy, Scale, Add, Triad).

---

## 2. Repository Layout
```text
MAP/
├── README.md                               # Comprehensive documentation and reproduction guide
├── LOG.md                                  # Development milestone log
├── Makefile                                # Pure C11 build system (LLVM Clang + libomp)
├── requirements.txt                        # Python dependencies (numpy, matplotlib, python-docx, pypdf)
├── .gitignore                              # Git exclusion rules
├── src/
│   ├── common/
│   │   ├── types.h                         # Canonical structs (Dataset, Centroids, KMeansResult, Layout)
│   │   ├── utils.h / utils.c               # Dataset IO, distance routines, centroid initialization
│   │   └── metrics.h / metrics.c           # High-precision monotonic timers and %.12e CSV logging
│   ├── sequential/
│   │   └── kmeans_sequential.c             # Optimized sequential C11 reference
│   ├── openmp/
│   │   ├── kmeans_private.c                # Thread-private accumulator reduction
│   │   ├── kmeans_atomic.c                 # Atomic updates
│   │   ├── kmeans_critical.c               # Critical section updates
│   │   ├── kmeans_simd.c                   # ARM NEON 128-bit vectorised distance
│   │   └── kmeans_aos_soa.c                # AoS vs SoA memory layout kernels
│   ├── pthreads/
│   │   └── kmeans_pthreads.c               # POSIX Pthreads implementation
│   └── benchmark/
│       ├── benchmark.c                     # Unified benchmark driver (5 runs + 1 warm-up)
│       └── stream_mem.c                    # Authentic STREAM memory bandwidth benchmark
├── scripts/
│   ├── generate_dataset.py                 # Synthetic Gaussian blob generator (fixed seed 42)
│   ├── prepare_real_dataset.py             # Download & parse UCI Iris & Wine real datasets
│   ├── plot_results.py                     # Generates 12 high-resolution performance plots
│   └── make_report.py                      # MSRIT Academic DOCX report generator
├── tests/
│   └── check_correctness.py                # Automated correctness test harness (error <= 1e-6)
├── datasets/
│   ├── synthetic/                          # Generated binary datasets (N=10k to 10M, d=2 to 128, k=8 to 1024)
│   └── real/                               # UCI Iris (N=150, d=4) and Wine (N=178, d=13) datasets
├── results/
│   ├── raw/                                # Raw benchmark CSVs with %.12e precision and stream_bandwidth.csv
│   └── plots/                              # 12 Publication-quality plots (Fig 1 to Fig 12)
├── report/
│   ├── Shared_Memory_KMeans_Report.docx    # Complete 27-page academic DOCX report (MSRIT template)
│   └── Shared_Memory_KMeans_Report.pdf     # Rendered academic PDF report
└── docs/
    ├── architecture.md                     # Multicore kernel architecture & memory hierarchy analysis
    └── methodology.md                      # Benchmarking protocol, metrics, and Roofline formulation
```

---

## 3. Hardware & Software Environment
- **CPU**: Apple M2 (ARM64, ARMv8.5-A, 8 cores: 4 Avalanche P-cores @ 3.49 GHz + 4 Blizzard E-cores @ 2.42 GHz)
- **Caches**: L1 Data: 128 KB (P-core), 64 KB (E-core); L2: 16 MB shared cluster cache; System Level Cache: 8 MB
- **System Memory**: 8 GB Unified LPDDR5-6400 SDRAM (128-bit bus, theoretical peak: 102.4 GB/s)
- **Measured Sustained Bandwidth (STREAM Benchmark)**:
  - **Copy**: `77.44 GB/s`
  - **Scale**: `74.45 GB/s`
  - **Add**: `67.80 GB/s`
  - **Triad**: `69.46 GB/s`
- **Compiler**: Apple LLVM Clang 21.0.0 (Homebrew LLVM 21.1.7)
- **Flags**: `-std=c11 -O3 -march=armv8.5-a -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp -lpthread -lm`
- **Operating System**: macOS Darwin (arm64, Unix 03 compliant)

---

## 4. Build Instructions
```bash
# Build the unified benchmark driver and STREAM memory benchmark
make clean && make all
```
Executables created:
- `bin/benchmark`
- `bin/stream_mem`

---

## 5. Execution & Verification

### Run Correctness Verification Suite
Validates all implementations across thread counts $p \in \{1, 2, 4, 8\}$ ensuring relative error $\le 10^{-6}$:
```bash
make test
# Or directly:
python3 tests/check_correctness.py
```
*Observed relative error across all configurations: $\le 3.5 \times 10^{-14}$ (well below the $10^{-6}$ limit).*

### Run the STREAM Memory Bandwidth Benchmark
```bash
make stream
```

### Run Benchmarks on Synthetic Datasets
```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib ./bin/benchmark datasets/synthetic/N100000_d2_k8.bin 8 results/raw/bench_N100k_d2_k8.csv
```

### Run Benchmarks on Real Datasets
```bash
python3 scripts/prepare_real_dataset.py
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib ./bin/benchmark datasets/real/iris.bin 8 results/raw/bench_real_iris.csv
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib ./bin/benchmark datasets/real/wine.bin 8 results/raw/bench_real_wine.csv
```

---

## 6. Experimental Results & Performance Summary

### A. Core Variant Comparison ($N = 100{,}000$, $d = 2$, $k = 8$, 8 Threads, 5 Runs):
| Implementation | Mean Time (ms) | Std Dev (ms) | Speedup (Sp) | Parallel Eff. (Ep) | Throughput (Mpts/s) | Max Relative Error |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sequential Baseline** | 27.358 | 0.056 | 1.000× | 0.125 | 3.66 | Reference |
| **OpenMP Private Accumulator** | 28.063 | 0.628 | 0.975× | 0.122 | 3.56 | 0.00 |
| **OpenMP Atomic Updates** | 27.793 | 0.099 | 0.984× | 0.123 | 3.60 | 0.00 |
| **OpenMP Critical Section** | 27.659 | 0.098 | 0.989× | 0.124 | 3.62 | 0.00 |
| **OpenMP SIMD (ARM NEON)** | 14.864 | 0.086 | 1.841× | 0.230 | 6.73 | 0.00 |
| **OpenMP AoS** | 27.962 | 0.234 | 0.978× | 0.122 | 3.58 | 0.00 |
| **OpenMP SoA** | 21.132 | 0.124 | 1.295× | 0.162 | 4.73 | 0.00 |
| **POSIX Pthreads** | **6.364** | **0.072** | **4.299×** | **0.537** | **15.71** | $3.86 \times 10^{-16}$ |

### B. AoS vs. SoA Memory Layout Across Dimensionalities ($N = 100{,}000$, $k = 8$, 8 Threads):
| Dimension (d) | OpenMP AoS Time (ms) | OpenMP SoA Time (ms) | AoS Speedup vs SoA | Architectural Finding |
| :---: | :---: | :---: | :---: | :--- |
| **$d = 2$** | 27.962 | 21.132 | 0.75× | SoA slightly faster due to minimal 2-word working set. |
| **$d = 16$** | **13.432** | 25.798 | **1.92×** | Contiguous AoS coordinates maximise L1 cache line utilisation. |
| **$d = 64$** | **83.767** | 160.585 | **1.92×** | SoA suffers severe TLB/cache thrashing across strided dimensions. |
| **$d = 128$** | **165.741** | 302.965 | **1.83×** | AoS maintains spatial locality; SoA takes almost 2× wall-clock time. |

### C. Scaling Across Problem Sizes ($d = 2$, $k = 8$, 8 Threads):
- **$N = 10{,}000$**: Sequential = 2.75 ms, Pthreads = 1.76 ms (Throughput: 5.67 Mpts/s).
- **$N = 100{,}000$**: Sequential = 27.36 ms, Pthreads = 6.36 ms (Throughput: 15.71 Mpts/s, **4.30× speedup**).
- **$N = 1{,}000{,}000$**: Sequential = 277.38 ms, Pthreads = 52.55 ms (Throughput: 19.03 Mpts/s, **5.28× speedup**).
- **$N = 10{,}000{,}000$ (10M points)**: Sequential = 2116.23 ms, Pthreads = 372.31 ms (Throughput: 26.86 Mpts/s, **5.68× speedup**).

### D. Scaling Across Cluster Counts ($N = 100{,}000$, $d = 2$, 8 Threads):
- **$k = 8$**: Sequential = 27.36 ms, SIMD = 14.86 ms, Pthreads = 6.36 ms.
- **$k = 64$**: Sequential = 204.70 ms, SIMD = 112.37 ms, Pthreads = 35.77 ms.
- **$k = 256$**: Sequential = 776.17 ms, SIMD = 569.10 ms, Pthreads = 131.26 ms.
- **$k = 1{,}024$**: Sequential = 3070.02 ms, SIMD = 2364.51 ms, Pthreads = 684.22 ms.

### E. Documented Memory Boundaries:
A dataset of $N = 10^8$ points in $d = 16$ dimensions requires $10^8 \times 16 \times 8 = 12.8\text{ GB}$ points storage plus $800\text{ MB}$ assignments, which exceeds the physical 8 GB RAM of the testbed machine. To prevent operating system memory compression and disk swapping, $N = 10^7$ (10 Million points, requiring ~160 MB points + 80 MB assignments) was benchmarked as the physical upper bound.

---

## 7. Generated Performance Graphs
All 12 high-resolution figures are stored in [`results/plots/`](file:///Users/armank.b/Desktop/map/results/plots/):
- `fig1_time_by_impl.png`: Execution time breakdown across implementations
- `fig2_speedup.png`: Strong scaling speedup curve vs thread count ($p = 1, 2, 4, 8$)
- `fig3_efficiency.png`: Parallel efficiency curves ($E_p = S_p / p$)
- `fig4_time_vs_N.png`: Execution time scaling vs problem size $N$ (10k to 10M, log-log)
- `fig5_omp_sync.png`: Private vs Atomic vs Critical synchronisation comparison across $k$
- `fig6_aos_vs_soa.png`: AoS vs SoA execution time comparison across dimensions $d = 2, 16, 64, 128$
- `fig7_simd_vs_nonsimd.png`: ARM NEON 128-bit SIMD speedup vs scalar baseline
- `fig8_pthreads_vs_omp.png`: Pthreads vs OpenMP runtime execution time across $N$
- `fig9_perf_vs_k.png`: Performance scaling across cluster counts $k = 8, 64, 256, 1024$
- `fig10_perf_vs_d.png`: Performance scaling across dimensionalities $d = 2, 16, 64, 128$
- `fig11_stream_bandwidth.png`: Sustained memory bandwidth measured by STREAM benchmark
- `fig12_throughput.png`: Processing throughput (Million Points processed per second)

---

## 8. Academic Project Reports
The project report strictly preserves the official MSRIT template structure, cover page, and evaluation sheet:
- **Editable Word Report**: [`report/Shared_Memory_KMeans_Report.docx`](https://github.com/Armankb2/MAP/blob/main/report/Shared_Memory_KMeans_Report.docx)
- **Rendered PDF Report (27 pages)**: [`report/Shared_Memory_KMeans_Report.pdf`](https://github.com/Armankb2/MAP/blob/main/report/Shared_Memory_KMeans_Report.pdf)

---

## 9. License
Academic project for Ramaiah Institute of Technology, Department of Computer Science and Engineering. Course CS72. Released under the MIT License.
