from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ethereum_network.network import read_graph
from ethereum_network.ppr import compute_individual_ppr_matrix_batch, sample_random_nodes, write_ppr_matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--nodes-output", required=True)
    parser.add_argument("--alpha", type=float, default=0.85)
    parser.add_argument("--weight", default="log_value")
    args = parser.parse_args()

    graph = read_graph(args.network)
    target_nodes = sample_random_nodes(graph, args.n, args.seed)
    matrix = compute_individual_ppr_matrix_batch(graph, target_nodes, alpha=args.alpha, weight=args.weight)
    write_ppr_matrix(matrix, args.output)

    nodes_path = Path(args.nodes_output)
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"node": target_nodes}).to_csv(nodes_path, index=False)


if __name__ == "__main__":
    main()
