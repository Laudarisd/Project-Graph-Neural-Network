import os
import shutil
import cv2

def main():
    unique_file_names = set()
    file_data = {}

    # Iterate over the files to collect file data
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            file_name_parts = file.strip('_').split('.')[0].split('_')
            filtered_file_name = '_'.join(file_name_parts[1:-1])
            unique_file_names.add(filtered_file_name)

            # Extract center points information
            file_name_parts = file.rsplit('.', 1)[0].split('_')
            image_name = '_'.join(file_name_parts[:-2])
            center_x = file_name_parts[-2]
            center_y = file_name_parts[-1]
            center_points = f"{center_x} {center_y}"
            key = image_name
            if key in file_data:
                file_data[key].append(center_points)
            else:
                file_data[key] = [center_points]

    print(unique_file_names)
    print(file_data)

    # Copy XML files
    for file_name in unique_file_names:
        for root, dirs, xml_files in os.walk(xmls_dir):
            for xml_file in xml_files:
                xml_file_name = xml_file.split('.')[0]
                if file_name == xml_file_name:
                    shutil.copy(os.path.join(root, xml_file), os.path.join(xmls_dest_dir, xml_file))
                    print(f"Copying {xml_file} to {xmls_dest_dir}")
                    break

    # Copy image files and add circles
    for root, dirs, image_files in os.walk(image_dir):
        for image_file in image_files:
            image_file_name = image_file.split('.')[0]
            if image_file_name in unique_file_names:
                shutil.copy(os.path.join(root, image_file), os.path.join(images_dest_dir, image_file))
                print(f"Copying {image_file} to {images_dest_dir}")

                image_path = os.path.join(images_dest_dir, image_file)
                image_name = os.path.splitext(image_file)[0]

                # Read the image
                image = cv2.imread(image_path)
                if image is not None:
                    for key, value in file_data.items():
                        if image_name in key:
                            for center_points in value:
                                x, y = map(float, center_points.split(' '))
                                x, y = int(x), int(y)
                                # Draw circles
                                cv2.circle(image, (x, y), 3, (0, 0, 255), -1)

                    # Save the modified image
                    cv2.imwrite(os.path.join(images_dest_dir, f"{image_name}.PNG"), image)
                else:
                    print(f"Failed to read image: {image_path}")

    print(unique_file_names)
    print(len(unique_file_names))

if __name__ == "__main__":
    root_dir = "./class_data/junc_I/junc_I_undefined"
    xmls_dir = "./raw_data-v2-editing-now/xmls-v2"
    image_dir = "./raw_data-v2-editing-now/images-v2"
    xmls_dest_dir = "./raw_data-v2-editing-now/undefined/xmls-dest"
    images_dest_dir = "./raw_data-v2-editing-now/undefined/images-dest"
    os.makedirs(xmls_dest_dir, exist_ok=True)
    os.makedirs(images_dest_dir, exist_ok=True)
    main()