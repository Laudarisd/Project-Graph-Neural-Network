# engine/dataset.py
import os
import torch
from torch_geometric.data import InMemoryDataset
from engine.data_loader import load_data
from engine.graph_constructor import process_data, create_graph
from engine.data_normalizer.py import normalize_features

class PoseGraphDataset(InMemoryDataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super(PoseGraphDataset, self).__init__(root, transform, pre_transform)
        self.data_list = load_data(os.path.join(root, 'csv_data', '*.csv'))
    
    @property
    def raw_file_names(self):
        return [os.path.basename(file) for file in self.data_list]
    
    @property
    def processed_file_names(self):
        return [f'data_{i}.pt' for i in range(len(self.data_list))]
    
    def download(self):
        pass
    
    def process(self):
        for i, data in enumerate(self.data_list):
            nodes, edges, node_features = process_data([data])
            node_features = normalize_features(node_features)
            graph_data = create_graph(node_features, edges)
            
            torch.save(graph_data, os.path.join(self.processed_dir, f'data_{i}.pt'))
    
    def len(self):
        return len(self.processed_file_names)
    
    def get(self, idx):
        data = torch.load(os.path.join(self.processed_dir, f'data_{idx}.pt'))
        return data
