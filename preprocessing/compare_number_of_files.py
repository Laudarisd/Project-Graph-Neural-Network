import os
import shutil

#Compare files name and number in jsons, and print which folder has more files and what files
def comparedfiles(images_dir, jsons_dir):
    #parse image files and remove extension
    image_files = []
    for file in os.listdir(images_dir):
        if file.endswith(('.png', '.jpg', '.PNG', '.JPG')):
            image_files.append(os.path.splitext(file)[0])
    #parse json files and remove extension
    json_files = []
    for file in os.listdir(jsons_dir):
        if file.endswith('.json'):
            json_files.append(os.path.splitext(file)[0])

    #compare files
    if len(image_files) > len(json_files):
        print(f"More image files than json files: {len(image_files)} > {len(json_files)}")
        print("Extra image files:")
        for file in image_files:
            if file not in json_files:
                print(file)
    elif len(image_files) < len(json_files):
        print(f"More json files than image files: {len(json_files)} > {len(image_files)}")
        print("Extra json files:")
        for file in json_files:
            if file not in image_files:
                print(file)
    else:
        print(f"Number of image files and json files are equal: {len(image_files)}")

if __name__ == '__main__':
    images_dir = './images'
    jsons_dir = './json'
    comparedfiles(images_dir, jsons_dir)