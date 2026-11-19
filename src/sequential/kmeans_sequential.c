#include "../common/types.h"
#include "../common/utils.h"
#include "../common/metrics.h"
#include <stdio.h>
#include <stdlib.h>
#include <float.h>
#include <string.h>
#include <math.h>

// Sequential K-Means implementation – uses utility functions for centroids and distance
KMeansResult kmeans_sequential(const Dataset *data, size_t max_iters, real_t tol) {
    size_t N = data->N, d = data->d, k = data->k;
    const real_t *points = data->points;

    Centroids cent;
    init_centroids(data, &cent);

    size_t *assign = (size_t *)malloc(N * sizeof(size_t));
    real_t *sums = (real_t *)calloc(k * d, sizeof(real_t));
    size_t *counts = (size_t *)calloc(k, sizeof(size_t));

    real_t prev_inertia = DBL_MAX;
    real_t inertia = 0.0;
    for (size_t iter = 0; iter < max_iters; ++iter) {
        inertia = 0.0;
        // Assignment step
        for (size_t p = 0; p < N; ++p) {
            const real_t *pt = points + p * d;
            real_t best_dist = DBL_MAX;
            size_t best_c = 0;
            for (size_t c = 0; c < k; ++c) {
                const real_t *cent_ptr = cent.data + c * d;
                real_t dist = squared_distance(pt, cent_ptr, d);
                if (dist < best_dist) {
                    best_dist = dist;
                    best_c = c;
                }
            }
            assign[p] = best_c;
            inertia += best_dist;
        }
        // Update centroids
        memset(sums, 0, k * d * sizeof(real_t));
        memset(counts, 0, k * sizeof(size_t));
        for (size_t p = 0; p < N; ++p) {
            size_t c = assign[p];
            const real_t *pt = points + p * d;
            real_t *sum = sums + c * d;
            for (size_t dim = 0; dim < d; ++dim) {
                sum[dim] += pt[dim];
            }
            counts[c]++;
        }
        for (size_t c = 0; c < k; ++c) {
            if (counts[c] == 0) continue; // keep previous centroid if empty
            real_t *cent_ptr = cent.data + c * d;
            const real_t *sum_ptr = sums + c * d;
            real_t inv = 1.0 / (real_t)counts[c];
            for (size_t dim = 0; dim < d; ++dim) {
                cent_ptr[dim] = sum_ptr[dim] * inv;
            }
        }
        if (fabs(prev_inertia - inertia) / prev_inertia < tol) {
            break;
        }
        prev_inertia = inertia;
    }
    KMeansResult res;
    res.inertia = inertia;
    res.assignments = assign;
    res.centroids = cent;
    free(sums);
    free(counts);
    return res;
}
