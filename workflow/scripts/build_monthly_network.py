from __future__ import annotations

import argparse

from ethereum_network.labels import LABEL_TYPES, count_graph_labels, count_label_dict, load_node_labels
from ethereum_network.network import build_monthly_network, write_graph


def print_label_counts(month: str, loaded_counts: dict[str, int], matched_counts: dict[str, int]) -> None:
    print(f"[build_monthly_network] month={month} label counts", flush=True)
    print("label\tloaded\tmatched_in_graph", flush=True)
    for label in LABEL_TYPES:
        print(f"{label}\t{loaded_counts.get(label, 0)}\t{matched_counts.get(label, 0)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--label-file", required=True)
    parser.add_argument("--miner-file", required=True)
    parser.add_argument("--genesis-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    labels = load_node_labels(args.label_file, args.miner_file, args.genesis_file)
    graph = build_monthly_network(args.transactions, args.month, labels)
    print_label_counts(args.month, count_label_dict(labels), count_graph_labels(graph))
    write_graph(graph, args.output)


if __name__ == "__main__":
    main()
