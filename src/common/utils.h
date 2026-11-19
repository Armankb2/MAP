#pragma once
#include "types.h"
#include <stddef.h>

// Load a dataset from the binary format used by the Python generator.
// Returns 0 on success, non‑zero on failure.
int load_dataset(const char *path, Dataset *out);

// Free the memory allocated inside a Dataset.
void free_dataset(Dataset *ds);

// Initialise centroids (deterministic: first k points).
void init_centroids(const Dataset *ds, Centroids *cent);

// Compute squared Euclidean distance between two points (both AoS layout).
real_t squared_distance(const real_t *a, const real_t *b, size_t d);
