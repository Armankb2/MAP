#include "../common/types.h"
#include "../common/utils.h"
#include "../common/metrics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <omp.h>

KMeansResult kmeans_openmp_private(const Dataset *ds, size_t max_iters, real_t tol) {
    size_t N = ds->N, d = ds->d, k = ds->k;
    const real_t *points = ds->points;
    Centroids cent;
    init_centroids(ds, &cent);
    size_t *assign  = (size_t *)malloc(N * sizeof(size_t));
    real_t *gsums   = (real_t *)calloc(k * d, sizeof(real_t));
    size_t *gcounts = (size_t *)calloc(k,     sizeof(size_t));
    real_t prev_inertia = DBL_MAX, inertia = 0.0;
    for (size_t iter = 0; iter < max_iters; ++iter) {
        inertia = 0.0;
        /* ---- assignment ---- */
        #pragma omp parallel for reduction(+:inertia)
        for (size_t p = 0; p < N; ++p) {
            const real_t *pt = points + p * d;
            real_t best = DBL_MAX; size_t bc = 0;
            for (size_t c = 0; c < k; ++c) {
                real_t dist = squared_distance(pt, cent.data + c * d, d);
                if (dist < best) { best = dist; bc = c; }
            }
            assign[p] = bc; inertia += best;
        }
        /* ---- update with private accumulators ---- */
        memset(gsums,   0, k * d * sizeof(real_t));
        memset(gcounts, 0, k     * sizeof(size_t));
        #pragma omp parallel
        {
            real_t  *lsums   = (real_t  *)calloc(k * d, sizeof(real_t));
            size_t  *lcounts = (size_t  *)calloc(k,     sizeof(size_t));
            #pragma omp for nowait
            for (size_t p = 0; p < N; ++p) {
                size_t c = assign[p];
                const real_t *pt = points + p * d;
                real_t *s = lsums + c * d;
                for (size_t dim = 0; dim < d; ++dim) s[dim] += pt[dim];
                lcounts[c]++;
            }
            #pragma omp critical
            {
                for (size_t c = 0; c < k; ++c) {
                    if (!lcounts[c]) continue;
                    for (size_t dim = 0; dim < d; ++dim)
                        gsums[c*d+dim] += lsums[c*d+dim];
                    gcounts[c] += lcounts[c];
                }
            }
            free(lsums); free(lcounts);
        }
        for (size_t c = 0; c < k; ++c) {
            if (!gcounts[c]) continue;
            real_t inv = 1.0 / (real_t)gcounts[c];
            real_t *cp = cent.data + c*d;
            const real_t *sp = gsums + c*d;
            for (size_t dim = 0; dim < d; ++dim) cp[dim] = sp[dim]*inv;
        }
        if (fabs(prev_inertia - inertia) / prev_inertia < tol) break;
        prev_inertia = inertia;
    }
    KMeansResult res; res.inertia = inertia; res.assignments = assign; res.centroids = cent;
    free(gsums); free(gcounts);
    return res;
}
