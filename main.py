# main.py
import os
import torch
from engine.dataset import PoseGraphDataset

def main():
    # Paths
    root = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(root, 'data')
    
    # Ensure data directory exists
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    
    # Initialize and process dataset
    dataset = PoseGraphDataset(root=root)
    dataset.process()
    
    # Print the processed data
    for i in range(len(dataset)):
        data = dataset[i]
        print(f'Graph {i}:', data)
    
    # Save processed data
    for i in range(len(dataset)):
        data = dataset[i]
        torch.save(data, os.path.join(data_path, f'processed_data_{i}.pt'))

if __name__ == "__main__":
    main()
