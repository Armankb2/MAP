#pragma once
#include <stddef.h>
#include <stdint.h>

/* Floating‑point type used for all arithmetic */
typedef double real_t;

/* Memory layout identifier – used by the dataset loader and algorithms */
enum Layout { LAYOUT_AOS = 0, LAYOUT_SOA = 1 };

typedef enum Layout Layout;

/* Dataset description – holds raw point data and metadata */
typedef struct {
    size_t N;          /* number of points */
    size_t d;          /* dimensionality */
    size_t k;          /* number of clusters */
    Layout layout;     /* AoS or SoA */
    real_t *points;    /* flat array of size N*d */
} Dataset;

/* Centroid container – always stored in AoS layout for simplicity */
typedef struct {
    size_t k;          /* number of clusters */
    size_t d;          /* dimensionality */
    real_t *data;      /* flat array of size k*d, row‑major */
} Centroids;

/* Result of a K‑Means run */
typedef struct {
    real_t inertia;            /* final sum of squared distances */
    size_t *assignments;       /* length N, cluster index for each point */
    Centroids centroids;       /* final centroids */
} KMeansResult;
