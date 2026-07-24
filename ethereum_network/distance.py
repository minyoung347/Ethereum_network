from itertools import combinations
from pathlib import Path
from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import kendalltau

from tqdm import tqdm


def read_ppr_matrix(path):
    """Read PPR matrix saved as scipy sparse npz."""
    X = sparse.load_npz(path)
    return X.tocsr()


def write_ppr_matrix(matrix, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not sparse.issparse(matrix):
        matrix = sparse.csr_matrix(matrix)

    sparse.save_npz(path, matrix.tocsr())


def select_group_rows_from_graph(
    graph: nx.Graph,
    nodes_file,
    group: str,
):
    """Select row indices in all-PPR matrix for a node group.

    Assumes nodes_file maps row -> node for the all-PPR matrix.
    """
    nodes_df = pd.read_csv(nodes_file)
    nodes_df["node"] = nodes_df["node"].astype(str)

    node_to_row = dict(zip(nodes_df["node"], nodes_df["row"]))

    if group == "all":
        rows = nodes_df["row"].to_numpy(dtype=np.int64)
        nodes = nodes_df["node"].tolist()
        return rows, nodes

    type_dic = nx.get_node_attributes(graph, "type")

    selected_nodes = []
    selected_rows = []

    for node, node_type in type_dic.items():
        node = str(node)
        if group in str(node_type) and node in node_to_row:
            selected_nodes.append(node)
            selected_rows.append(int(node_to_row[node]))

    rows = np.asarray(selected_rows, dtype=np.int64)
    return rows, selected_nodes


def _sample_pairs(n: int, pair_sample, seed: int = 42):
    max_pairs = n * (n - 1) // 2

    if n < 2:
        return []

    if pair_sample is None or pair_sample <= 0 or pair_sample >= max_pairs:
        return list(combinations(range(n), 2))

    rng = np.random.default_rng(seed)
    pairs = []
    seen = set()

    while len(pairs) < pair_sample:
        i = int(rng.integers(0, n))
        j = int(rng.integers(0, n))
        if i == j:
            continue
        if i > j:
            i, j = j, i
        key = (i, j)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)

    return pairs


def _row_nonzero_sorted(X: sparse.csr_matrix, row_idx: int):
    """Return nonzero target ids and scores sorted by descending score."""
    row = X.getrow(row_idx)
    idx = row.indices
    val = row.data

    if len(val) == 0:
        return np.asarray([], dtype=np.int64), np.asarray([], dtype=np.float32)

    order = np.argsort(-val)
    return idx[order].astype(np.int64), val[order].astype(np.float32)


def _row_topk_sorted(X: sparse.csr_matrix, row_idx: int, k: int):
    """Return top-k target ids and scores from a sparse row."""
    row = X.getrow(row_idx)
    idx = row.indices
    val = row.data

    if len(val) == 0:
        return np.asarray([], dtype=np.int64), np.asarray([], dtype=np.float32)

    kk = min(k, len(val))
    if kk <= 0:
        return np.asarray([], dtype=np.int64), np.asarray([], dtype=np.float32)

    top_pos = np.argpartition(-val, kk - 1)[:kk]
    order = np.argsort(-val[top_pos])

    return idx[top_pos][order].astype(np.int64), val[top_pos][order].astype(np.float32)


def _rank_dict(items: Iterable[int]):
    return {int(item): rank + 1 for rank, item in enumerate(items)}


def _partial_kendall(
    list_a: np.ndarray,
    list_b: np.ndarray,
    missing_rank_a: int,
    missing_rank_b: int,
) -> float:
    """Kendall tau over union of two partial ranked lists.

    Items absent from one list are assigned the lowest rank.
    """
    if len(list_a) == 0 or len(list_b) == 0:
        return np.nan

    union = np.union1d(list_a, list_b)
    if len(union) < 2:
        return np.nan

    rank_a_map = _rank_dict(list_a)
    rank_b_map = _rank_dict(list_b)

    rank_a = np.empty(len(union), dtype=np.int32)
    rank_b = np.empty(len(union), dtype=np.int32)

    for pos, item in enumerate(union):
        item = int(item)
        rank_a[pos] = rank_a_map.get(item, missing_rank_a)
        rank_b[pos] = rank_b_map.get(item, missing_rank_b)

    tau, _ = kendalltau(rank_a, rank_b)
    return float(tau) if tau == tau else np.nan


def _rbo(list_a: np.ndarray, list_b: np.ndarray, p: float = 0.9, depth = None) -> float:
    """Finite rank-biased overlap for two ranked lists.

    This is a practical finite-depth RBO score. It is suitable for comparing
    incomplete ranked lists and gives larger weight to agreement near the top.
    """
    if len(list_a) == 0 or len(list_b) == 0:
        return np.nan

    if depth is None:
        depth = max(len(list_a), len(list_b))
    depth = min(depth, max(len(list_a), len(list_b)))

    seen_a = set()
    seen_b = set()
    score = 0.0

    for d in range(1, depth + 1):
        if d <= len(list_a):
            seen_a.add(int(list_a[d - 1]))
        if d <= len(list_b):
            seen_b.add(int(list_b[d - 1]))

        agreement = len(seen_a & seen_b) / d
        score += (p ** (d - 1)) * agreement

    return float((1 - p) * score)


def _raw_kendall_pair(X: sparse.csr_matrix, i: int, j: int) -> float:
    """Raw Kendall tau over full dense PPR vectors.

    This reproduces the previous full-ranking style. Use mainly for comparison,
    because it can be dominated by the near-zero tail.
    """
    a = X.getrow(i).toarray().ravel()
    b = X.getrow(j).toarray().ravel()

    if len(a) < 2:
        return np.nan

    # Rank by descending score. Use average ranks for ties.
    # pandas is slower but stable for tied ranks.
    ra = pd.Series(a).rank(ascending=False, method="average").to_numpy()
    rb = pd.Series(b).rank(ascending=False, method="average").to_numpy()

    tau, _ = kendalltau(ra, rb)
    return float(tau) if tau == tau else np.nan


def _similarity_pair(
    X: sparse.csr_matrix,
    i: int,
    j: int,
    metric: str,
    top_k: int = 1000,
    rbo_p: float = 0.9,
) -> float:
    if metric == "raw_kendall":
        return _raw_kendall_pair(X, i, j)

    if metric == "topk_kendall":
        a, _ = _row_topk_sorted(X, i, top_k)
        b, _ = _row_topk_sorted(X, j, top_k)
        return _partial_kendall(a, b, missing_rank_a=top_k + 1, missing_rank_b=top_k + 1)

    if metric == "nonzero_kendall":
        a, _ = _row_nonzero_sorted(X, i)
        b, _ = _row_nonzero_sorted(X, j)
        missing_a = len(a) + 1
        missing_b = len(b) + 1
        return _partial_kendall(a, b, missing_rank_a=missing_a, missing_rank_b=missing_b)

    if metric == "topk_rbo":
        a, _ = _row_topk_sorted(X, i, top_k)
        b, _ = _row_topk_sorted(X, j, top_k)
        return _rbo(a, b, p=rbo_p, depth=top_k)

    if metric == "nonzero_rbo":
        a, _ = _row_nonzero_sorted(X, i)
        b, _ = _row_nonzero_sorted(X, j)
        return _rbo(a, b, p=rbo_p)

    raise ValueError(f"Unknown metric: {metric}")


def _summary_from_values(values):
    arr = np.asarray([v for v in values if v == v], dtype=np.float64)

    if len(arr) == 0:
        return {
            "n_pairs_valid": 0,
            "mean": np.nan,
            "std": np.nan,
            "median": np.nan,
            "q025": np.nan,
            "q25": np.nan,
            "q75": np.nan,
            "q975": np.nan,
        }

    return {
        "n_pairs_valid": int(len(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "median": float(np.median(arr)),
        "q025": float(np.quantile(arr, 0.025)),
        "q25": float(np.quantile(arr, 0.25)),
        "q75": float(np.quantile(arr, 0.75)),
        "q975": float(np.quantile(arr, 0.975)),
    }


def pairwise_sync(
    X,
    metric: str = "raw_kendall",
    top_k: int = 1000,
    rbo_p: float = 0.9,
    pair_sample = None,
    seed: int = 42,
    source_nodes = None,
    summary_only: bool = False,
) -> pd.DataFrame:
    """Compute pairwise synchronization.

    Parameters
    ----------
    X:
        CSR sparse PPR matrix. Rows are source users; columns are target nodes.
    metric:
        raw_kendall, topk_kendall, nonzero_kendall, topk_rbo, nonzero_rbo.
    pair_sample:
        If None or <=0, compute all pairs. Otherwise sample that many pairs.
    summary_only:
        If True, return one-row summary instead of pair-level rows.
    """
    if not sparse.issparse(X):
        X = sparse.csr_matrix(X)
    X = X.tocsr()

    n = X.shape[0]
    pairs = _sample_pairs(n, pair_sample=pair_sample, seed=seed)

    values = []
    rows = []

    for count, (i, j) in enumerate(
        tqdm(pairs, desc=f"[sync {metric}]", unit="pair"),
        start=1,
    ):
        sim = _similarity_pair(X, i, j, metric=metric, top_k=top_k, rbo_p=rbo_p)
        values.append(sim)

        if not summary_only:
            source = source_nodes[i] if source_nodes is not None else i
            target = source_nodes[j] if source_nodes is not None else j
            rows.append(
                {
                    "source": source,
                    "target": target,
                    "similarity": sim,
                    "metric": metric,
                    "top_k": top_k if "topk" in metric else "",
                    "rbo_p": rbo_p if "rbo" in metric else "",
                }
            )


    if summary_only:
        summary = _summary_from_values(values)
        summary.update(
            {
                "metric": metric,
                "top_k": top_k if "topk" in metric else "",
                "rbo_p": rbo_p if "rbo" in metric else "",
                "n_users": n,
                "n_pairs_requested": len(pairs),
            }
        )
        return pd.DataFrame([summary])

    return pd.DataFrame(rows)