import argparse
import networkx as nx
import os 
import random
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import pandas as pd 
import numpy as np
from collections import defaultdict
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
    help='Output file',
    type=str,
    required=True,
)

args = parser.parse_args()

def construct_monthly_network(number):
    add_label = pd.read_csv("/home/damini/Ethereum/Labeling/addresslabel.txt", names = ["addID", "type", "nametag"] , sep = " ")
    add_label = add_label.set_index("addID")

    genesis = pd.read_csv("/home/damini/Ethereum/Labeling/genesis_labels.txt", usecols = [0,1], names = ["addID", "type"] , sep = " ")
    genesis = genesis.set_index("addID")

    miner = pd.read_csv("/home/damini/Ethereum/Basic_Dataset/blockminer.txt", names = ["blockID", "addID","uncle"], header=None, sep=' ')
    miner_type = miner.drop_duplicates(["addID"])
    miner_type["type"] = "miner" 
    miner_type = miner_type.set_index("addID")

    label_dic = add_label.to_dict("index")
    for node, labels in label_dic.items():
        label_dic[node]['type'] = [labels['type']]

    genesis_dic = genesis.to_dict("index")
    miner_dic = miner_type[["type"]].to_dict("index")

    # setting multitype node
    node_type_dic = defaultdict(lambda: defaultdict(list))

    for node, type_dic in genesis_dic.items():
        node_type_dic[node]['type'].append('genesis')
    for node, type_dic in miner_dic.items():
        node_type_dic[node]['type'].append('miner')
    
    transaction = pd.read_csv('/home/damini/Ethereum/Except_tx_fee/transaction_data_except_txfee.csv')
    transaction["txdatetime"] = transaction["txtime"].map(lambda x:datetime.fromtimestamp(x, timezone.utc))

    time_from = datetime.fromtimestamp(1438387200, timezone.utc) + relativedelta(months=1*int(number))
    time_until = time_from + relativedelta(months=1)
    tx_bytime = transaction[(transaction.txdatetime >= time_from) & (transaction.txdatetime < time_until)] 
    
    real_tx = tx_bytime.groupby(["in", "out"], as_index=False).agg({"value": np.sum})
    real_tx = real_tx[real_tx["value"] != 0]
    real_tx["logvalue"] = real_tx["value"].apply(lambda x: np.log10(x))

    tx_G_bytime = nx.from_pandas_edgelist(real_tx, source = "out", target = "in", edge_attr=["logvalue"], create_using=nx.DiGraph())
    nx.set_node_attributes(tx_G_bytime, label_dic)
    nx.set_node_attributes(tx_G_bytime, node_type_dic)
    
    return tx_G_bytime

def calculate_individual_PPR(graph, target):
    personal = {}
    
    for node in graph.nodes():
        if node == target:
            personal[node] = 1
        else:
            personal[node] = 0
        
    pagerank = nx.pagerank(graph, alpha=0.85, personalization = personal, weight='logvalue')
    return pagerank

def construct_PPRdf_by_group(input_dir, type_, number, output_file):
#     network = nx.read_gml(os.path.join(input_dir, 'monthly_network_{}.gml'.format(number)))
       
    if type_ == 'random':
        random.seed(2015)
        number_of_sample = 500
        node_list = random.sample(network.nodes(), number_of_sample)
    else:
        type_dic = nx.get_node_attributes(network, "type")
        node_list = [k for k, v in type_dic.items() if type_ in v ]
    
    get_PPR = {}
    for node in node_list:
        get_PPR[node] = calculate_individual_PPR(network, node)
        
    PPR_df = pd.DataFrame.from_dict(get_PPR)
    
    PPR_df.to_csv(output_file)

if __name__=='__main__':

    TYPE = args.type
    NUMBER = args.month
    OUTPUT_FILE = args.output
    
#     INPUT_DIR = args.input
#     construct_PPRdf_by_group(INPUT_DIR, TYPE, NUMBER, OUTPUT_FILE)

    network = construct_monthly_network(NUMBER)
    construct_PPRdf_by_group(network, TYPE, NUMBER, OUTPUT_FILE)