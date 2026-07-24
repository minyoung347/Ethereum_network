from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from .dates import month_start, next_month


TRANSACTION_COLUMNS = ["txID", "blockID", "in", "out", "txtime", "value", "gas_price", "gas_used"]


def read_transactions(path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    usecols = columns or TRANSACTION_COLUMNS
    return pd.read_csv(path, usecols=usecols)


def add_month_column(transactions: pd.DataFrame) -> pd.DataFrame:
    out = transactions.copy()
    out["txdatetime"] = pd.to_datetime(out["txtime"], unit="s", utc=True)
    out["month"] = out["txdatetime"].dt.strftime("%Y%m")
    return out


def write_monthly_transactions(raw_csv: str | Path, output_dir: str | Path, months: list[str]) -> None:
    transactions = add_month_column(read_transactions(raw_csv))
    output_dir = Path(output_dir)
    month_set = set(months)
    for month, monthly_transactions in transactions.groupby("month", sort=False):
        if month not in month_set:
            continue
        month_dir = output_dir / f"month={month}"
        month_dir.mkdir(parents=True, exist_ok=True)
        monthly_transactions.to_csv(
            month_dir / "transactions.csv.gz",
            index=False,
            compression={"method": "gzip", "compresslevel": 1},
        )


def read_month_transactions(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    transactions = pd.read_csv(path)
    if "txdatetime" in transactions.columns:
        transactions["txdatetime"] = pd.to_datetime(transactions["txdatetime"], utc=True)
        return transactions
    return add_month_column(transactions)


def filter_transactions_by_month(transactions: pd.DataFrame, month: str) -> pd.DataFrame:
    out = transactions
    if "txdatetime" not in out.columns:
        out = add_month_column(out)
    start = pd.Timestamp(month_start(month))
    stop = pd.Timestamp(next_month(month))
    return out.loc[(out["txdatetime"] >= start) & (out["txdatetime"] < stop)].copy()


def build_transaction_graph(transactions: pd.DataFrame, node_labels: dict[str, dict[str, object]]) -> nx.DiGraph:
    real_tx = transactions.loc[transactions["in"] != transactions["out"]].copy()
    real_tx["in"] = real_tx["in"].astype(str)
    real_tx["out"] = real_tx["out"].astype(str)
    real_tx = real_tx.groupby(["in", "out"], as_index=False).agg(value=("value", "sum"))
    real_tx = real_tx.loc[real_tx["value"] > 0].copy()
    real_tx["log_value"] = np.log10(real_tx["value"])

    graph = nx.from_pandas_edgelist(
        real_tx,
        source="out",
        target="in",
        edge_attr=["value", "log_value"],
        create_using=nx.DiGraph(),
    )
    nx.set_node_attributes(graph, node_labels)
    return graph


def build_monthly_network(
    transaction_path: str | Path,
    month: str,
    node_labels: dict[str, dict[str, object]],
) -> nx.DiGraph:
    transactions = read_month_transactions(transaction_path)
    if "month" not in transactions.columns or transactions["month"].nunique() != 1:
        transactions = filter_transactions_by_month(transactions, month)
    return build_transaction_graph(transactions, node_labels)


def read_graph(path: str | Path) -> nx.DiGraph:
    return nx.read_gexf(path)


def write_graph(graph: nx.DiGraph, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(graph, path)
