# Shared-Memory K-Means Clustering (P28 – Cluster H)

**Course:** Multicore Architecture and Programming (CS72)  
**Institution:** M.S. Ramaiah Institute of Technology, Bengaluru  
**Department:** Department of Computer Science and Engineering  
**Cluster:** H – K-Means Clustering for Data Analytics  
**Problem ID:** P28  
**Platform:** Shared-Memory Multicore CPU (OpenMP & POSIX Pthreads)

### Team Members
1. **Arman KB** – USN: `1MS23CS030`
2. **Chiranth DV** – USN: `1MS23CS044`

---

## 1. Project Overview
This repository contains a high-performance **pure C (C11)** implementation, benchmarking suite, and performance evaluation of shared-memory parallel K-Means clustering. The research investigates how synchronisation primitives, SIMD vectorisation (ARM NEON), memory layouts (AoS vs SoA), and thread models (OpenMP vs POSIX Pthreads) impact scalability and memory bandwidth utilization.

### Implemented Variants (All Pure C11)
1. **Sequential Baseline** (`src/sequential/kmeans_sequential.c`): Optimized single-threaded reference compiled with `-O3 -march=native`.
2. **OpenMP Private Accumulators** (`src/openmp/kmeans_private.c`): Thread-local centroid sum and count reduction buffers merged via critical section.
3. **OpenMP Atomic Updates** (`src/openmp/kmeans_atomic.c`): Concurrent accumulation using hardware-atomic operations.
4. **OpenMP Critical Sections** (`src/openmp/kmeans_critical.c`): Lock-synchronised accumulation for contention analysis.
5. **SIMD Vectorised Distance** (`src/openmp/kmeans_simd.c`): ARM NEON 128-bit vector arithmetic (`float64x2_t`) with FMA instructions.
6. **AoS vs SoA Memory Layout** (`src/openmp/kmeans_aos_soa.c`): Evaluation of Array-of-Structures vs Structure-of-Arrays cache locality.
7. **POSIX Pthreads** (`src/pthreads/kmeans_pthreads.c`): Custom multi-threaded implementation featuring block-partitioning and mutex-controlled accumulation.

---

## 2. Repository Structure
```text
MAP/
├── README.md                               # Project documentation and reproduction guide
├── LOG.md                                  # Development milestone log
├── Makefile                                # C11 build system (Clang + libomp)
├── requirements.txt                        # Python dependencies for plotting and reports
├── .gitignore                              # Git exclusion rules
├── src/
│   ├── common/
│   │   ├── types.h                         # Shared C11 structs and layout enums
│   │   ├── utils.h / utils.c               # IO, distance calculation, centroid initialization
│   │   └── metrics.h / metrics.c           # Monotonic timers and CSV logging
│   ├── sequential/
│   │   └── kmeans_sequential.c             # Optimized sequential reference
│   ├── openmp/
│   │   ├── kmeans_private.c                # Thread-private accumulator reduction
│   │   ├── kmeans_atomic.c                 # Atomic updates
│   │   ├── kmeans_critical.c               # Critical section updates
│   │   ├── kmeans_simd.c                   # ARM NEON vectorised distance
│   │   └── kmeans_aos_soa.c                # Memory layout comparison
│   ├── pthreads/
│   │   └── kmeans_pthreads.c               # POSIX Pthreads implementation
│   └── benchmark/
│       └── benchmark.c                     # Unified benchmarking driver
├── scripts/
│   ├── generate_dataset.py                 # Synthetic Gaussian blob generator
│   ├── prepare_real_dataset.py             # Download & format UCI Iris & Wine datasets
│   ├── plot_results.py                     # Publication-quality Matplotlib graph generator
│   └── make_report.py                      # MSRIT Academic DOCX report generator
├── tests/
│   └── check_correctness.py                # Automated correctness test harness
├── datasets/
│   ├── synthetic/                          # Generated binary datasets
│   └── real/                               # Real-world benchmark datasets (Iris, Wine)
├── results/
│   ├── raw/                                # Raw benchmark CSV files
│   └── plots/                              # Generated high-resolution performance plots
├── report/
│   ├── Shared_Memory_KMeans_Report.docx    # Complete 27-page academic report (DOCX)
│   └── Shared_Memory_KMeans_Report.pdf     # Verified academic report (PDF)
└── docs/
    ├── architecture.md                     # Kernel architecture and design details
    └── methodology.md                      # Benchmarking protocol and metrics
```

---

## 3. Hardware & Software Environment
- **CPU**: Apple M2 (ARM64, 8 physical cores: 4 Performance + 4 Efficiency)
- **RAM**: 8 GB Unified Memory (LPDDR5-6400, ~100 GB/s bandwidth)
- **Caches**: L1 Data: 128 KB (P-core), L2: 16 MB shared cluster cache
- **SIMD**: ARM NEON (`float64x2_t`)
- **Operating System**: macOS (Darwin 24.x)
- **Compiler**: Homebrew LLVM Clang 21.0.0
- **Flags**: `-std=c11 -O3 -march=armv8.5-a -I/opt/homebrew/opt/libomp/include`
- **Libraries**: `libomp 21.1.7`, `pthread`, `math`

---

## 4. Build Instructions
The project uses standard GNU Make:
```bash
# Clean and build the unified C11 benchmark binary
make clean && make all
```
The compiled executable is placed in `bin/benchmark`.

---

## 5. Execution & Verification

### Run Correctness Tests
Verify all implementations against the sequential reference (ensuring inertia relative error $\le 10^{-6}$):
```bash
python3 tests/check_correctness.py
```

### Run Benchmarks on Synthetic Datasets
```bash
# Generate synthetic Gaussian blobs (N=100,000, d=2, k=8)
python3 scripts/generate_dataset.py --N 100000 --d 2 --k 8 --seed 42 --layout AoS --out datasets/synthetic/N100000_d2_k8.bin

# Run benchmark driver with 8 threads
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib ./bin/benchmark datasets/synthetic/N100000_d2_k8.bin 8 results/raw/bench_N100k_d2_k8.csv
```

### Run Benchmarks on Real Datasets
```bash
# Download and prepare UCI Iris and Wine datasets
python3 scripts/prepare_real_dataset.py

# Benchmark Iris
DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib ./bin/benchmark datasets/real/iris.bin 8 results/raw/bench_real_iris.csv
```

---

## 6. Performance Results Summary
Measured on Apple M2 (ARM64), $N = 100{,}000$, $d = 2$, $k = 8$, 8 threads, 5 measured runs (1 warm-up discarded):

| Implementation | Mean Time (ms) | Std Dev (ms) | Speedup vs Seq | Parallel Efficiency | Max Error vs Seq |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Sequential Baseline** | 27.672 | 0.273 | 1.000× | 0.125 | Reference |
| **OpenMP Private Accumulator** | 27.383 | 0.319 | 1.011× | 0.126 | $0.00$ |
| **OpenMP Atomic Updates** | 27.308 | 0.272 | 1.013× | 0.127 | $0.00$ |
| **OpenMP Critical Section** | 27.546 | 0.312 | 1.005× | 0.126 | $0.00$ |
| **OpenMP SIMD (ARM NEON)** | 14.902 | 0.143 | 1.857× | 0.232 | $0.00$ |
| **POSIX Pthreads** | **6.476** | **0.196** | **4.273×** | **0.534** | $1.93 \times 10^{-16}$ |

---

## 7. Performance Graphs & Reports
- **Generate Plots**: `python3 scripts/plot_results.py` (saved to `results/plots/`)
  - `fig1_time_by_impl.png`: Execution time breakdown
  - `fig2_speedup.png`: Speedup over sequential baseline
  - `fig3_efficiency.png`: Parallel efficiency curves
  - `fig4_time_vs_N.png`: Execution time vs dataset size $N$ (log-log)
  - `fig5_omp_sync.png`: Private vs Atomic vs Critical sync comparison
  - `fig6_simd_vs_nonsimd.png`: ARM NEON vector speedup
  - `fig7_pthreads_vs_omp.png`: Pthreads vs OpenMP comparison
  - `fig8_perf_vs_k.png`: Scaling across cluster count $k$
  - `fig9_perf_vs_d.png`: Scaling across dimension $d$
  - `fig10_throughput.png`: Processing throughput (Million pts/s)
- **Academic Reports**:
  - `report/Shared_Memory_KMeans_Report.docx` (Editable MSRIT template)
  - `report/Shared_Memory_KMeans_Report.pdf` (Rendered 27-page PDF)

---

## 8. License
Academic project for MSRIT CSE Course CS72. Released under the MIT License.
