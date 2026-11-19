#include "metrics.h"
#include <time.h>
#include <stdio.h>

double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}

void write_csv_header(const char *path) {
    FILE *f = fopen(path, "w");
    if (!f) return;
    fprintf(f, "cluster,problem,platform,implementation,dataset,size,threads_or_ranks,run_id,total_ms,kernel_ms,transfer_ms,throughput,error,power_w\n");
    fclose(f);
}

void append_csv_line(const char *path,
                     const char *cluster,
                     const char *problem,
                     const char *platform,
                     const char *implementation,
                     const char *dataset,
                     size_t size,
                     int threads,
                     int run_id,
                     double total_ms,
                     double kernel_ms,
                     double transfer_ms,
                     double throughput,
                     double error,
                     double power_w) {
    FILE *f = fopen(path, "a");
    if (!f) return;
    fprintf(f, "%s,%s,%s,%s,%s,%zu,%d,%d,%.3f,%.3f,%.3f,%.3f,%.12e,%.6f\n",
            cluster, problem, platform, implementation, dataset, size, threads, run_id,
            total_ms, kernel_ms, transfer_ms, throughput, error, power_w);
    fclose(f);
}
