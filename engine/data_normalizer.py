# engine/data_normalizer.py
from sklearn.preprocessing import StandardScaler

def normalize_features(features):
    scaler = StandardScaler()
    normalized_features = scaler.fit_transform(features)
    return normalized_features
