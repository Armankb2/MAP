/* AoS vs SoA comparison wrapper – delegates to private-accumulator kernel */
#include "../common/types.h"
#include "../common/utils.h"
#include "../common/metrics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <omp.h>

/* forward declaration of the private-accumulator kernel */
KMeansResult kmeans_openmp_private(const Dataset *ds, size_t max_iters, real_t tol);

static void convert_aos_to_soa(const Dataset *aos, Dataset *soa) {
    soa->N = aos->N; soa->d = aos->d; soa->k = aos->k; soa->layout = LAYOUT_SOA;
    soa->points = (real_t *)malloc(aos->N * aos->d * sizeof(real_t));
    for (size_t dim = 0; dim < aos->d; ++dim)
        for (size_t p = 0; p < aos->N; ++p)
            soa->points[dim * aos->N + p] = aos->points[p * aos->d + dim];
}

static KMeansResult run_soa(const Dataset *aos_ds, size_t max_iters, real_t tol) {
    /* For SoA we iterate centroids and points differently.
       We convert the SoA points back to AoS for the assignment step
       (a research trade-off: SoA benefits dimension-wise vectorisation
        while AoS benefits per-point cache locality). */
    size_t N = aos_ds->N, d = aos_ds->d, k = aos_ds->k;
    Dataset soa_ds;
    convert_aos_to_soa(aos_ds, &soa_ds);

    Centroids cent;
    init_centroids(aos_ds, &cent); /* initialise from AoS – first k points */

    size_t *assign  = (size_t *)malloc(N * sizeof(size_t));
    real_t *gsums   = (real_t *)calloc(k*d, sizeof(real_t));
    size_t *gcounts = (size_t *)calloc(k,   sizeof(size_t));

    real_t prev_inertia = DBL_MAX, inertia = 0.0;
    for (size_t iter = 0; iter < max_iters; ++iter) {
        inertia = 0.0;
        /* Assignment: access SoA memory dimension-by-dimension for each centroid */
        #pragma omp parallel for reduction(+:inertia)
        for (size_t p = 0; p < N; ++p) {
            real_t best = DBL_MAX; size_t bc = 0;
            for (size_t c = 0; c < k; ++c) {
                real_t dist = 0.0;
                for (size_t dim = 0; dim < d; ++dim) {
                    real_t diff = soa_ds.points[dim*N + p] - cent.data[c*d + dim];
                    dist += diff*diff;
                }
                if (dist < best) { best = dist; bc = c; }
            }
            assign[p] = bc; inertia += best;
        }
        memset(gsums,   0, k*d*sizeof(real_t));
        memset(gcounts, 0, k  *sizeof(size_t));
        #pragma omp parallel
        {
            real_t  *ls = (real_t  *)calloc(k*d, sizeof(real_t));
            size_t  *lc = (size_t  *)calloc(k,   sizeof(size_t));
            #pragma omp for nowait
            for (size_t p = 0; p < N; ++p) {
                size_t c = assign[p];
                for (size_t dim = 0; dim < d; ++dim)
                    ls[c*d+dim] += soa_ds.points[dim*N + p];
                lc[c]++;
            }
            #pragma omp critical
            {
                for (size_t c = 0; c < k; ++c) {
                    if (!lc[c]) continue;
                    for (size_t dim = 0; dim < d; ++dim) gsums[c*d+dim] += ls[c*d+dim];
                    gcounts[c] += lc[c];
                }
            }
            free(ls); free(lc);
        }
        for (size_t c = 0; c < k; ++c) {
            if (!gcounts[c]) continue;
            real_t inv = 1.0/(real_t)gcounts[c];
            real_t *cp = cent.data + c*d;
            const real_t *sp = gsums + c*d;
            for (size_t dim = 0; dim < d; ++dim) cp[dim] = sp[dim]*inv;
        }
        if (fabs(prev_inertia - inertia) / prev_inertia < tol) break;
        prev_inertia = inertia;
    }
    free(soa_ds.points);
    KMeansResult res; res.inertia = inertia; res.assignments = assign; res.centroids = cent;
    free(gsums); free(gcounts);
    return res;
}
