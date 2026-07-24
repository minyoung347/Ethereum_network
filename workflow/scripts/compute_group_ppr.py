from __future__ import annotations

import argparse

from ethereum_network.network import read_graph
from ethereum_network.ppr import compute_group_ppr, write_ppr_series


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--alpha", type=float, default=0.85)
    parser.add_argument("--weight", default="log_value")
    args = parser.parse_args()

    graph = read_graph(args.network)
    ppr = compute_group_ppr(graph, args.group, alpha=args.alpha, weight=args.weight)
    write_ppr_series(ppr, args.output)


if __name__ == "__main__":
    main()
