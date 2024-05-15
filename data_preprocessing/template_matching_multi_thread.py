import os
import cv2
import cv2.cuda
import numpy as np
from shutil import copy, move
import concurrent.futures

class OrientationClassifier:
    def __init__(self, cropped_folder, output_folder, template_folders, gpu_devices=None):
        self.cropped_folder = cropped_folder
        self.output_folder = output_folder
        self.orientation_types = list(template_folders.keys())
        self.templates = self.load_templates(template_folders, gpu_devices)

    def check_folder_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def load_templates(self, template_folders, gpu_devices):
        templates = {}

        # Check for CUDA-capable GPUs
        try:
            cuda_available_devices = cv2.cuda.getCudaEnabledDeviceCount()
            if cuda_available_devices == 0:
                print("No CUDA-capable GPU devices found. Using CPU for template matching.")
                gpu_devices = None
            else:
                if gpu_devices is None:
                    gpu_devices = [i for i in range(cuda_available_devices)]
                else:
                    gpu_devices = [device for device in gpu_devices if device < cuda_available_devices]
                    if not gpu_devices:
                        print("Invalid GPU device indices provided. Using CPU for template matching.")
                        gpu_devices = None

        except cv2.error as e:
            print(f"Error checking for CUDA devices: {e}")
            gpu_devices = None

        if gpu_devices:
            print(f"Using GPU devices: {', '.join(str(device) for device in gpu_devices)}")

        for orientation, folder in template_folders.items():
            templates[orientation] = []
            for filename in os.listdir(folder):
                if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.PNG') or filename.endswith('.JPG'):
                    template_path = os.path.join(folder, filename)
                    template_cpu = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                    template_gpus = [cv2.cuda_GpuMat() for _ in gpu_devices] if gpu_devices else [template_cpu]

                    for i, template_gpu in enumerate(template_gpus):
                        if gpu_devices:
                            cv2.cuda.setDevice(gpu_devices[i])
                            template_gpu.upload(template_cpu)
                            template_gpu = cv2.cuda.threshold(template_gpu, 127, 255, cv2.THRESH_BINARY)[1]  # Binarize the template
                            kernel = cv2.cuda_GpuMat()
                            template_gpu = cv2.cuda.erode(template_gpu, kernel, iterations=2)  # Remove small noise
                            template_gpu = cv2.cuda.dilate(template_gpu, kernel, iterations=2)  # Fill in gaps
                        else:
                            template_gpu = template_cpu

                    templates[orientation].append(template_gpus)
        return templates

    def detect_orientation(self, image_path, gpu_devices):
        image_cpu = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image_cpu is None:
            print(f"Error: Failed to load image {image_path}")
            return None, 0

        # Convert the image to GPU format
        image_gpus = [cv2.cuda_GpuMat() for _ in gpu_devices] if gpu_devices else [image_cpu]

        for i, image_gpu in enumerate(image_gpus):
            if gpu_devices:
                cv2.cuda.setDevice(gpu_devices[i])
                image_gpu.upload(image_cpu)
                image_gpu = cv2.cuda.threshold(image_gpu, 127, 255, cv2.THRESH_BINARY)[1]  # Binarize the image
                kernel = cv2.cuda_GpuMat()
                image_gpu = cv2.cuda.erode(image_gpu, kernel, iterations=2)  # Remove small noise
                image_gpu = cv2.cuda.dilate(image_gpu, kernel, iterations=2)  # Fill in gaps
            else:
                image_gpu = image_cpu

        best_match_scores = [0] * len(gpu_devices) if gpu_devices else [0]
        best_match_orientations = [None] * len(gpu_devices) if gpu_devices else [None]

        for orientation, templates in self.templates.items():
            for template_gpus in templates:
                for i, (template_gpu, image_gpu) in enumerate(zip(template_gpus, image_gpus)):
                    if template_gpu is not None:
                        match_gpu = cv2.cuda_GpuMat()
                        cv2.cuda.matchTemplate(image_gpu, template_gpu, match_gpu, cv2.TM_SQDIFF_NORMED)

                        match_cpu = match_gpu.download()
                        min_val, _, min_loc, _ = cv2.minMaxLoc(match_cpu)
                        match_score = 1 - min_val  # Invert the score since we're using TM_SQDIFF_NORMED

                        if match_score > best_match_scores[i]:
                            best_match_scores[i] = match_score
                            best_match_orientations[i] = orientation

                            # Visualize the match (optional)
                            height, width = template_gpu.shape[:2]
                            top_left = min_loc
                            bottom_right = (top_left[0] + width, top_left[1] + height)
                            cv2.rectangle(image_cpu, top_left, bottom_right, (0, 0, 255), 2)
                            # cv2.imshow('Matches', image_cpu)
                            # cv2.waitKey(0)
                            # cv2.destroyAllWindows()

        best_match_score = max(best_match_scores)
        best_match_orientation = best_match_orientations[best_match_scores.index(best_match_score)]

        return best_match_orientation, best_match_score

    def process_image(self, image_path, gpu_devices):
        filename = os.path.basename(image_path)
        orientation, match_score = self.detect_orientation(image_path, gpu_devices)
        output_dir = os.path.join(self.output_folder, orientation) if orientation else None
        self.check_folder_exists(output_dir)
        return orientation, match_score, filename, output_dir

    def classify_images(self, gpu_devices):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for filename in os.listdir(self.cropped_folder):
                if filename.endswith('.PNG'):
                    image_path = os.path.join(self.cropped_folder, filename)
                    future = executor.submit(self.process_image, image_path, gpu_devices)
                    futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                orientation, match_score, filename, output_dir = future.result()
                if orientation is not None and match_score > 0.7:
                    output_path = os.path.join(output_dir, filename)
                    move(os.path.join(self.cropped_folder, filename), output_path)
                    print(f"Moved {filename} to {output_dir} with match score {match_score}")

# Example usage
cropped_folder = './cropped_img/junc_T'
output_folder = './test_images'
template_folders = {
    'right': './class_data/junc_T/junc_T_right_up_down',
    'down': './class_data/junc_T/junc_T_down_right_left',
    'left': './class_data/junc_T/junc_T_left_up_down',
    'up': './class_data/junc_T/junc_T_up_right_left',
    'undefined': './class_data/junc_T/junc_T_undefined'
}


gpu_devices = [0]  # Use GPU 0 for template matching
classifier = OrientationClassifier(cropped_folder, output_folder, template_folders, gpu_devices)
classifier.classify_images(gpu_devices)

