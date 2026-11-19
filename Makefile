# Makefile for Shared-Memory K-Means (P28 – Cluster H)
# Pure C11 Implementation on Apple Silicon (ARM64)
# Requires: Clang + libomp + Pthreads

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

BENCH_SRC := $(COMMON) $(SEQ) $(OMP) $(PTH) $(BENCH)
BENCH_OBJ := $(BENCH_SRC:.c=.o)

.PHONY: all clean test stream

all: $(BIN_DIR)/benchmark $(BIN_DIR)/stream_mem

$(BIN_DIR)/benchmark: $(BENCH_OBJ)
	@mkdir -p $(BIN_DIR)
	$(CLANG) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BIN_DIR)/stream_mem: src/benchmark/stream_mem.c
	@mkdir -p $(BIN_DIR)
	$(CLANG) $(CFLAGS) -o $@ $< $(LDFLAGS)

%.o: %.c
	$(CLANG) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BIN_DIR) $(BENCH_OBJ)

test: all
	@mkdir -p results/raw
	python3 tests/check_correctness.py

stream: $(BIN_DIR)/stream_mem
	DYLD_LIBRARY_PATH=/opt/homebrew/opt/libomp/lib $(BIN_DIR)/stream_mem 8
