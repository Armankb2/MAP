# Shared-Memory K-Means Architecture (P28 – Cluster H)

## 1. Overview
This project investigates the shared-memory parallelisation of Lloyd's K-Means clustering algorithm on multicore CPU architectures (specifically Apple Silicon M2, ARM64) using pure C (C11), OpenMP, and POSIX Pthreads.

The core research question addressed:
> "How do synchronisation strategies, memory layout, SIMD vectorisation, and thread-level parallelism affect the performance and scalability of shared-memory K-Means clustering?"

## 2. Kernel Design & Data Structures
All implementations share unified, cache-aligned C structures defined in `src/common/types.h`:

- **Floating-point precision**: Double precision (`real_t = double`) ensuring strict numerical accuracy across parallel reductions.
- **`Dataset`**:
  ```c
  typedef struct {
      size_t N;          // Number of data points
      size_t d;          // Dimensionality
      size_t k;          // Cluster count
      Layout layout;     // LAYOUT_AOS (0) or LAYOUT_SOA (1)
      real_t *points;    // Contiguous flat buffer (N * d)
  } Dataset;
  ```
- **`Centroids`**: Row-major contiguous array (`k * d`), cached in L1/L2 during assignment.
- **`KMeansResult`**: Contains final within-cluster sum of squares (inertia), assignment array, and converged centroids.

## 3. Parallel Architectures & Synchronisation Models

### A. Sequential Reference (`src/sequential/kmeans_sequential.c`)
- Unoptimised single-threaded baseline compiled with `-O3 -march=armv8.5-a`.
- Provides the reference inertia for all speedup, efficiency, and correctness checks.

### B. OpenMP Private Accumulators (`src/openmp/kmeans_private.c`)
- **Principle**: Work-sharing loop over points in the assignment phase.
- **Update**: Each thread allocates a thread-local accumulator buffer (`k * d` floats + `k` counts).
- **Merge**: Merges private buffers into global accumulators in a single `#pragma omp critical` block per thread at the end of the iteration.
- Eliminates false sharing and cache-line bouncing during assignment accumulation.

### C. OpenMP Atomic Updates (`src/openmp/kmeans_atomic.c`)
- **Principle**: Shared centroid sum and count arrays directly updated by concurrent threads.
- **Synchronisation**: `#pragma omp atomic` per dimension update.
- Evaluates hardware atomic contention overhead as cluster count `k` and dimension `d` scale.

### D. OpenMP Critical Section (`src/openmp/kmeans_critical.c`)
- **Principle**: Scoped `#pragma omp critical` block around point-level centroid accumulation.
- Measures worst-case lock contention overhead and serialisation delays.

### E. SIMD / ARM NEON Acceleration (`src/openmp/kmeans_simd.c`)
- **Principle**: Distance calculation optimised with ARM NEON 128-bit vector registers (`float64x2_t`).
- Uses `vld1q_f64`, `vsubq_f64`, `vfmaq_f64` (fused multiply-accumulate), and `vaddvq_f64` (vector horizontal reduction).
- Processes 2 double-precision floating-point coordinates per cycle.

### F. AoS vs SoA Memory Layout (`src/openmp/kmeans_aos_soa.c`)
- **AoS (`points[N][d]`)**: Optimal spatial locality when accessing all dimensions of a single point during nearest-centroid distance computation.
- **SoA (`points[d][N]`)**: Transposed layout enabling contiguous vector loads across points for a fixed dimension.

### G. POSIX Pthreads Architecture (`src/pthreads/kmeans_pthreads.c`)
- Explicit POSIX thread creation, static contiguous block chunking, and thread-local accumulators.
- Mutex-protected reduction into global centroid structures after thread completion.
- Portable across POSIX environments without OpenMP runtime overhead.

## 4. Hardware Characterisation
- **CPU**: Apple M2 (ARMv8.5-A, 8 cores: 4 performance + 4 efficiency)
- **Memory**: 8 GB Unified LPDDR5-6400 (bandwidth ~100 GB/s)
- **Caches**:
  - L1 Data: 128 KB per performance core
  - L2: 16 MB shared cluster cache
- **Compiler**: LLVM Clang 21.0.0 with libomp 21.1.7
