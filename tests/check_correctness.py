"""
Automated correctness test suite for P28 Shared-Memory K-Means.
Validates all implementations against the sequential reference:
- Sequential baseline
- OpenMP private accumulators
- OpenMP atomic updates
- OpenMP critical sections
- OpenMP SIMD (ARM NEON)
- OpenMP AoS vs SoA
- POSIX Pthreads

Checks relative error <= 1e-6 for multiple dataset configurations.
"""
import sys, os, subprocess, csv

def run_test(dataset_path, threads, csv_out):
    cmd = [
        "./bin/benchmark",
        dataset_path,
        str(threads),
        csv_out
    ]
    env = os.environ.copy()
    env["DYLD_LIBRARY_PATH"] = "/opt/homebrew/opt/libomp/lib"
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED to run benchmark: {res.stderr}")
        return False
    
    # Parse CSV output and check relative error column
    with open(csv_out, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            err = float(row["error"])
            impl = row["implementation"]
            if err > 1e-6:
                print(f"FAIL: {impl} relative error {err:.2e} > 1e-6 tolerance!")
                return False
            else:
                print(f"PASS: {impl} on {row['dataset']} (threads={row['threads_or_ranks']}, run={row['run_id']}) error={err:.2e} <= 1e-6")
    return True

def main():
    os.makedirs("results/raw", exist_ok=True)
    test_csv = "results/raw/test_verification.csv"
    
    # Generate test datasets with varying parameters:
    # 1. Standard small: N=5000, d=2, k=4
    # 2. Multi-dimensional: N=5000, d=16, k=8
    # 3. High cluster count: N=5000, d=4, k=32
    # 4. Single cluster (k=1 edge case): N=1000, d=2, k=1
    test_configs = [
        (5000, 2, 4, "datasets/synthetic/test_n5k_d2_k4.bin"),
        (5000, 16, 8, "datasets/synthetic/test_n5k_d16_k8.bin"),
        (5000, 4, 32, "datasets/synthetic/test_n5k_d4_k32.bin"),
        (1000, 2, 1, "datasets/synthetic/test_n1k_d2_k1.bin"),
    ]
    
    for N, d, k, out_file in test_configs:
        print(f"\n--- Generating test dataset N={N}, d={d}, k={k} ---")
        subprocess.run([
            "python3", "scripts/generate_dataset.py",
            "--N", str(N), "--d", str(d), "--k", str(k),
            "--seed", "123", "--out", out_file
        ], check=True)
        
        for threads in [1, 2, 4, 8]:
            print(f"\nVerifying with thread count = {threads}...")
            ok = run_test(out_file, threads, test_csv)
            if not ok:
                print("Test verification FAILED!")
                sys.exit(1)
                
    print("\n========================================================")
    print("ALL CORRECTNESS TESTS PASSED (relative error <= 1e-6)!")
    print("========================================================")

if __name__ == "__main__":
    main()
