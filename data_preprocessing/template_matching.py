import os
import cv2
import numpy as np
from shutil import copy, move

class OrientationClassifier:
    def __init__(self, cropped_folder, output_folder, template_folders):
        self.cropped_folder = cropped_folder
        self.output_folder = output_folder
        self.orientation_types = list(template_folders.keys())
        self.templates = self.load_templates(template_folders)

    def check_folder_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def load_templates(self, template_folders):
        templates = {}
        for orientation, folder in template_folders.items():
            templates[orientation] = []
            for filename in os.listdir(folder):
                if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.PNG') or filename.endswith('.JPG'):
                    template_path = os.path.join(folder, filename)
                    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                    template = cv2.threshold(template, 127, 255, cv2.THRESH_BINARY)[1]  # Binarize the template
                    
                    # Apply additional preprocessing
                    template = cv2.erode(template, None, iterations=2)  # Remove small noise
                    template = cv2.dilate(template, None, iterations=2)  # Fill in gaps
                    
                    templates[orientation].append(template)
        return templates

    def detect_orientation(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"Error: Failed to load image {image_path}")
            return None, 0

        image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)[1]  # Binarize the image

        # Apply additional preprocessing
        image = cv2.erode(image, None, iterations=2)  # Remove small noise
        image = cv2.dilate(image, None, iterations=2)  # Fill in gaps

        best_match_score = 0
        best_match_orientation = None

        for orientation, templates in self.templates.items():
            for template in templates:
                if template is not None:
                    match = cv2.matchTemplate(image, template, cv2.TM_SQDIFF_NORMED)
                    min_val, _, min_loc, _ = cv2.minMaxLoc(match)
                    match_score = 1 - min_val  # Invert the score since we're using TM_SQDIFF_NORMED

                    if match_score > best_match_score:
                        best_match_score = match_score
                        best_match_orientation = orientation

                        # Visualize the match (optional)
                        height, width = template.shape[:2]
                        top_left = min_loc
                        bottom_right = (top_left[0] + width, top_left[1] + height)
                        cv2.rectangle(image, top_left, bottom_right, (0, 0, 255), 2)
                        # cv2.imshow('Matches', image)
                        # cv2.waitKey(0)
                        # cv2.destroyAllWindows()

        return best_match_orientation, best_match_score
    
    def classify_images(self):
        for filename in os.listdir(self.cropped_folder):
            if filename.endswith('.PNG'):
                image_path = os.path.join(self.cropped_folder, filename)
                orientation, match_score = self.detect_orientation(image_path)
                if orientation is not None and match_score > 0.4:  # Adjust the threshold as needed
                    output_dir = os.path.join(self.output_folder, orientation)
                    self.check_folder_exists(output_dir)
                    output_path = os.path.join(output_dir, filename)
                    move(image_path, output_path)
                    print(f"Moved {filename} to {output_dir} with match score {match_score}")

# Example usage
cropped_folder = './class_data/junc_I/junc_I_undefined'
output_folder = './test_images'
template_folders = {
    'junc_I_up': './class_data/junc_I/junc_I_up',
    'junc_I_down': './class_data/junc_I/junc_I_down',
    'junc_I_right': './class_data/junc_I/junc_I_right',
    'junc_I_left': './class_data/junc_I/junc_I_left',
}

classifier = OrientationClassifier(cropped_folder, output_folder, template_folders)
classifier.classify_images()