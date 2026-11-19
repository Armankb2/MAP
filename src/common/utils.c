#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int load_dataset(const char *path, Dataset *out) {
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        perror("fopen");
        return 1;
    }
    uint64_t N, d, k; uint8_t lay;
    if (fread(&N, sizeof(uint64_t), 1, fp) != 1) { fclose(fp); return 1; }
    if (fread(&d, sizeof(uint64_t), 1, fp) != 1) { fclose(fp); return 1; }
    if (fread(&k, sizeof(uint64_t), 1, fp) != 1) { fclose(fp); return 1; }
    if (fread(&lay, sizeof(uint8_t), 1, fp) != 1) { fclose(fp); return 1; }
    out->N = (size_t)N;
    out->d = (size_t)d;
    out->k = (size_t)k;
    out->layout = (lay == 0) ? LAYOUT_AOS : LAYOUT_SOA;
    out->points = (real_t *)malloc(out->N * out->d * sizeof(real_t));
    if (!out->points) { fclose(fp); return 1; }
    size_t read = fread(out->points, sizeof(real_t), out->N * out->d, fp);
    fclose(fp);
    return (read == out->N * out->d) ? 0 : 1;
}

void free_dataset(Dataset *ds) {
    if (ds->points) free(ds->points);
    ds->points = NULL;
    ds->N = ds->d = ds->k = 0;
}

void init_centroids(const Dataset *ds, Centroids *cent) {
    cent->k = ds->k;
    cent->d = ds->d;
    cent->data = (real_t *)calloc(cent->k * cent->d, sizeof(real_t));
    for (size_t i = 0; i < cent->k; ++i) {
        const real_t *src = ds->points + i * ds->d; // first k points (AoS assumed)
        real_t *dst = cent->data + i * ds->d;
        memcpy(dst, src, ds->d * sizeof(real_t));
    }
}

real_t squared_distance(const real_t *a, const real_t *b, size_t d) {
    real_t sum = 0.0;
    for (size_t i = 0; i < d; ++i) {
        real_t diff = a[i] - b[i];
        sum += diff * diff;
    }
    return sum;
}
