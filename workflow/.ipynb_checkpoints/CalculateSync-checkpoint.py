import argparse
import networkx as nx
import pandas as pd
from scipy import stats
import numpy as np 
from itertools import combinations

parser = argparse.ArgumentParser()

parser.add_argument(
    '-i', 
    '--input',
    help='Input data',
    type=str,
    required=True,
)
parser.add_argument(
    '-t', 
    '--type',
    help='Node type',
    type=str,
    required=True,
)
parser.add_argument(
    '-m', 
    '--month',
    help='Network number',
    type=str,
    required=True,
)
parser.add_argument(
    '-o', 
    '--output',
    help='Ouput data',
    type=str,
    required=True,
)

args = parser.parse_args()

def calculate_rank_correlation(input_file, output_file):
    PPR = pd.read_csv(input_file)
    PPR = PPR.set_index("Unnamed: 0")
    
    node_list = list(PPR.columns)
    N = len(node_list)
    k_correlation = np.zeros((int(N*(N-1)/2),3))
    
    PPR_rank = pd.DataFrame()
    for node in node_list:
        PPR_rank[node] = PPR[node].rank(ascending=False)
    PPR_rank = PPR_rank.set_index(PPR.index)

    for i, (a, b) in enumerate(combinations(node_list, 2)):
        
        k_correlation[i][0] = a
        k_correlation[i][1] = b
        k_correlation[i][2] = stats.kendalltau(PPR_rank[a], PPR_rank[b])[0]
        
    k_correlation_df = pd.DataFrame(k_correlation)
    k_correlation_df.to_csv(output_file, index=False)

if __name__=='__main__':
    INPUT_DIR = args.input
    OUTPUT_FILE = args.output
    TYPE = args.type
    NUMBER = args.month
    
    calculate_rank_correlation(INPUT_DIR, OUTPUT_FILE)