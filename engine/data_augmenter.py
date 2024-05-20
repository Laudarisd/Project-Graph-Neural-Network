# engine/data_augmenter.py
from torchvision import transforms
import torch
import numpy as np

augmentations = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(30)
])

def augment_node_coordinates(node_features):
    augmented_features = []
    for feature in node_features:
        feature_tensor = torch.tensor(feature).unsqueeze(0)
        augmented_feature = augmentations(feature_tensor)
        augmented_features.append(augmented_feature.squeeze(0).numpy())
    return np.array(augmented_features)
