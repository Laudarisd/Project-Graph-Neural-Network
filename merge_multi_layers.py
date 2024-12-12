import os
from PIL import Image, ImageFile
import numpy as np
from typing import Dict, List

# Increase decompression limit to handle large images safely
Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True


class MergeImages:
    def __init__(self, scale_factor: int = 2, resolution_dpi: int = 300):
        self.scale_factor = scale_factor
        self.resolution_dpi = resolution_dpi

    def enhance_resolution(self, image: Image.Image, method: str = 'lanczos') -> Image.Image:
        width, height = image.size
        resampling_methods = {
            'lanczos': Image.Resampling.LANCZOS,
            'bicubic': Image.Resampling.BICUBIC,
            'nearest': Image.Resampling.NEAREST
        }
        resampling = resampling_methods.get(method.lower(), Image.Resampling.LANCZOS)

        # Return the original image if no scaling is needed
        return image

    def merge_layers(self, input_dir: str, output_path: str):
        # Create merged_img folder inside the output directory
        output_dir = os.path.join(output_path, "merged_img")
        os.makedirs(output_dir, exist_ok=True)

        # Collect all image paths across subdirectories
        image_paths = []
        for root, dirs, files in os.walk(input_dir):
            main_folder = os.path.relpath(root, input_dir).split(os.sep)[0]
            if root == input_dir:
                continue
            #print(f"Processing {dirs}")
            for file in files:
                #if file.lower().endswith(('.png', '.jpg', '.jpeg', '.PNG')):
                image_paths.append(os.path.join(root, file))
        if not image_paths:
            print("No images found to process")
            return
        try:
            # Open the first image and enhance resolution
            base_image = Image.open(image_paths[0]).convert('L')
            enhanced_base = self.enhance_resolution(base_image, method='lanczos')
            width, height = enhanced_base.size
            # Create a white background
            merged_array = np.full((height, width), 255, dtype=np.uint8)
            for layer_path in image_paths:
                try:
                    # Use absolute paths and handle potential encoding issues
                    layer = Image.open(os.path.abspath(layer_path)).convert('L')
                    # Resize layer to match base image dimensions if needed
                    if layer.size != (width, height):
                        layer = layer.resize((width, height), Image.Resampling.LANCZOS)
                    enhanced_layer = self.enhance_resolution(layer, method='lanczos')
                    layer_array = np.array(enhanced_layer)
                    # Combine layers, preserving black pixels
                    merged_array = np.minimum(merged_array, layer_array)
                except PermissionError as pe:
                    print(f"Permission error processing {layer_path}: {pe}")
                    print(f"Check file permissions for: {layer_path}")
                except Exception as e:
                    print(f"Error processing {layer_path}: {str(e)}")
            # Generate a unique filename based on input directory name
            base_name = os.path.basename(input_dir)
            final_output_path = os.path.join(output_dir, f"{main_folder}.png")
            # Convert back to an image
            final_image = Image.fromarray(merged_array)
            final_image.info['dpi'] = (self.resolution_dpi, self.resolution_dpi)
            final_image.save(final_output_path, quality=95, dpi=(self.resolution_dpi, self.resolution_dpi))
            print(f"Merged image saved to: {final_output_path}")

        except Exception as e:
            print(f"Unexpected error in merge process: {e}")
