from __future__ import annotations

import argparse
from pathlib import Path

from ethereum_network.distance import pairwise_sync, read_ppr_matrix, select_group_rows_from_graph
from ethereum_network.network import read_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ppr-matrix", required=True)
    parser.add_argument("--nodes-file", required=True)
    parser.add_argument("--network", required=True)
    parser.add_argument("--group", required=True, choices=["genesis", "miner", "all"])
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
    parser.add_argument("--pair-sample", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    graph = read_graph(args.network)
    X_all = read_ppr_matrix(args.ppr_matrix)

    rows, selected_nodes = select_group_rows_from_graph(
        graph=graph,
        nodes_file=args.nodes_file,
        group=args.group,
    )

    X_group = X_all[rows].tocsr()

    print(f"[compute_sync] group={args.group}")
    print(f"[compute_sync] selected rows={len(rows)}, matrix shape={X_group.shape}")
    print(f"[compute_sync] metric={args.metric}, top_k={args.top_k}, rbo_p={args.rbo_p}")

    pair_sample = args.pair_sample if args.pair_sample > 0 else None

    sync = pairwise_sync(
        X_group,
        metric=args.metric,
        top_k=args.top_k,
        rbo_p=args.rbo_p,
        pair_sample=pair_sample,
        seed=args.seed,
        source_nodes=selected_nodes,
        summary_only=args.summary_only,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sync.to_csv(output, index=False)

    print(f"[compute_sync] wrote {output}")
    
if __name__ == "__main__":
    main()
