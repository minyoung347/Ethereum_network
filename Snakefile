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
#NETWORK_FILE = j(OUTPUT_DIR, "monthly_network_{month}.gml")
PPR_FILE = j(OUTPUT_DIR, "Ethereum_PPR/PPR_network{month}_{type}.csv")
SYNC_FILE = j(OUTPUT_DIR, "Ethereum_SYNC/SYNC_network{month}_{type}.csv")

###############################################################################
# CONFIGURATION
###############################################################################
MONTHS = ['3','4','5','6','7','8','9','10','11','12','13','14','15','16']
TYPES_OF_NODE = ["genesis", "miner", "random"]

rule all:
    input:
#        expand(NETWORK_FILE, month=MONTHS)
        expand(PPR_FILE, type=TYPES_OF_NODE, month=MONTHS),
        expand(SYNC_FILE, type=TYPES_OF_NODE, month=MONTHS)
        
#rule monthly_network:
#    input:
#        INPUT_DIR
#    output:
#        NETWORK_FILE
#    shell:
#        "python workflow/monthly_network.py --input {input} --month {wildcards.month} --output {output}"

rule calculate_PPR:
    input:
        INPUT_DIR
    output:
        PPR_FILE
    shell:
        "python workflow/CalculatePPR.py --input {input} --type {wildcards.type} --month {wildcards.month} --output {output}" 

rule calculate_synchronization:
    input:
        ppr = PPR_FILE
    output:
        SYNC_FILE
    shell:
        "python workflow/CalculateSync.py --input {input.ppr} --type {wildcards.type} --month {wildcards.month} --output {output}" 