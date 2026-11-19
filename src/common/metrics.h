#pragma once
#include <stddef.h>

// Return current time in milliseconds (monotonic clock).
double now_ms(void);

// Write CSV header (creates/overwrites the file).
void write_csv_header(const char *path);

// Append a line to CSV file with the required columns.
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
                     double power_w);
