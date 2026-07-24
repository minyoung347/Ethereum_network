from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


LABEL_TYPES = ["miner", "genesis", "Exchange", "Gambling", "ICO", "Token Contract"]

    
def load_node_labels(
    label_file: str | Path,
    miner_file: str | Path,
    genesis_file: str | Path,
) -> dict[str, dict[str, object]]:
    add_label = pd.read_csv(label_file, names = ["addID", "type", "nametag"] , sep = " ")
    add_label["addID"] = add_label["addID"].astype(float).astype(int)
    add_label = add_label.set_index("addID")
    label_dic = {k: v.dropna().to_dict() for k,v in add_label.T.items()} # drop nan
    add_label.index = add_label.index.map(str)

    genesis = pd.read_csv(
        genesis_file,
        usecols=[0, 1],
        names=["addID", "type"],
        sep = " ",
    ).set_index("addID")
    genesis.index = genesis.index.map(str)

    miner = pd.read_csv(
        miner_file,
        names=["blockID", "addID","uncle"],
        header=None,
        sep= " ",
    )
    miner = miner.drop_duplicates(["addID"])
    miner["type"] = "miner"
    miner = miner[["addID", "type"]].set_index("addID")
    miner.index = miner.index.map(str)

    label_df = pd.concat(
        [
            add_label,
            pd.get_dummies(add_label["type"]).rename(columns={"miner": "miner_label"}),
            pd.get_dummies(miner["type"]).rename(columns={"miner": "miner_block"}),
            pd.get_dummies(genesis["type"]),
        ],
        axis=1,
    )
    label_df["miner"] = np.where(
        (label_df.get("miner_label", 0) == 1) | (label_df.get("miner_block", 0) == 1),
        1,
        np.nan,
    )

    for column in LABEL_TYPES:
        if column not in label_df.columns:
            label_df[column] = np.nan

    columns = LABEL_TYPES + ["nametag"]
    label_df = label_df[columns].replace(0, np.nan)
    label_df.index = label_df.index.map(str)
    return {node: values.dropna().to_dict() for node, values in label_df.T.items()}

def count_label_dict(node_labels: dict[str, dict[str, object]]) -> dict[str, int]:
    return {
        label: sum(1 for attrs in node_labels.values() if attrs.get(label) in (1, "1", True))
        for label in LABEL_TYPES
    }


def count_graph_labels(graph) -> dict[str, int]:
    return {
        label: sum(1 for _, attrs in graph.nodes(data=True) if attrs.get(label) in (1, "1", True))
        for label in LABEL_TYPES
    }