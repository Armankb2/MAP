# Project Development Log — P28 Shared-Memory K-Means

## Milestone 1: Requirements Analysis & Repository Setup (2026-11-19)
- Cloned GitHub repository `https://github.com/Armankb2/MAP.git`.
- Inspected official course briefs: confirmed Problem P28 in Cluster H (K-Means Clustering for Data Analytics).
- Team allocation confirmed: Arman KB (1MS23CS030) and Chiranth DV (1MS23CS044).
- Extracted official MSRIT Project Report template (`Multicore_Project_Report_Template.docx`).
- Configured directory skeleton: `src/`, `scripts/`, `tests/`, `datasets/`, `results/`, `report/`, `docs/`.

## Milestone 2: Pure C11 Architectural Migration & Headers (2026-11-19)
- Migrated design from C++ to pure C11 standard (`-std=c11`).
- Created canonical headers:
  - `src/common/types.h`: Defined `real_t`, `Dataset`, `Centroids`, `Layout` enum (`LAYOUT_AOS`, `LAYOUT_SOA`), and `KMeansResult`.
  - `src/common/utils.h` / `src/common/utils.c`: Implemented dataset loading, memory cleanup, deterministic centroid initialisation, and squared Euclidean distance.
  - `src/common/metrics.h` / `src/common/metrics.c`: Implemented high-resolution monotonic timer (`clock_gettime`) and standardized CSV logging conforming to Cluster H schema.

## Milestone 3: Implementation of K-Means Kernel Variants (2026-11-19)
- **Sequential Baseline** (`src/sequential/kmeans_sequential.c`): Fully functional, optimized single-threaded reference implementation.
- **OpenMP Private Accumulators** (`src/openmp/kmeans_private.c`): Thread-local centroid accumulators merged via critical section.
- **OpenMP Atomic Updates** (`src/openmp/kmeans_atomic.c`): Direct accumulation using hardware-atomic instructions.
- **OpenMP Critical Sections** (`src/openmp/kmeans_critical.c`): Lock-synchronised centroid updates for contention measurement.
- **SIMD Distance Computation** (`src/openmp/kmeans_simd.c`): ARM NEON 128-bit vectorised distance kernel (`float64x2_t`) using `vfmaq_f64` and horizontal vector reduction.
- **Memory Layout Kernels** (`src/openmp/kmeans_aos_soa.c`): Implemented both `kmeans_openmp_aos` and `kmeans_openmp_soa` for direct empirical cache locality comparison.
- **POSIX Pthreads Implementation** (`src/pthreads/kmeans_pthreads.c`): Thread block-partitioning, private accumulator allocation, and mutex-protected global merge (handling macOS platform nuances).
- **STREAM Memory Bandwidth Benchmark** (`src/benchmark/stream_mem.c`): Authentic C11 memory bandwidth benchmark measuring sustained RAM throughput (Copy, Scale, Add, Triad).

## Milestone 4: Precision & Driver Enhancements (2026-11-19)
- Integrated AoS and SoA implementations directly into `src/benchmark/benchmark.c`.
- Fixed error logging format in `src/common/metrics.c` to scientific notation `%.12e` so non-zero floating-point deviations are preserved accurately.
- Re-architected Makefile to build both `bin/benchmark` and `bin/stream_mem`.

## Milestone 5: Testing & Correctness Verification (2026-11-19)
- Executed automated Python test suite `tests/check_correctness.py`.
- Tested across varying problem sizes ($N=1000$ to $5000$), dimensions ($d=2, 4, 16$), cluster counts ($k=1, 4, 8, 32$), and thread counts (1, 2, 4, 8).
- **Result**: All parallel implementations matched sequential baseline inertia within $< 3.5 \times 10^{-14}$ relative error (well within the required $\le 10^{-6}$ tolerance).

## Milestone 6: Multi-Dimensional Benchmarking & Real Datasets (2026-11-19)
- Evaluated problem sizes up to $N = 10,000,000$ (10M points).
- Evaluated dimensionalities: $d \in \{2, 16, 64, 128\}$.
- Evaluated cluster counts: $k \in \{8, 64, 256, 1024\}$.
- Evaluated real-world datasets: UCI Iris ($N=150, d=4, k=3$) and UCI Wine ($N=178, d=13, k=3$).
- Executed authentic STREAM memory benchmark on Apple M2: Copy = 77.44 GB/s, Scale = 74.45 GB/s, Add = 67.80 GB/s, Triad = 69.46 GB/s.
- Evaluated strong thread scaling across thread counts $p \in \{1, 2, 4, 8\}$.
- All measured runs stored in `results/raw/*.csv`.

## Milestone 7: Performance Plot Suite (2026-11-19)
- Generated 12 publication-quality plots in `results/plots/` using Matplotlib:
  - `fig1_time_by_impl.png`: Execution time breakdown
  - `fig2_speedup.png`: Strong scaling speedup curve
  - `fig3_efficiency.png`: Parallel efficiency curve
  - `fig4_time_vs_N.png`: Execution time vs N (10k to 10M, log-log)
  - `fig5_omp_sync.png`: Private vs Atomic vs Critical sync comparison
  - `fig6_aos_vs_soa.png`: AoS vs SoA comparison across dimensions d=2 to 128
  - `fig7_simd_vs_nonsimd.png`: ARM NEON SIMD speedup across dimensions
  - `fig8_pthreads_vs_omp.png`: Pthreads vs OpenMP comparison across N
  - `fig9_perf_vs_k.png`: Scaling across k=8 to 1024
  - `fig10_perf_vs_d.png`: Scaling across d=2 to 128
  - `fig11_stream_bandwidth.png`: Sustained STREAM memory bandwidth
  - `fig12_throughput.png`: Processing throughput in Mpts/s

## Milestone 8: Academic Report Generation & LaTeX/PDF Export (2026-11-19)
- Formatted complete MSRIT project report using `python-docx` strictly adhering to course template structure, institutional header, and evaluation sheet.
- Set correct Academic Year: 2026-27.
- Replaced hardcoded supervisor with template standard `<Faculty Guide Name>`.
- Verified every scholarly reference in IEEE style.
- Generated `report/Shared_Memory_KMeans_Report.docx` (27 pages).
- Exported and verified `report/Shared_Memory_KMeans_Report.pdf` via native macOS Pages PDF pipeline.

## Milestone 9: Final Review & Git Delivery (2026-11-19)
- Removed all obsolete C++ files.
- Completed comprehensive `README.md`, `docs/architecture.md`, `docs/methodology.md`, and `requirements.txt`.
- Staged, committed, and pushed final project artifacts to GitHub `main` branch.
