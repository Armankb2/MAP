import struct, argparse, numpy as np, os, sys

def generate(N, d, k, seed, layout='AoS'):
    rng = np.random.default_rng(seed)
    # Generate k centroids randomly
    centroids = rng.normal(loc=0.0, scale=5.0, size=(k, d))
    # Assign each point to a random centroid then add Gaussian noise
    assignments = rng.integers(low=0, high=k, size=N)
    points = centroids[assignments] + rng.normal(scale=1.0, size=(N, d))
    if layout == 'SoA':
        points = points.T.reshape(-1)
    else:
        points = points.reshape(-1)
    return points.astype(np.float64)

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic Gaussian blob dataset for K-Means')
    parser.add_argument('--N', type=int, required=True, help='Number of points')
    parser.add_argument('--d', type=int, required=True, help='Dimensionality')
    parser.add_argument('--k', type=int, required=True, help='Number of clusters')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--layout', choices=['AoS','SoA'], default='AoS', help='Memory layout')
    parser.add_argument('--out', type=str, required=True, help='Output binary file')
    args = parser.parse_args()
    pts = generate(args.N, args.d, args.k, args.seed, args.layout)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'wb') as f:
        f.write(struct.pack('Q', args.N))
        f.write(struct.pack('Q', args.d))
        f.write(struct.pack('Q', args.k))
        f.write(struct.pack('B', 0 if args.layout == 'AoS' else 1))
        f.write(pts.tobytes())
    print(f'Wrote {args.N}x{args.d} points (layout={args.layout}) to {args.out}')

if __name__ == '__main__':
    main()
