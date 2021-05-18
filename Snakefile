from os.path import join as j
from glob import glob

configfile: "workflow/config.yaml"

###############################################################################
# FOLDERS
###############################################################################
INPUT_DIR = config["input_dir"] 
OUTPUT_DIR = config["output_dir"]

###############################################################################
# PROCESSED DATA FILES
###############################################################################
NETWORK_FILE = j(OUTPUT_DIR, "network_{month}.gml")
PPR_FILE = j(OUTPUT_DIR, "PPR/PPR_{type}_{month}.csv")

###############################################################################
# CONFIGURATION
###############################################################################
PERIODS_FOR_ANALYSIS = ['2015-08-01','2015-09-01','2015-10-01']
TYPES_OF_NODE = ["genesis", "miner", "random"]

rule all:
    input:
        expand(NETWORK_FILE, month=PERIODS_FOR_ANALYSIS)
	expand(PPR_FILE, type=TYPES_OF_NODE, month=PERIOD_FOR_ANALYSIS)

rule monthly_network:
    input:
        INPUT_DIR
    output:
        NETWORK_FILE
    shell:
        "python workflow/monthly_network.py --input {input} --month {wildcards.month} --output {output}"

rule calculate_PPR:
    input:
	NETWORK_FILE
    output:
        PPR_FILE
    shell:
	"python workflow/Calculate_PPR.py --input {input} --type {wildcards.type} --month {wildcards.month} --output {output}" 
