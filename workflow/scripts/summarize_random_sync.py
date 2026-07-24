from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dfs = []
    for path in args.inputs:
        df = pd.read_csv(path)
        dfs.append(df)

    out = pd.concat(dfs, ignore_index=True)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)


if __name__ == "__main__":
    main()