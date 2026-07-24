from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ethereum_network.distance import pairwise_sync, read_ppr_matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ppr-matrix", required=True)
    parser.add_argument("--nodes-file", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--repeat", required=True)
    parser.add_argument("--base-seed", type=int, required=True)
    parser.add_argument("--n-nodes", type=int, required=True)
    parser.add_argument("--pair-sample", type=int, default=0)
    parser.add_argument(
        "--metric",
        required=True,
        choices=[
            "raw_kendall",
            "topk_kendall",
            "nonzero_kendall",
            "topk_rbo",
            "nonzero_rbo",
        ],
    )
    parser.add_argument("--top-k", type=int, default=1000)
    parser.add_argument("--rbo-p", type=float, default=0.9)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repeat_int = int(args.repeat)
    seed = args.base_seed + repeat_int
    rng = np.random.default_rng(seed)

    X_all = read_ppr_matrix(args.ppr_matrix)
    nodes_df = pd.read_csv(args.nodes_file)
    nodes_df["node"] = nodes_df["node"].astype(str)

    n_total = X_all.shape[0]
    n_sample = min(args.n_nodes, n_total)

    selected_rows = rng.choice(n_total, size=n_sample, replace=False)
    selected_nodes = nodes_df.iloc[selected_rows]["node"].tolist()

    X_random = X_all[selected_rows].tocsr()

    print(f"[compute_random_sync] month={args.month}, repeat={args.repeat}, seed={seed}")
    print(f"[compute_random_sync] sample={n_sample}/{n_total}, matrix shape={X_random.shape}")
    print(f"[compute_random_sync] metric={args.metric}, pair_sample={args.pair_sample}")

    sync = pairwise_sync(
        X_random,
        metric=args.metric,
        top_k=args.top_k,
        rbo_p=args.rbo_p,
        pair_sample=args.pair_sample,
        seed=seed,
        source_nodes=selected_nodes,
        summary_only=True,
    )

    sync.insert(0, "seed", seed)
    sync.insert(0, "repeat", args.repeat)
    sync.insert(0, "month", args.month)
    sync.insert(0, "group", "random")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sync.to_csv(output, index=False)

    print(f"[compute_random_sync] wrote {output}")


if __name__ == "__main__":
    main()