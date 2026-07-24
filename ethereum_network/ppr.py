from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy import sparse

from tqdm import tqdm


def nodes_by_group(graph: nx.Graph, group: str) -> list[str]:
    nodes = []
    for node, attrs in graph.nodes(data=True):
        value = attrs.get(group)
        type_value = attrs.get("type")
        if value in (1, "1", True) or type_value == group:
            nodes.append(node)
    return sorted(nodes)


def sample_random_nodes(graph: nx.Graph, n: int, seed: int) -> list[str]:
    rng = np.random.default_rng(seed)
    nodes = np.array(list(graph.nodes()), dtype=object)
    if n > len(nodes):
        raise ValueError(f"Cannot sample {n} nodes from graph with {len(nodes)} nodes")
    return sorted(rng.choice(nodes, size=n, replace=False).tolist())


def personalization(graph: nx.Graph, seed_nodes: list[str]) -> dict[str, float]:
    if not seed_nodes:
        raise ValueError("Personalization seed node list is empty")
    seed_set = set(seed_nodes)
    value = 1.0 / len(seed_set)
    return {node: value if node in seed_set else 0.0 for node in graph.nodes()}


def compute_ppr(
    graph: nx.DiGraph,
    seed_nodes: list[str],
    alpha: float = 0.85,
    weight: str = "log_value",
    tol: float = 1e-8,
    max_iter: int = 100,
) -> dict[str, float]:
    return nx.pagerank(
        graph,
        alpha=alpha,
        personalization=personalization(graph, seed_nodes),
        dangling=personalization(graph, seed_nodes),
        weight=weight,
        tol=tol,
        max_iter=max_iter,
    )


def compute_group_ppr(graph: nx.DiGraph, group: str, **kwargs) -> pd.Series:
    seeds = nodes_by_group(graph, group)
    return pd.Series(compute_ppr(graph, seeds, **kwargs), name=group).sort_index()


def compute_individual_ppr_matrix(graph: nx.DiGraph, target_nodes: list[str], **kwargs) -> pd.DataFrame:
    ppr_by_node = {}
    for node in target_nodes:
        ppr_by_node[node] = compute_ppr(graph, [node], **kwargs)
    return pd.DataFrame.from_dict(ppr_by_node).sort_index()


def compute_individual_ppr_matrix_batch(
    graph: nx.DiGraph,
    target_nodes: list[str],
    alpha: float = 0.85,
    weight: str = "log_value",
    tol: float = 1e-8,
    max_iter: int = 100,
) -> sparse.csr_matrix:
    if not target_nodes:
        return pd.DataFrame(index=sorted(graph.nodes()))

    nodes = sorted(str(n) for n in graph.nodes())
    node_index = {node: idx for idx, node in enumerate(nodes)}
    n_nodes = len(nodes)

    target_nodes = [str(n) for n in target_nodes]

    if not target_nodes:
        return sparse.csr_matrix((0, n_nodes), dtype=np.float32)

    missing = [node for node in target_nodes if node not in node_index]
    if missing:
        raise ValueError(
            f"{len(missing)} target nodes are not in the graph. "
            f"Examples: {missing[:5]}"
        )

    # Check edge weights once. PageRank weights must be non-negative.
    for source, target, attrs in graph.edges(data=True):
        value = float(attrs.get(weight, 1.0))
        if value < 0:
            raise ValueError(
                f"Negative edge weight found: {source}->{target}, "
                f"{weight}={value}"
            )

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []

    for row_idx, source_node in enumerate(tqdm(target_nodes, desc="[PPR nx]", unit="source")):
        personalization = {source_node: 1.0}

        # For directed personalized PageRank, dangling mass is returned to the
        # source node through the same personalization vector.
        pr = nx.pagerank(
            graph,
            alpha=alpha,
            personalization=personalization,
            dangling=personalization,
            weight=weight,
            tol=tol,
            max_iter=max_iter,
        )

        for target_node, score in pr.items():
            score = float(score)
            if score > 0.0:
                target_node = str(target_node)
                col_idx = node_index.get(target_node)
                if col_idx is not None:
                    rows.append(row_idx)
                    cols.append(col_idx)
                    data.append(score)

    matrix = sparse.csr_matrix(
        (
            np.asarray(data, dtype=np.float32),
            (
                np.asarray(rows, dtype=np.int64),
                np.asarray(cols, dtype=np.int64),
            ),
        ),
        shape=(len(target_nodes), n_nodes),
        dtype=np.float32,
    )

    return matrix

def write_ppr_series(series: pd.Series, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    series = series.sort_index()
    np.savez_compressed(
        path,
        ppr=series.to_numpy(dtype=np.float32),
        nodes=np.asarray(series.index.astype(str), dtype=str),
    )


def write_ppr_matrix(matrix, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if sparse.issparse(matrix):
        sparse.save_npz(output, matrix.tocsr())
    elif isinstance(matrix, pd.DataFrame):
        matrix = matrix.sort_index()
        matrix.to_csv(output)
    else:
        sparse.save_npz(output, sparse.csr_matrix(matrix))
