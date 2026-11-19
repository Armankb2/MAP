# Experimental Methodology & Benchmarking Baseline

## 1. Experimental Protocol
To ensure rigorous and reproducible results, the benchmarking suite strictly follows the MSRIT CS72 Common Baseline guidelines:

1. **Repetitions & Warm-up**:
   - Each benchmark configuration is run **5 times** consecutively.
   - The first run is strictly treated as a warm-up run (to prime OS page caches, branch predictors, and CPU frequency governor) and discarded from statistical calculations.
   - Execution times reported are the arithmetic mean and sample standard deviation over the subsequent 5 runs.

2. **Deterministic Inputs**:
   - Fixed pseudo-random seed (`seed = 42` for synthetic datasets, `seed = 123` for correctness tests).
   - Centroids are initialised identically across all algorithms using the first $k$ points of the dataset.
   - Consistent stopping criteria: maximum 20 iterations or relative centroid shift tolerance $\Delta < 1 \times 10^{-4}$.

3. **Correctness & Error Verification**:
   - Every parallel execution must match the sequential reference inertia within a relative tolerance $\le 1 \times 10^{-6}$:
     $$\text{Relative Error} = \frac{|J_{\text{parallel}} - J_{\text{seq}}|}{J_{\text{seq}}} \le 10^{-6}$$
   - Any floating-point variation strictly stems from non-associative parallel summation ordering.

## 2. Performance Metrics & Formulations

- **Speedup ($S_p$)**:
  $$S_p = \frac{T_{\text{sequential}}}{T_{\text{parallel}}(p)}$$
  where $T_{\text{sequential}}$ is measured on the fully optimised single-threaded baseline compiled with `-O3 -march=native`.

- **Parallel Efficiency ($E_p$)**:
  $$E_p = \frac{S_p}{p}$$
  where $p$ is the thread count.

- **Throughput ($\Phi$)**:
  $$\Phi = \frac{N}{T_{\text{execution}}} \quad (\text{points / second})$$

## 3. CSV Output Schema
All benchmark outputs are recorded in standardized CSV files adhering to the Cluster H common baseline:
```csv
cluster,problem,platform,implementation,dataset,size,threads_or_ranks,run_id,total_ms,kernel_ms,transfer_ms,throughput,error,power_w
```
- `cluster`: `H`
- `problem`: `P28`
- `platform`: `Sequential` | `OpenMP` | `Pthreads`
- `implementation`: `sequential` | `omp_private` | `omp_atomic` | `omp_critical` | `omp_simd` | `pthreads`
- `dataset`: Binary dataset filename
- `size`: Number of points $N$
- `threads_or_ranks`: 1, 2, 4, 8
- `run_id`: 1 through 5
- `total_ms`: Wall-clock execution time in milliseconds
- `throughput`: Points processed per second
- `error`: Relative inertia error vs. sequential reference
