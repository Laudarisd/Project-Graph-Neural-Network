import os
import json
import re

# Directory containing JSON files
json_dir = "json"  # Replace with your directory path

# Target image path format
target_prefix = "..\\images\\"

# Function to check and update imagePath
def update_image_path(json_file_path):
    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get the current imagePath
    current_image_path = data.get("imagePath", "")
    json_filename = os.path.basename(json_file_path)  # e.g., "image1.json"
    image_base_name = os.path.splitext(json_filename)[0]  # e.g., "image1"
    
    # Expected image path format: ..\images\image_base_name.extension
    # Assuming the extension should match typical image formats (e.g., .jpg, .png)
    expected_image_path = f"{target_prefix}{image_base_name}.PNG"  # Default to .jpg, adjust if needed

    # Check if the current imagePath matches the expected format
    if not re.match(r"\.\.\\images\\[^\\]+\.(jpg|png|jpeg|bmp)$", current_image_path, re.IGNORECASE):
        print(f"Updating {json_file_path}:")
        print(f"  Old imagePath: {current_image_path}")
        # Update to the expected format
        data["imagePath"] = expected_image_path
        print(f"  New imagePath: {expected_image_path}")

        # Write the updated JSON back to the file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    else:
        print(f"No update needed for {json_file_path}: {current_image_path}")

# Iterate through all JSON files in the directory
for filename in os.listdir(json_dir):
    if filename.endswith(".json"):
        json_file_path = os.path.join(json_dir, filename)
        update_image_path(json_file_path)

print("Done processing all JSON files.")