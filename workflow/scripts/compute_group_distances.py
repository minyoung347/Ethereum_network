from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ethereum_network.distance import compare_ppr_vectors, read_ppr_series


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", nargs="+", required=True)
    parser.add_argument("--left-template", required=True)
    parser.add_argument("--right-template", required=True)
    parser.add_argument("--left-group", required=True)
    parser.add_argument("--right-group", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = []
    for month in args.months:
        left = read_ppr_series(args.left_template.format(month=month, group=args.left_group))
        right = read_ppr_series(args.right_template.format(month=month, group=args.right_group))
        rows.append({"month": month, **compare_ppr_vectors(left, right)})

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)


if __name__ == "__main__":
    main()
