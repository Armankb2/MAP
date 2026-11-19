#include "../common/types.h"
#include "../common/utils.h"
#include "../common/metrics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <pthread.h>

#define MAX_THREADS 64

typedef struct {
    int id;
    int num_threads;
    size_t N, d, k;
    const real_t *points;
    real_t  *cent_data;   /* shared: read-only during assignment, written after join */
    size_t  *assign;      /* shared output */
    real_t   local_inertia;
    real_t  *local_sums;
    size_t  *local_counts;
    real_t  *global_sums;
    size_t  *global_counts;
    pthread_mutex_t *mutex;
} ThreadArgs;

static void *worker(void *arg) {
    ThreadArgs *a = (ThreadArgs *)arg;
    size_t N = a->N, d = a->d, k = a->k;

    size_t chunk = (N + (size_t)a->num_threads - 1) / (size_t)a->num_threads;
    size_t start = (size_t)a->id * chunk;
    size_t end   = start + chunk;
    if (end > N) end = N;

    /* ---- assignment ---- */
    a->local_inertia = 0.0;
    for (size_t p = start; p < end; ++p) {
        const real_t *pt = a->points + p * d;
        real_t best = DBL_MAX; size_t bc = 0;
        for (size_t c = 0; c < k; ++c) {
            const real_t *cp = a->cent_data + c * d;
            real_t dist = 0.0;
            for (size_t dim = 0; dim < d; ++dim) {
                real_t diff = pt[dim] - cp[dim];
                dist += diff * diff;
            }
            if (dist < best) { best = dist; bc = c; }
        }
        a->assign[p] = bc;
        a->local_inertia += best;
    }

    /* ---- local accumulation ---- */
    memset(a->local_sums,   0, k * d * sizeof(real_t));
    memset(a->local_counts, 0, k     * sizeof(size_t));
    for (size_t p = start; p < end; ++p) {
        size_t c = a->assign[p];
        const real_t *pt = a->points + p * d;
        real_t *s = a->local_sums + c * d;
        for (size_t dim = 0; dim < d; ++dim) s[dim] += pt[dim];
        a->local_counts[c]++;
    }

    /* ---- merge into global ---- */
    pthread_mutex_lock(a->mutex);
    for (size_t c = 0; c < k; ++c) {
        if (!a->local_counts[c]) continue;
        for (size_t dim = 0; dim < d; ++dim)
            a->global_sums[c*d+dim] += a->local_sums[c*d+dim];
        a->global_counts[c] += a->local_counts[c];
    }
    pthread_mutex_unlock(a->mutex);

    return NULL;
}

KMeansResult kmeans_pthreads(const Dataset *ds, int num_threads, size_t max_iters, real_t tol) {
    size_t N = ds->N, d = ds->d, k = ds->k;
    if (num_threads > MAX_THREADS) num_threads = MAX_THREADS;

    Centroids cent;
    init_centroids(ds, &cent);
    size_t  *assign  = (size_t  *)malloc(N * sizeof(size_t));
    real_t  *gsums   = (real_t  *)calloc(k * d, sizeof(real_t));
    size_t  *gcounts = (size_t  *)calloc(k,     sizeof(size_t));
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

    real_t  **lsums   = (real_t  **)malloc((size_t)num_threads * sizeof(real_t  *));
    size_t  **lcounts = (size_t  **)malloc((size_t)num_threads * sizeof(size_t  *));
    for (int t = 0; t < num_threads; ++t) {
        lsums[t]   = (real_t  *)calloc(k * d, sizeof(real_t));
        lcounts[t] = (size_t  *)calloc(k,     sizeof(size_t));
    }

    ThreadArgs args[MAX_THREADS];
    pthread_t  tids[MAX_THREADS];

    real_t prev_inertia = DBL_MAX, inertia = 0.0;
    for (size_t iter = 0; iter < max_iters; ++iter) {
        memset(gsums,   0, k * d * sizeof(real_t));
        memset(gcounts, 0, k     * sizeof(size_t));

        for (int t = 0; t < num_threads; ++t) {
            args[t].id            = t;
            args[t].num_threads   = num_threads;
            args[t].N             = N; args[t].d = d; args[t].k = k;
            args[t].points        = ds->points;
            args[t].cent_data     = cent.data;
            args[t].assign        = assign;
            args[t].local_inertia = 0.0;
            args[t].local_sums    = lsums[t];
            args[t].local_counts  = lcounts[t];
            args[t].global_sums   = gsums;
            args[t].global_counts = gcounts;
            args[t].mutex         = &mutex;
            pthread_create(&tids[t], NULL, worker, &args[t]);
        }

        inertia = 0.0;
        for (int t = 0; t < num_threads; ++t) {
            pthread_join(tids[t], NULL);
            inertia += args[t].local_inertia;
        }

        for (size_t c = 0; c < k; ++c) {
            if (!gcounts[c]) continue;
            real_t inv = 1.0 / (real_t)gcounts[c];
            real_t *cp = cent.data + c * d;
            const real_t *sp = gsums + c * d;
            for (size_t dim = 0; dim < d; ++dim) cp[dim] = sp[dim] * inv;
        }
        if (fabs(prev_inertia - inertia) / prev_inertia < tol) break;
        prev_inertia = inertia;
    }

    pthread_mutex_destroy(&mutex);
    for (int t = 0; t < num_threads; ++t) { free(lsums[t]); free(lcounts[t]); }
    free(lsums); free(lcounts);
    free(gsums); free(gcounts);

    KMeansResult res; res.inertia = inertia; res.assignments = assign; res.centroids = cent;
    return res;
}
