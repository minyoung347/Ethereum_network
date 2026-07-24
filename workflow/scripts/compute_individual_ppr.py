from __future__ import annotations

import argparse
from pathlib import Path

from ethereum_network.network import read_graph
from ethereum_network.ppr import compute_individual_ppr_matrix_batch, nodes_by_group, write_ppr_matrix

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--nodes-output", required=True)
    parser.add_argument("--alpha", type=float, default=0.85)
    parser.add_argument("--weight", default="log_value")
    args = parser.parse_args()

    graph = read_graph(args.network)

    if args.group == "all":
        target_nodes = list(graph.nodes())
    else:
        target_nodes = nodes_by_group(graph, args.group)

    print(f"[compute_individual_ppr] network={args.network}")
    print(f"[compute_individual_ppr] group={args.group}, n_sources={len(target_nodes)}, n_nodes={graph.number_of_nodes()}")
    print(f"[compute_individual_ppr] alpha={args.alpha}, weight={args.weight}")

    matrix = compute_individual_ppr_matrix_batch(graph, target_nodes, alpha=args.alpha, weight=args.weight)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_ppr_matrix(matrix, output)

    nodes_path = Path(args.nodes_output)
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row": range(len(target_nodes)), "node": target_nodes}).to_csv(nodes_path, index=False)

    print(f"[compute_individual_ppr] wrote matrix: {output}")
    print(f"[compute_individual_ppr] wrote nodes: {nodes_path}")

if __name__ == "__main__":
    main()
