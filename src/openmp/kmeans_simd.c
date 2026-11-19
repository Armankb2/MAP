#include "../common/types.h"
#include "../common/utils.h"
#include "../common/metrics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <omp.h>

/* ARM NEON SIMD for distance – falls back to scalar on non-NEON targets */
#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>

static real_t squared_distance_neon(const real_t *a, const real_t *b, size_t d) {
    float64x2_t acc = vdupq_n_f64(0.0);
    size_t i = 0;
    for (; i + 1 < d; i += 2) {
        float64x2_t va = vld1q_f64(a + i);
        float64x2_t vb = vld1q_f64(b + i);
        float64x2_t diff = vsubq_f64(va, vb);
        acc = vfmaq_f64(acc, diff, diff);
    }
    real_t sum = vaddvq_f64(acc);
    for (; i < d; ++i) { real_t diff = a[i]-b[i]; sum += diff*diff; }
    return sum;
}
#define DIST(a,b,d) squared_distance_neon(a,b,d)
#else
#define DIST(a,b,d) squared_distance(a,b,d)
#endif

KMeansResult kmeans_openmp_simd(const Dataset *ds, size_t max_iters, real_t tol) {
    size_t N = ds->N, d = ds->d, k = ds->k;
    const real_t *points = ds->points;
    Centroids cent;
    init_centroids(ds, &cent);
    size_t *assign  = (size_t *)malloc(N * sizeof(size_t));
    real_t *gsums   = (real_t *)calloc(k*d, sizeof(real_t));
    size_t *gcounts = (size_t *)calloc(k,   sizeof(size_t));
    real_t prev_inertia = DBL_MAX, inertia = 0.0;
    for (size_t iter = 0; iter < max_iters; ++iter) {
        inertia = 0.0;
        #pragma omp parallel for reduction(+:inertia)
        for (size_t p = 0; p < N; ++p) {
            const real_t *pt = points + p*d;
            real_t best = DBL_MAX; size_t bc = 0;
            for (size_t c = 0; c < k; ++c) {
                real_t dist = DIST(pt, cent.data + c*d, d);
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
                const real_t *pt = points + p*d;
                real_t *s = ls + c*d;
                for (size_t dim = 0; dim < d; ++dim) s[dim] += pt[dim];
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
    KMeansResult res; res.inertia = inertia; res.assignments = assign; res.centroids = cent;
    free(gsums); free(gcounts);
    return res;
}
