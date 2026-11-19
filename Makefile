# Makefile for Shared-Memory K-Means (P28 – Cluster H)
# Requires: Homebrew LLVM clang + libomp on Apple Silicon (ARM64)

CLANG   := /opt/homebrew/opt/llvm/bin/clang
CFLAGS  := -std=c11 -O3 -march=armv8.5-a \
           -I/opt/homebrew/opt/libomp/include \
           -Isrc/common \
           -Wall -Wextra
LDFLAGS := -L/opt/homebrew/opt/libomp/lib -lomp -lpthread -lm
BIN_DIR := bin

COMMON  := src/common/utils.c src/common/metrics.c
SEQ     := src/sequential/kmeans_sequential.c
OMP     := src/openmp/kmeans_private.c \
           src/openmp/kmeans_atomic.c \
           src/openmp/kmeans_critical.c \
           src/openmp/kmeans_simd.c \
           src/openmp/kmeans_aos_soa.c
PTH     := src/pthreads/kmeans_pthreads.c
BENCH   := src/benchmark/benchmark.c

ALL_SRC := $(COMMON) $(SEQ) $(OMP) $(PTH) $(BENCH)
ALL_OBJ := $(ALL_SRC:.c=.o)

.PHONY: all clean test

all: $(BIN_DIR)/benchmark

$(BIN_DIR)/benchmark: $(ALL_OBJ)
	@mkdir -p $(BIN_DIR)
	$(CLANG) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CLANG) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BIN_DIR) $(ALL_OBJ)

test: all
	@mkdir -p results/raw
	python3 scripts/generate_dataset.py --N 10000 --d 2 --k 8 --seed 42 --layout AoS --out /tmp/test_ds.bin
	$(BIN_DIR)/benchmark /tmp/test_ds.bin 4 results/raw/test_run.csv
	python3 tests/check_correctness.py results/raw/test_run.csv
