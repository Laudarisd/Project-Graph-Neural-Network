import os

def count_files_in_dir(directory):
    return len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])




directory = "./yolo_format"
file_count = count_files_in_dir(directory)
print(f"Number of files in {directory}: {file_count}")