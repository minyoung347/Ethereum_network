from os.path import join as j
from glob import glob

configfile: "workflow/config.yaml"
shell.prefix("export PYTHONPATH=$PWD:$PYTHONPATH; ")


###############################################################################
# FOLDERS
###############################################################################

RAW_TRANSACTION_FILE = config["raw_transaction_file"]
LABEL_DIR = config["label_dir"]
RESULTS = config["results_dir"]


###############################################################################
# PROCESSED DATA FILES
###############################################################################
TX_MONTHLY = j(RESULTS, "transactions/month={month}/transactions.csv.gz")
NETWORK = j(RESULTS, "networks/month={month}/network.gexf")
GROUP_PPR = j(RESULTS, "ppr/group/month={month}/type={group}.npz")

INDIVIDUAL_PPR_ALL = j(RESULTS, "ppr/individual/month={month}/type=all.npz")
INDIVIDUAL_PPR_NODES = j(RESULTS, "ppr/individual/month={month}/type=all_nodes.csv")

# RANDOM_PPR = j(RESULTS, f"ppr/random/month={{month}}/seed={RANDOM_SEED}_n={RANDOM_N}.npz")
# RANDOM_NODES = j(RESULTS, f"ppr/random/month={{month}}/seed={RANDOM_SEED}_n={RANDOM_N}_nodes.csv")
SYNC = j(RESULTS, "sync/metric={sync}/month={month}/type={group}.csv")

RANDOM_SYNC_REPEAT = j(RESULTS, "sync/random/metric={sync}/month={month}/repeat={repeat}.csv")
RANDOM_SYNC_SUMMARY = j(RESULTS, "sync/random/metric={sync}/random_summary.csv")
GROUP_DISTANCE = j(RESULTS, "distances/group_ppr_distance.csv")

###############################################################################
# PARAMETERS
###############################################################################
GROUPS = ["genesis", "miner"]

START_MONTH = "201508"
END_MONTH = "201612"

PPR_ALPHA = 0.85
PPR_WEIGHT = "log_value"

SYNC_METRICS = ["topk_kendall", "nonzero_kendall", "topk_rbo", "nonzero_rbo"]  # raw_kendall, topk_kendall, nonzero_kendall, topk_rbo, nonzero_rbo
SYNC_TOP_K = 1000
SYNC_RBO_P = 0.9

SYNC_RANDOM_REPEATS = 5  # 일단 테스트용. 나중에 100~1000
RANDOM_SYNC_N = 500
RANDOM_SYNC_PAIR_SAMPLE = 0

RANDOM_SYNC_BASE_SEED = 42

###############################################################################
# CONFIGURATION
###############################################################################
import pandas as pd

MONTHS = [
    month.strftime("%Y%m")
    for month in pd.date_range(start=START_MONTH + "01", end=END_MONTH + "01", freq="MS")
]
MONTHS_ARG = " ".join(MONTHS)
REPEATS = [f"{repeat:03d}" for repeat in range(SYNC_RANDOM_REPEATS)]

rule all:
    input:
        expand(NETWORK, month=MONTHS),
        expand(GROUP_PPR, month=MONTHS, group=GROUPS),
        expand(INDIVIDUAL_PPR_ALL, month=MONTHS, group=GROUPS),
        expand(INDIVIDUAL_PPR_NODES, month=MONTHS, group=GROUPS),
        # expand(RANDOM_PPR, month=MONTHS),
        expand(SYNC, month=MONTHS, group=GROUPS, sync=SYNC_METRICS),
        expand(RANDOM_SYNC_REPEAT, month=MONTHS, sync=SYNC_METRICS, repeat=REPEATS),
        expand(RANDOM_SYNC_SUMMARY, sync=SYNC_METRICS),
        GROUP_DISTANCE,

rule prepare_transactions:
    input:
        RAW_TRANSACTION_FILE
    output:
        expand(TX_MONTHLY, month=MONTHS)
    shell:
        "python3 workflow/scripts/prepare_transactions.py "
        "--raw-csv {input} "
        "--output-dir {RESULTS}/transactions "
        "--start-month {START_MONTH} "
        "--end-month {END_MONTH}"


rule build_monthly_network:
    input:
        transactions=TX_MONTHLY,
        label_file=j(LABEL_DIR, "addresslabel.txt"),
        miner_file=j(LABEL_DIR, "blockminer.txt"),
        genesis_file=j(LABEL_DIR, "genesis_labels.txt"),
    output:
        NETWORK
    shell:
        "python3 workflow/scripts/build_monthly_network.py "
        "--transactions {input.transactions} "
        "--month {wildcards.month} "
        "--label-file {input.label_file} "
        "--miner-file {input.miner_file} "
        "--genesis-file {input.genesis_file} "
        "--output {output}"

rule compute_group_ppr:
    input:
        NETWORK
    output:
        GROUP_PPR
    shell:
        "python3 workflow/scripts/compute_group_ppr.py "
        "--network {input} "
        "--group {wildcards.group} "
        "--alpha {PPR_ALPHA} "
        "--weight {PPR_WEIGHT} "
        "--output {output}"

rule compute_group_distances:
    input:
        expand(GROUP_PPR, month=MONTHS, group=GROUPS)
    output:
        GROUP_DISTANCE
    shell:
        "python3 workflow/scripts/compute_group_distances.py "
        "--months {MONTHS_ARG} "
        "--left-template '{RESULTS}/ppr/group/month={{month}}/type={{group}}.npz' "
        "--right-template '{RESULTS}/ppr/group/month={{month}}/type={{group}}.npz' "
        "--left-group genesis "
        "--right-group miner "
        "--output {output}"


rule compute_individual_ppr:
    input:
        NETWORK
    output:
        matrix=INDIVIDUAL_PPR_ALL,
        nodes=INDIVIDUAL_PPR_NODES
    shell:
        "python3 workflow/scripts/compute_individual_ppr.py "
        "--network {input} "
        "--group all "
        "--alpha {PPR_ALPHA} "
        "--weight {PPR_WEIGHT} "
        "--output {output.matrix} "
        "--nodes-output {output.nodes}"

rule compute_sync:
    input:
        ppr=INDIVIDUAL_PPR_ALL,
        nodes=INDIVIDUAL_PPR_NODES,
        network=NETWORK
    output:
        SYNC
    shell:
        "python3 workflow/scripts/compute_sync.py "
        "--ppr-matrix {input.ppr} "
        "--nodes-file {input.nodes} "
        "--network {input.network} "
        "--group {wildcards.group} "
        "--metric {wildcards.sync} "
        "--top-k {SYNC_TOP_K} "
        "--rbo-p {SYNC_RBO_P} "
        "--output {output}"


rule compute_random_sync:
    input:
        ppr=INDIVIDUAL_PPR_ALL,
        nodes=INDIVIDUAL_PPR_NODES
    output:
        RANDOM_SYNC_REPEAT
    shell:
        "python3 workflow/scripts/compute_random_sync.py "
        "--ppr-matrix {input.ppr} "
        "--nodes-file {input.nodes} "
        "--month {wildcards.month} "
        "--repeat {wildcards.repeat} "
        "--base-seed {RANDOM_SYNC_BASE_SEED} "
        "--n-nodes {RANDOM_SYNC_N} "
        "--pair-sample {RANDOM_SYNC_PAIR_SAMPLE} "
        "--metric {wildcards.sync} "
        "--top-k {SYNC_TOP_K} "
        "--rbo-p {SYNC_RBO_P} "
        "--output {output}"

rule summarize_random_sync:
    input:
        expand(RANDOM_SYNC_REPEAT, month=MONTHS, sync=SYNC_METRICS, repeat=REPEATS)
    output:
        RANDOM_SYNC_SUMMARY
    shell:
        "python3 workflow/scripts/summarize_random_sync.py --inputs {input} --output {output}"