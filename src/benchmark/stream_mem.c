/* 
 * STREAM-style Memory Bandwidth Benchmark in C11
 * Measures Copy, Scale, Add, Triad operations for measuring sustained memory bandwidth.
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <float.h>
#include <omp.h>

#define STREAM_ARRAY_SIZE 10000000  /* 10M elements of double = 80 MB per array, 240 MB total */
#define NTIMES 10

static double a[STREAM_ARRAY_SIZE];
static double b[STREAM_ARRAY_SIZE];
static double c[STREAM_ARRAY_SIZE];

static double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

int main(int argc, char *argv[]) {
    int threads = omp_get_max_threads();
    if (argc >= 2) threads = atoi(argv[1]);
    omp_set_num_threads(threads);

    #pragma omp parallel for
    for (size_t i = 0; i < STREAM_ARRAY_SIZE; ++i) {
        a[i] = 1.0;
        b[i] = 2.0;
        c[i] = 0.0;
    }

    double scalar = 3.0;
    double t_copy = DBL_MAX, t_scale = DBL_MAX, t_add = DBL_MAX, t_triad = DBL_MAX;

    for (int k = 0; k < NTIMES; ++k) {
        /* Copy: c = a */
        double t0 = get_time_sec();
        #pragma omp parallel for
        for (size_t i = 0; i < STREAM_ARRAY_SIZE; ++i) c[i] = a[i];
        double t1 = get_time_sec();
        if (k > 0 && (t1 - t0) < t_copy) t_copy = t1 - t0;

        /* Scale: b = scalar * c */
        t0 = get_time_sec();
        #pragma omp parallel for
        for (size_t i = 0; i < STREAM_ARRAY_SIZE; ++i) b[i] = scalar * c[i];
        t1 = get_time_sec();
        if (k > 0 && (t1 - t0) < t_scale) t_scale = t1 - t0;

        /* Add: c = a + b */
        t0 = get_time_sec();
        #pragma omp parallel for
        for (size_t i = 0; i < STREAM_ARRAY_SIZE; ++i) c[i] = a[i] + b[i];
        t1 = get_time_sec();
        if (k > 0 && (t1 - t0) < t_add) t_add = t1 - t0;

        /* Triad: a = b + scalar * c */
        t0 = get_time_sec();
        #pragma omp parallel for
        for (size_t i = 0; i < STREAM_ARRAY_SIZE; ++i) a[i] = b[i] + scalar * c[i];
        t1 = get_time_sec();
        if (k > 0 && (t1 - t0) < t_triad) t_triad = t1 - t0;
    }

    double bytes_copy  = 2.0 * sizeof(double) * STREAM_ARRAY_SIZE;
    double bytes_scale = 2.0 * sizeof(double) * STREAM_ARRAY_SIZE;
    double bytes_add   = 3.0 * sizeof(double) * STREAM_ARRAY_SIZE;
    double bytes_triad = 3.0 * sizeof(double) * STREAM_ARRAY_SIZE;

    double bw_copy  = (bytes_copy  / t_copy)  / 1e9;
    double bw_scale = (bytes_scale / t_scale) / 1e9;
    double bw_add   = (bytes_add   / t_add)   / 1e9;
    double bw_triad = (bytes_triad / t_triad) / 1e9;

    printf("STREAM Memory Bandwidth Results (threads=%d, array_size=%d doubles):\n", threads, STREAM_ARRAY_SIZE);
    printf("  Copy:  %8.2f GB/s  (best time = %8.6f s)\n", bw_copy,  t_copy);
    printf("  Scale: %8.2f GB/s  (best time = %8.6f s)\n", bw_scale, t_scale);
    printf("  Add:   %8.2f GB/s  (best time = %8.6f s)\n", bw_add,   t_add);
    printf("  Triad: %8.2f GB/s  (best time = %8.6f s)\n", bw_triad, t_triad);

    /* Output machine-readable CSV for inclusion in results/raw/ */
    FILE *f = fopen("results/raw/stream_bandwidth.csv", "w");
    if (f) {
        fprintf(f, "operation,best_time_s,bandwidth_gbs,threads\n");
        fprintf(f, "Copy,%.6f,%.2f,%d\n", t_copy, bw_copy, threads);
        fprintf(f, "Scale,%.6f,%.2f,%d\n", t_scale, bw_scale, threads);
        fprintf(f, "Add,%.6f,%.2f,%d\n", t_add, bw_add, threads);
        fprintf(f, "Triad,%.6f,%.2f,%d\n", t_triad, bw_triad, threads);
        fclose(f);
    }
    return 0;
}
