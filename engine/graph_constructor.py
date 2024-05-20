# engine/graph_constructor.py
import numpy as np
import torch
from torch_geometric.data import Data

def process_data(data_list):
    nodes = []
    edges = []
    node_features = []

    for data in data_list:
        for index, row in data.iterrows():
            start_node = (row['Start X'], row['Start Y'])
            end_node = (row['End X'], row['End Y'])
            
            if start_node not in nodes:
                nodes.append(start_node)
                node_features.append([row['Start X'], row['Start Y']])
            
            if end_node not in nodes:
                nodes.append(end_node)
                node_features.append([row['End X'], row['End Y']])
            
            edges.append((nodes.index(start_node), nodes.index(end_node)))
    
    node_features = np.array(node_features)
    edges = np.array(edges)
    
    return nodes, edges, node_features

def create_graph(node_features, edges):
    node_features = torch.tensor(node_features, dtype=torch.float)
    edge_index = torch.tensor(edges.T, dtype=torch.long)
    
    data = Data(x=node_features, edge_index=edge_index)
    
    return data
