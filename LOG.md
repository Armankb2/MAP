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
- **Memory Layout Comparison** (`src/openmp/kmeans_aos_soa.c`): Comparison between Array-of-Structures (AoS) and Structure-of-Arrays (SoA).
- **POSIX Pthreads Implementation** (`src/pthreads/kmeans_pthreads.c`): Thread block-partitioning, private accumulator allocation, and mutex-protected global merge (handling macOS platform nuances).

## Milestone 4: Build System & Toolchain Configuration (2026-11-19)
- Configured Makefile using Homebrew LLVM Clang (`/opt/homebrew/opt/llvm/bin/clang`) and `libomp 21.1.7`.
- Flags: `-std=c11 -O3 -march=armv8.5-a -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp -lpthread -lm`.
- Resolved multi-main symbol duplication by consolidating entry points into `src/benchmark/benchmark.c`.

## Milestone 5: Testing & Correctness Verification (2026-11-19)
- Built automated Python test suite `tests/check_correctness.py`.
- Tested across varying problem sizes ($N=1000$ to $5000$), dimensions ($d=2, 4, 16$), cluster counts ($k=1, 4, 8, 32$), and thread counts (1, 2, 4, 8).
- **Result**: All parallel implementations matched sequential baseline inertia within $< 10^{-15}$ relative error (well within the required $\le 10^{-6}$ tolerance).

## Milestone 6: Experimental Benchmarking & Plot Generation (2026-11-19)
- Synthetic datasets generated: $N=10\text{k}, 100\text{k}, 1\text{M}$; $d=2, 16$; $k=8, 64$; fixed seed 42.
- Real datasets prepared: UCI Iris and UCI Wine datasets.
- Executed 5 measured runs + 1 warm-up run per configuration. Recorded mean, standard deviation, speedup, efficiency, and throughput into `results/raw/*.csv`.
- Generated 10 publication-quality graphs using Matplotlib (`scripts/plot_results.py`):
  - Execution time, speedup, efficiency, $N$-scaling, synchronisation overhead, SIMD vs scalar, Pthreads vs OpenMP, $k$-scaling, $d$-scaling, and throughput.

## Milestone 7: Academic Report Generation (2026-11-19)
- Formatted complete MSRIT project report using `python-docx` adhering strictly to course template structure.
- Generated `report/Shared_Memory_KMeans_Report.docx` (27 pages).
- Exported and verified `report/Shared_Memory_KMeans_Report.pdf` via native macOS Pages PDF pipeline.

## Milestone 8: Final Review & Git Delivery (2026-11-19)
- Removed all obsolete C++ files.
- Completed comprehensive `README.md`, `docs/architecture.md`, `docs/methodology.md`, and `requirements.txt`.
- Staged, committed, and pushed final project artifacts to GitHub `main` branch.
