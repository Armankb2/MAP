/* Unified benchmark driver for all K-Means implementations */
#include "../common/types.h"
#include "../common/utils.h"
#include "../common/metrics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Forward declarations of all kernel entry points */
KMeansResult kmeans_sequential        (const Dataset *, size_t, real_t);
KMeansResult kmeans_openmp_private    (const Dataset *, size_t, real_t);
KMeansResult kmeans_openmp_atomic     (const Dataset *, size_t, real_t);
KMeansResult kmeans_openmp_critical   (const Dataset *, size_t, real_t);
KMeansResult kmeans_openmp_simd       (const Dataset *, size_t, real_t);
KMeansResult kmeans_pthreads          (const Dataset *, int, size_t, real_t);

#define RUNS 5
#define WARMUP 1

static void free_result(KMeansResult *r) {
    free(r->assignments);
    free(r->centroids.data);
}

static char g_dataset_tag[128] = "unknown";

static void bench(const char *csv, const char *impl, const char *platform,
                  int threads, const Dataset *ds, real_t ref_inertia,
                  KMeansResult (*fn)(const Dataset*, size_t, real_t)) {
    double times[RUNS];
    real_t last_inertia = 0.0;
    for (int r = 0; r < RUNS + WARMUP; ++r) {
        double t0 = now_ms();
        KMeansResult res = fn(ds, 20, 1e-4);
        double t1 = now_ms();
        last_inertia = res.inertia;
        if (r >= WARMUP) times[r - WARMUP] = t1 - t0;
        free_result(&res);
    }
    double mean = 0.0;
    for (int r = 0; r < RUNS; ++r) mean += times[r];
    mean /= RUNS;
    double var = 0.0;
    for (int r = 0; r < RUNS; ++r) { double d = times[r]-mean; var += d*d; }
    double sd = sqrt(var/(RUNS-1));
    double throughput = (double)ds->N / (mean / 1000.0);
    double rel_err = fabs(last_inertia - ref_inertia) / ref_inertia;
    printf("  %-20s  mean=%.3f ms  sd=%.3f ms  tput=%.2e pts/s  err=%.2e\n",
           impl, mean, sd, throughput, rel_err);
    for (int r = 0; r < RUNS; ++r) {
        append_csv_line(csv, "H", "P28", platform, impl,
                        g_dataset_tag, ds->N, threads, r+1,
                        times[r], times[r], 0.0,
                        (double)ds->N/(times[r]/1000.0), rel_err, 0.0);
    }
}

static void bench_pth(const char *csv, int threads, const Dataset *ds, real_t ref_inertia,
                       KMeansResult (*fn)(const Dataset*, int, size_t, real_t)) {
    double times[RUNS];
    real_t last_inertia = 0.0;
    for (int r = 0; r < RUNS + WARMUP; ++r) {
        double t0 = now_ms();
        KMeansResult res = fn(ds, threads, 20, 1e-4);
        double t1 = now_ms();
        last_inertia = res.inertia;
        if (r >= WARMUP) times[r - WARMUP] = t1 - t0;
        free_result(&res);
    }
    double mean = 0.0;
    for (int r = 0; r < RUNS; ++r) mean += times[r];
    mean /= RUNS;
    double var = 0.0;
    for (int r = 0; r < RUNS; ++r) { double d=times[r]-mean; var+=d*d; }
    double sd = sqrt(var/(RUNS-1));
    double throughput = (double)ds->N / (mean / 1000.0);
    double rel_err = fabs(last_inertia - ref_inertia) / ref_inertia;
    printf("  %-20s  mean=%.3f ms  sd=%.3f ms  tput=%.2e pts/s  err=%.2e\n",
           "pthreads", mean, sd, throughput, rel_err);
    for (int r = 0; r < RUNS; ++r) {
        append_csv_line(csv, "H", "P28", "Pthreads", "pthreads",
                        g_dataset_tag, ds->N, threads, r+1,
                        times[r], times[r], 0.0,
                        (double)ds->N/(times[r]/1000.0), rel_err, 0.0);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <dataset.bin> [threads] [csv_path]\n", argv[0]);
        return 1;
    }
    const char *path = argv[1];
    int threads = 4;
    if (argc >= 3) threads = atoi(argv[2]);
    const char *csv = "results/raw/benchmark_H_P28.csv";
    if (argc >= 4) csv = argv[3];

    /* build dataset tag from filename */
    const char *base = strrchr(path, '/');
    base = base ? base+1 : path;
    snprintf(g_dataset_tag, sizeof(g_dataset_tag), "%s", base);

    Dataset ds;
    if (load_dataset(path, &ds) != 0) return 1;
    printf("Dataset: N=%zu  d=%zu  k=%zu\n", ds.N, ds.d, ds.k);

    /* create/init CSV */
    write_csv_header(csv);

    /* ---- reference sequential run ---- */
    printf("Sequential baseline...\n");
    KMeansResult ref = kmeans_sequential(&ds, 20, 1e-4);
    real_t ref_inertia = ref.inertia;
    printf("  ref inertia = %.6f\n", ref_inertia);
    free_result(&ref);

    /* benchmark all implementations */
    printf("\n--- Benchmarks (N=%zu, d=%zu, k=%zu, threads=%d) ---\n",
           ds.N, ds.d, ds.k, threads);

    bench(csv, "sequential",   "Sequential", 1,       &ds, ref_inertia, kmeans_sequential);

    /* set omp threads for all OMP variants */
    extern void omp_set_num_threads(int);
    omp_set_num_threads(threads);

    bench(csv, "omp_private",  "OpenMP", threads, &ds, ref_inertia, kmeans_openmp_private);
    bench(csv, "omp_atomic",   "OpenMP", threads, &ds, ref_inertia, kmeans_openmp_atomic);
    bench(csv, "omp_critical", "OpenMP", threads, &ds, ref_inertia, kmeans_openmp_critical);
    bench(csv, "omp_simd",     "OpenMP", threads, &ds, ref_inertia, kmeans_openmp_simd);
    bench_pth(csv, threads, &ds, ref_inertia, kmeans_pthreads);

    free_dataset(&ds);
    printf("\nResults appended to %s\n", csv);
    return 0;
}
