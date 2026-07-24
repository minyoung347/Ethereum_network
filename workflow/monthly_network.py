import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from collections import Counter, defaultdict

from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    "-t",
    "--transaction_file",
    help="Transaction file",
    type=str,
    required=True,
)
parser.add_argument(
    "-m",
    "--month",
    help="Network month",
    type=str,
    required=True,
)
parser.add_argument(
    "-o",
    "--output",
    help="Output Network file",
    type=str,
    required=True,
)
parser.add_argument(
    "-l",
    "--label_file",
    help="Label file",
    type=str,
    required=True,
)
parser.add_argument(
    "-m",
    "--miner_file",
    help="Miner file",
    type=str,
    required=True,
)
parser.add_argument(
    "-g",
    "--genesis_file",
    help="Genesis file",
    type=str,
    required=True,
)

args = parser.parse_args()

def label_node(label_file, miner_file, genesis_file):
    # Labeling (getting type and nametag to dictionary)

    add_label = pd.read_csv(label_file, names = ["addID", "type", "nametag"] , sep = " ")
    add_label = add_label.set_index("addID")
    label_dic = {k: v.dropna().to_dict() for k,v in add_label.T.items()} # drop nan

    # miner and genesis list
    genesis = pd.read_csv(genesis_file, usecols = [0,1], names = ["addID", "type"] , sep = " ")
    genesis = genesis.set_index("addID")

    miner = pd.read_csv(miner_file, names = ["blockID", "addID","uncle"], header=None, sep=' ')
    miner = miner.drop_duplicates(["addID"])
    miner["type"] = "miner" 
    miner = miner[["addID", "type"]].set_index("addID")

    # setting multitype node
    labeldf = pd.concat([add_label, pd.get_dummies(add_label.type).rename(columns={'miner':'miner_label'}), 
                    pd.get_dummies(miner.type).rename(columns={'miner':'miner_block'}), 
                    pd.get_dummies(genesis.type)], axis=1)

    labeldf['miner'] = np.where(((labeldf.miner_label == 1) | (labeldf.miner_block == 1)), 1, np.nan)

    column_name = ['miner', 'genesis', 'Exchange', 'Gambling', 'ICO', 'Token Contract', 'nametag']
    labeldf = labeldf[column_name].replace(0, np.nan)

    node_label_dic = {k: v.dropna().to_dict() for k,v in labeldf.T.items()} # drop nan

    return node_label_dic

def construct_monthly_network(month, transaction_file, node_label_dic, output_file):
    transaction=pd.read_csv(transaction_file)
    # timestamp to datetime 
    transaction["txdatetime"] = transaction["txtime"].map(lambda x:datetime.fromtimestamp(x, timezone.utc))
    # delete self transaction 
    transaction = transaction[transaction['in']!=transaction['out']] 

    def month_to_date(month):
        return datetime.strptime(month, '%Y%m')
    
    time_from = month_to_date(month)
    time_until = time_from + relativedelta(months=1)
    tx_bytime = transaction[(transaction.txdatetime >= time_from) & (transaction.txdatetime < time_until)] 
    real_tx = tx_bytime.groupby(["in", "out"], as_index=False).agg({"value": np.sum})
    real_tx = real_tx[real_tx["value"] != 0]
    real_tx["log_value"] = real_tx["value"].apply(lambda x: np.log10(x))
        
    tx_G_bytime = nx.from_pandas_edgelist(
        real_tx, 
        source = "out", 
        target = "in", 
        edge_attr=["value"], 
        create_using=nx.DiGraph(),
    )

    nx.set_node_attributes(tx_G_bytime, node_label_dic)
    # save_network 
    nx.write_gexf(tx_G_bytime, output_file)

    return

if __name__ == "__main__":
    node_label_dic = label_node(args.label_file, args.miner_file, args.genesis_file)
    construct_monthly_network(args.month, args.transaction_file, node_label_dic, args.output)