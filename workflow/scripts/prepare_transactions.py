from __future__ import annotations

import argparse

from ethereum_network.dates import month_range
from ethereum_network.network import write_monthly_transactions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    args = parser.parse_args()

    write_monthly_transactions(args.raw_csv, args.output_dir, month_range(args.start_month, args.end_month))


if __name__ == "__main__":
    main()
