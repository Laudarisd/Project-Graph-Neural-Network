import os
from shutil import copy
import re

compare_to = './compare_img/refined_I'
cropped_img = './compare_img/cropped'
copy_to = './compare_img/undefined'

if not os.path.exists(copy_to):
    os.makedirs(copy_to)

def parse_filename(file_name):
    # Match the coordinates and extension only
    match = re.match(r'(.+)_(\d+\.\d+)_(\d+\.\d+)(\.PNG)$', file_name, re.IGNORECASE)
    if match:
        x = format(float(match.group(2)), ".6f")  # Format the coordinate with six decimal places
        y = format(float(match.group(3)), ".6f")
        return ((x, y), file_name)  # Return coordinates as the key, and the full file name
    return (None, file_name)

def get_files(directory):
    files_dict = {}
    for file in os.listdir(directory):
        key, original_file_name = parse_filename(file)
        if key:
            if key not in files_dict:
                files_dict[key] = []
            files_dict[key].append(original_file_name)
    return files_dict

def copy_unique_files(compare_to, cropped_img, copy_to):
    files_compared = get_files(compare_to)
    files_cropped = get_files(cropped_img)

    print(f"Total files in compared folder: {len(files_compared)}")
    print(f"Total files in cropped folder: {len(files_cropped)}")

    unique_files = []
    for coords, filenames in files_cropped.items():
        if coords not in files_compared:
            unique_files.extend(filenames)

    
    unique_in_compared = []

    for coords, filenames in files_compared.items():
        if coords not in files_cropped:
            unique_in_compared.extend(filenames)

    print(f"Total unique files to copy from cropped: {len(unique_files)}")
    print(f"Unique files to copy from compared: {len(unique_in_compared)}")

    #Copy unique files to copy_to directory
    for file_name in unique_files:
        src_file_path = os.path.join(cropped_img, file_name)
        dest_file_path = os.path.join(copy_to, file_name)
        copy(src_file_path, dest_file_path)
        print(f"Copied '{file_name}' to '{copy_to}'.")

if __name__ == '__main__':
    copy_unique_files(compare_to, cropped_img, copy_to)
