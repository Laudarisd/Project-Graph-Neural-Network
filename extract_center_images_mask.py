import os
import shutil
import cv2
from collections import defaultdict

class DrawMask:
    def __init__(self, cropped_path, copy_to, original_img):
        self.cropped_path = cropped_path
        self.copy_to = copy_to
        self.original_img = original_img

    def parse_cropped_img(self):
        file_dict = defaultdict(list)  # Dictionary to store the file names and centers
        for root, dirs, files in os.walk(self.cropped_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    parts = file.split('_')
                    
                    if len(parts) == 3:  # Handle files with only numeric names
                        filtered_file_name = parts[0]
                    else:  # Handle files with alphanumeric names
                        filtered_file_name = '_'.join(parts[1:-2])

                    center_x, center_y = parts[-2], parts[-1].split('.')[0]
                    file_dict[filtered_file_name].append((float(center_x), float(center_y)))
        return file_dict

    def process_images(self):
        file_dict = self.parse_cropped_img()
        for filtered_file_name, centers in file_dict.items():
            original_file_path = os.path.join(self.original_img, f"{filtered_file_name}.png")
            if os.path.exists(original_file_path):
                img = cv2.imread(original_file_path)
                if img is not None:
                    for center_x, center_y in centers:
                        # Draw bounding box (assuming 100x100 box around center)
                        start_point = (int(center_x - 10), int(center_y - 10))
                        end_point = (int(center_x + 10), int(center_y + 10))
                        #color = (0, 255, 0)  # Green
                        # color red
                        color = (0, 0, 255)
                        thickness = 1
                        cv2.rectangle(img, start_point, end_point, color, thickness)

                        # Draw center point
                        center_point = (int(center_x), int(center_y))
                        center_color = (0, 0, 255)  # Red
                        center_thickness = -1
                        cv2.circle(img, center_point, 3, center_color, center_thickness)

                    # Save the processed image
                    destination_path = os.path.join(self.copy_to, os.path.basename(original_file_path))
                    cv2.imwrite(destination_path, img)
                    print(f"Processed and saved: {destination_path}")
                else:
                    print(f"Failed to read image: {original_file_path}")
            else:
                print(f"Original image not found: {original_file_path}")

if __name__ == '__main__':
    cropped_path = './raw_data-v2/direction/need_to_edit'
    copy_to = './raw_data-v2/direction/mask_img'
    original_img = './raw_data-v2/direction/images'
    os.makedirs(copy_to, exist_ok=True)
    draw_mask = DrawMask(cropped_path, copy_to, original_img)
    draw_mask.process_images()
