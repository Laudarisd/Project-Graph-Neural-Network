# engine/data_loader.py
import pandas as pd
import glob

def load_data(file_pattern):
    all_data = []
    for file in glob.glob(file_pattern):
        data = pd.read_csv(file)
        all_data.append(data)
    return all_data
