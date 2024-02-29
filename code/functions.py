
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import time

# Define functions

def delete_by_edge_threshold_and_degree(graph, value, threshold, num = 0):
    thre = np.percentile(np.array(list(graph.edges.data('value')))[:,2], threshold)
    selected_edges = [(u,v) for u,v,e in graph.edges(data=True) if e[value] < thre]
    
    graph.remove_edges_from(list(map(lambda e: (e[0], e[1]), selected_edges)))
    weakly_set = max(nx.weakly_connected_components(graph), key = len)
    remove_nodes_set = set(graph.nodes) - weakly_set
    graph.remove_nodes_from(remove_nodes_set)
    
    selected_nodes = [node for node,degree in graph.degree() if degree < num]
    graph.remove_nodes_from(selected_nodes)
    weakly_set = max(nx.weakly_connected_components(graph), key = len)
    remove_nodes_set = set(graph.nodes) - weakly_set
    graph.remove_nodes_from(remove_nodes_set)
    
    return graph

def get_tx_edges(tx_filename, txvalue_filename, miner):
    # setting transaction

    transaction = pd.read_csv(tx_filename, names = ["txID", "blockID", "in", "out"], header=None, sep=" ")
    txvalue = pd.read_csv(txvalue_filename, names = ["txID", "value", "gas_price", "gas_used"], header=None, sep=" ")
    transaction = pd.merge(transaction, txvalue, on="txID")
    

    # if you want to think tx_fee as one of the transaction, merge miner information to transaction
    transaction = pd.merge(transaction, miner, on="blockID", how = "left")
    transaction["tx_fee"] = transaction["gas_price"]*transaction["gas_used"]
    miner_txfee = transaction[["out", "addID", "tx_fee", "txID"]]
    miner_txfee = miner_txfee.rename(columns = {"addID": "in", "tx_fee": "value"})
    transaction = pd.concat([transaction, miner_txfee])

    return transaction

def give_node_deep_color(graph):
    for node in graph.nodes():
        ty = graph.nodes[node].get("type")
        if ty == "miner":
            graph.nodes[node]["deep_color"] = "#d9534f"#10 #"r"
        elif ty == "Exchange":
            graph.nodes[node]["deep_color"] = "#5cb85c" #20 #"g"
        elif ty == "Gambling":
            graph.nodes[node]["deep_color"] = "#ffff00" #"y"
        elif ty == "genesis":
            graph.nodes[node]["deep_color"] = "#0275dB" #40 #"b"
        elif ty == "ICO":
            graph.nodes[node]["deep_color"] = "#5fedeb" # aqua
        elif ty != None:
            graph.nodes[node]["deep_color"] = "#aa46be" # pink
        else:
            graph.nodes[node]["deep_color"] = "#808080" #100 #"k"

            
def select_top10(sorted_list, nametag, type_, colors):
    x = []
    y = []
    c = []
    for i in range(10):
        name = nametag.get(sorted_list[i][0])
        node_type = type_.get(sorted_list[i][0])
        color = colors.get(sorted_list[i][0])
        if name:
            node_name = name
        else:
            node_name = str(sorted_list[i][0])
        if node_type:
            node_name = node_name + "(" + str(node_type) + ")"
        
        x.append(node_name)
        y.append(sorted_list[i][1])
        c.append(color)
    return x,y,c


def plot_degree_centrality(G, time_from):
    
#     giant = delete_by_edge_threshold_and_degree(G.to_directed(), "value", 97, 2)
#     degree_centrality = nx.degree_centrality(giant)
    degree_centrality = weighted_degree_centrality(G)
    sorted_dc = sorted(degree_centrality.items(), key=(lambda x: x[1]), reverse = True)
    

    nametag = nx.get_node_attributes(G,"nametag")
    type_ = nx.get_node_attributes(G,"type")
    give_node_deep_color(G)
    deep_color = nx.get_node_attributes(G,"deep_color")

    x_dc, y_dc, c_dc = select_top10(sorted_dc, nametag, type_, deep_color)

    plt.figure(figsize = (12,9))
    plt.barh(x_dc, y_dc, color = c_dc)
    # sns.barplot(x_dc, y_dc)
    plt.xticks(fontsize = 14)
    plt.yticks(fontsize = 14)
    time_to = time_from + relativedelta(months=2)
    plt.title(time_from.strftime("%m/%d/%Y")+ "-" + time_to.strftime("%m/%d/%Y"), fontsize = 18)
    # plt.savefig("../Image_files/dc_"+time_from.strftime("%Y_%m")+".png", format="PNG", bbox_inches='tight', dpi=200)
    plt.show()
    
    return degree_centrality

def weighted_degree_centrality(G, normalized=True):
    
    weighted_dc = {n:0.0 for n in G.nodes()}
    for u, v, d in G.edges(data=True):
        weighted_dc[u]+=d['value']
        weighted_dc[v]+=d['value']
    if normalized:
        weighted_dc_sum = sum(weighted_dc.values())
        weighted_dc = {k:v/weighted_dc_sum for k, v in weighted_dc.items()}
    
    return weighted_dc