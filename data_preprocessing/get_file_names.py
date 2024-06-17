import os
import csv

def get_image_files(images_dir):
    image_files = []
    for file in os.listdir(images_dir):
        if file.endswith(('.png', '.jpg', '.PNG', '.JPG')):
            image_files.append(os.path.splitext(file)[0])
    return image_files

def write_to_csv(image_files, csv_filename):
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ImageName'])
        for image_file in image_files:
            writer.writerow([image_file])

if __name__ == '__main__':
    images_dirs = {
        'test': './test/images',
        'train': './train/images',
        'valid': './valid/images'
    }

    for key, dir_path in images_dirs.items():
        image_files = get_image_files(dir_path)
        csv_filename = f'{key}_images.csv'
        write_to_csv(image_files, csv_filename)
        print(f'Wrote {len(image_files)} entries to {csv_filename}')
