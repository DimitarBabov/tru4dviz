import os
import numpy as np
from PIL import Image

# Define paths
input_base_folder = "HRRRImages"  # Folder containing the original parameter folders
output_base_folder = "HRRRImages_Final"  # Folder for the final processed images

# Ensure output base folder exists
if not os.path.exists(output_base_folder):
    os.makedirs(output_base_folder)

# Precipitation parameters
precipitation_params = ["csnow", "cicep", "cfrzr", "crain"]

# Function to find folders dynamically
def find_param_folder(base_folder, param):
    for folder_name in os.listdir(base_folder):
        if folder_name.startswith(param):
            return os.path.join(base_folder, folder_name)
    return None

# Function to combine precipitation categories
def combine_precipitation(images):
    """
    Combine precipitation categories into a single image.
    - Green: No precipitation (all categories are 0).
    - Yellow: Only rain (crain is 1, others are 0).
    - Red: Any frozen precipitation (csnow, cicep, or cfrzr is 1).
    """
    # Load all images into a dictionary by parameter name
    data_dict = {}
    for param, image_path in images.items():
        if not os.path.exists(image_path):
            print(f"File not found: {image_path}. Skipping...")
            continue
        image = Image.open(image_path).convert("L")
        data = np.array(image)

        # Normalize the data to 0 and 1
        data = data // 255  # Normalize 255 to 1
        print(f"Loaded {param}: min={data.min()}, max={data.max()}, unique={np.unique(data)}")  # Debugging
        data_dict[param] = data

    # Ensure all required precipitation parameters are present
    if not all(param in data_dict for param in precipitation_params):
        print("Missing one or more precipitation images. Skipping combination.")
        return None

    # Initialize the combined output
    combined = np.zeros_like(list(data_dict.values())[0], dtype=np.uint8)

    # Apply the rules
    no_precip_mask = (
        (data_dict["csnow"] == 0)
        & (data_dict["cicep"] == 0)
        & (data_dict["cfrzr"] == 0)
        & (data_dict["crain"] == 0)
    )
    rain_only_mask = (
        (data_dict["crain"] == 1)
        & (data_dict["csnow"] == 0)
        & (data_dict["cicep"] == 0)
        & (data_dict["cfrzr"] == 0)
    )
    frozen_precip_mask = (
        (data_dict["csnow"] == 1)
        | (data_dict["cicep"] == 1)
        | (data_dict["cfrzr"] == 1)
    )

    # Assign colors
    combined[no_precip_mask] = 0  # Green (no precipitation)
    combined[rain_only_mask] = 1  # Yellow (rain only)
    combined[frozen_precip_mask] = 2  # Red (frozen precipitation)

    # Debugging: Log mask statistics
    print(f"No Precipitation Pixels: {np.sum(no_precip_mask)}")
    print(f"Rain Only Pixels: {np.sum(rain_only_mask)}")
    print(f"Frozen Precipitation Pixels: {np.sum(frozen_precip_mask)}")

    return combined

# Process precipitation
print("Processing precipitation...")
precipitation_folder = os.path.join(output_base_folder, "precipitation_final")
os.makedirs(precipitation_folder, exist_ok=True)

# Locate folders for precipitation parameters
precipitation_folders = {
    param: find_param_folder(input_base_folder, param) for param in precipitation_params
}

# Validate that all required folders exist
if not all(precipitation_folders.values()):
    print("One or more precipitation parameter folders are missing. Skipping precipitation processing.")
else:
    # Collect timestamps (intersection of all parameter timestamps)
    timestamps = set()
    for folder in precipitation_folders.values():
        timestamps.update(
            "_".join(img.split("_")[1:]).split(".")[0]  # Extract full timestamp (e.g., 20250106_1100)
            for img in os.listdir(folder)
            if img.endswith(".png")
        )

    # Ensure only timestamps that exist for all parameters are processed
    valid_timestamps = []
    for timestamp in timestamps:
        all_exist = all(
            os.path.exists(os.path.join(folder, f"{param}_{timestamp}.png"))
            for param, folder in precipitation_folders.items()
        )
        if all_exist:
            valid_timestamps.append(timestamp)
        else:
            print(f"Skipping timestamp {timestamp} due to missing data.")

    # Process each valid timestamp
    for timestamp in sorted(valid_timestamps):
        images = {
            param: os.path.join(folder, f"{param}_{timestamp}.png")
            for param, folder in precipitation_folders.items()
        }
        combined_image = combine_precipitation(images)
        if combined_image is not None:
            # Convert combined array to colored image
            combined_colored = np.zeros((*combined_image.shape, 3), dtype=np.uint8)
            combined_colored[combined_image == 0] = [0, 255, 0]  # Green (no precipitation)
            combined_colored[combined_image == 1] = [255, 255, 0]  # Yellow (rain only)
            combined_colored[combined_image == 2] = [255, 0, 0]  # Red (frozen precipitation)

            # Save the combined image
            output_path = os.path.join(precipitation_folder, f"precipitation_{timestamp}.png")
            Image.fromarray(combined_colored).save(output_path)
            print(f"Saved: {output_path}")
