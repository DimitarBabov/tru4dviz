import os
import numpy as np
from PIL import Image

# Paths
input_base_folder = "HRRRImages"  # Folder containing the grayscale images
output_base_folder = "HRRRImages_Final"  # Folder for the final processed color-coded images

# Ensure the output folder exists
if not os.path.exists(output_base_folder):
    os.makedirs(output_base_folder)

# Parameters and thresholds
thresholds = {
    "t": {  # Temperature thresholds in Fahrenheit
        "green": 33,  # >33°F
        "yellow": (32, 33),  # Between 32°F and 33°F
        "red": 32,  # ≤32°F
    },
    "gust": {  # Wind gust thresholds in mph
        "green": 35,  # <35 mph
        "yellow": (35, 58),  # Between 35 and 58 mph
        "red": 58,  # >58 mph
    },
}

# Function to extract min and max values from the folder name
def extract_min_max(folder_name):
    """
    Extract min and max values from the folder name.
    Example: "t_min37.37_max102.52" -> (37.37, 102.52)
    """
    try:
        min_val = float(folder_name.split("_min")[1].split("_max")[0])
        max_val = float(folder_name.split("_max")[1])
        return min_val, max_val
    except (IndexError, ValueError):
        raise ValueError(f"Invalid folder name format: {folder_name}")

# Function to apply color-coding rules
def apply_color_coding(data, param):
    """
    Apply color thresholds for temperature or wind gusts:
    - Green, Yellow, Red based on the thresholds.
    """
    param_thresholds = thresholds[param]
    processed = np.zeros((*data.shape, 3), dtype=np.uint8)

    if param == "t":
        # Apply temperature thresholds
        processed[data > param_thresholds["green"]] = [0, 255, 0]  # Green
        processed[(data > param_thresholds["yellow"][0]) & (data <= param_thresholds["yellow"][1])] = [255, 255, 0]  # Yellow
        processed[data <= param_thresholds["red"]] = [255, 0, 0]  # Red
    elif param == "gust":
        # Apply wind gust thresholds
        processed[data < param_thresholds["green"]] = [0, 255, 0]  # Green
        processed[(data >= param_thresholds["yellow"][0]) & (data <= param_thresholds["yellow"][1])] = [255, 255, 0]  # Yellow
        processed[data > param_thresholds["red"]] = [255, 0, 0]  # Red

    return processed

# Process folders for temperature and wind gusts
for folder_name in os.listdir(input_base_folder):
    if folder_name.startswith("t_") or folder_name.startswith("gust_"):  # Process only relevant folders
        param = "t" if folder_name.startswith("t_") else "gust"
        input_folder = os.path.join(input_base_folder, folder_name)
        output_folder = os.path.join(output_base_folder, f"{param}_final")
        os.makedirs(output_folder, exist_ok=True)

        # Extract min and max values from the folder name
        try:
            min_val, max_val = extract_min_max(folder_name)
            print(f"Processing {param} with min={min_val}, max={max_val} from folder: {folder_name}")
        except ValueError as e:
            print(e)
            continue

        # Process all images in the folder
        for img_name in os.listdir(input_folder):
            if img_name.endswith(".png"):
                img_path = os.path.join(input_folder, img_name)
                image = Image.open(img_path).convert("L")
                data = np.array(image, dtype=np.float32)  # Load grayscale data

                # Scale grayscale (0–255) to the real-world values
                real_data = (data / 255) * (max_val - min_val) + min_val
                print(f"Image: {img_name} - Scaled {param} min={real_data.min()}, max={real_data.max()}")

                # Apply color-coding
                color_coded_image = apply_color_coding(real_data, param)

                # Save the color-coded image
                output_path = os.path.join(output_folder, img_name)
                Image.fromarray(color_coded_image).save(output_path)
                print(f"Saved: {output_path}")

print("Temperature and wind gust processing completed.")
