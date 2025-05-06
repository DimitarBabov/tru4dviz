import os
import pygrib
import numpy as np
from PIL import Image, ImageOps
from pyproj import Proj, transform

# Define the path to the GRIB2 files
data_folder = "HRRRdata"  # Folder where the GRIB2 files are stored
output_base_folder = "HRRRImages"  # Base folder to store the reprojected images
forecast_prefix = "hrrr.t10z.wrfsfc"  # Prefix for GRIB2 files
forecast_hours = range(1, 19)  # Forecast hours from f01 to f18 (adjust if needed)

# Check if the data folder exists
if not os.path.exists(data_folder):
    raise FileNotFoundError(f"Data folder not found: {data_folder}")

# Create the output base folder if it doesn't exist
if not os.path.exists(output_base_folder):
    os.makedirs(output_base_folder)
    print(f"Created folder: {output_base_folder}")
else:
    print(f"Using existing folder: {output_base_folder}")

# Define Lambert Conformal Conic (LCC) projection (source) and Web Mercator projection (target)
lcc_proj = Proj(proj="lcc", lon_0=262.5, lat_0=38.5, lat_1=38.5, lat_2=38.5, a=6371229, b=6371229)
web_mercator_proj = Proj(proj="merc", a=6378137, b=6378137)  # EPSG:3857

# Parameters of interest (short name and description)
desired_parameters = {
    "prate": "Precipitation rate",
    "csnow": "Categorical snow",
    "cicep": "Categorical ice pellets",
    "cfrzr": "Categorical freezing rain",
    "crain": "Categorical rain",
    "t": "Temperature",
    "gust": "Wind speed (gust)"
}

# Initialize global min/max trackers for each parameter
global_min_max = {param: {"min": float("inf"), "max": float("-inf")} for param in desired_parameters.keys()}

# Unit conversions
def convert_units(param, data):
    """Convert units for specific parameters."""
    if param == "t":  # Convert Kelvin to Fahrenheit
        return (data - 273.15) * 9/5 + 32  # K to °F
    elif param == "gust":  # Convert m/s to mph
        return data * 2.23694  # m/s to mph
    return data  # Return data unchanged for other parameters

### FIRST PASS: Compute Global Min/Max ###
print("Starting first pass to compute global min/max values...")
for hour in forecast_hours:
    # Construct the GRIB file name
    grib_file_name = f"{forecast_prefix}f{hour:02d}.grib2"
    grib_file_path = os.path.join(data_folder, grib_file_name)

    # Check if the GRIB file exists
    if not os.path.exists(grib_file_path):
        print(f"File not found: {grib_file_path}. Skipping...")
        continue

    print(f"Analyzing GRIB file: {grib_file_path}")

    # Open the GRIB2 file
    try:
        grbs = pygrib.open(grib_file_path)
        for grb in grbs:
            # Filter by desired parameters and surface level
            if grb.shortName in desired_parameters and grb.level == 0:
                # Update global min/max for this parameter
                param = grb.shortName
                data = convert_units(param, grb.values)  # Apply unit conversion
                global_min_max[param]["min"] = min(global_min_max[param]["min"], np.nanmin(data))
                global_min_max[param]["max"] = max(global_min_max[param]["max"], np.nanmax(data))
        grbs.close()
    except Exception as e:
        print(f"Error analyzing file {grib_file_name}: {e}")

print("First pass completed. Global min/max values:")
for param, min_max in global_min_max.items():
    print(f"  {param}: min = {min_max['min']}, max = {min_max['max']}")

### SECOND PASS: Generate Images Using Global Min/Max ###
print("Starting second pass to generate images...")
param_folders = {}  # To store the original folder paths for renaming later
for param in desired_parameters.keys():
    param_folder = os.path.join(output_base_folder, param)
    if not os.path.exists(param_folder):
        os.makedirs(param_folder)
        print(f"Created folder: {param_folder}")
    param_folders[param] = param_folder

for hour in forecast_hours:
    # Construct the GRIB file name
    grib_file_name = f"{forecast_prefix}f{hour:02d}.grib2"
    grib_file_path = os.path.join(data_folder, grib_file_name)

    # Check if the GRIB file exists
    if not os.path.exists(grib_file_path):
        print(f"File not found: {grib_file_path}. Skipping...")
        continue

    print(f"Processing GRIB file: {grib_file_path}")

    # Open the GRIB2 file
    try:
        grbs = pygrib.open(grib_file_path)
        for grb in grbs:
            # Filter by desired parameters and surface level
            if grb.shortName in desired_parameters and grb.level == 0:
                param = grb.shortName
                param_folder = param_folders[param]

                # Extract metadata
                forecast_time = grb.validDate.strftime("%Y%m%d_%H%M")
                file_name = f"{param}_{forecast_time}.png"
                file_path = os.path.join(param_folder, file_name)

                # Normalize data using global min/max
                data = convert_units(param, grb.values)  # Apply unit conversion
                min_val = global_min_max[param]["min"]
                max_val = global_min_max[param]["max"]
                normalized_data = (data - min_val) / (max_val - min_val) * 255
                normalized_data = np.nan_to_num(normalized_data).astype(np.uint8)

                # Create grayscale image
                image = Image.fromarray(normalized_data)

                # Flip the image vertically
                flipped_image = ImageOps.flip(image)

                # Save the image
                flipped_image.save(file_path)
                print(f"Saved: {file_path} (Units: {grb.units})")
        grbs.close()
    except Exception as e:
        print(f"Error processing file {grib_file_name}: {e}")

# Rename parameter folders to include min/max values
print("Renaming parameter folders to include min/max values...")
for param, min_max in global_min_max.items():
    min_val, max_val = min_max["min"], min_max["max"]
    new_folder_name = f"{param}_min{min_val:.2f}_max{max_val:.2f}"
    old_folder_path = param_folders[param]
    new_folder_path = os.path.join(output_base_folder, new_folder_name)

    # Rename the folder
    os.rename(old_folder_path, new_folder_path)
    print(f"Renamed folder: {old_folder_path} -> {new_folder_path}")

print("Image generation completed.")
