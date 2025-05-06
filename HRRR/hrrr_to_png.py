import os
import pygrib
import numpy as np
from PIL import Image, ImageOps

from pyproj import Proj, transform
# NEW: import our reprojection function
from reproject_utils import reproject_to_web_mercator

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

# Define Lambert Conformal Conic (LCC) projection (source) - NOT used directly if we rely on grb.latlons()
lcc_proj = Proj(proj="lcc", lon_0=-97.5, lat_0=38.5, lat_1=38.5, lat_2=38.5, a=6371229, b=6371229)

# Web Mercator projection
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
    if param == "t":  # Kelvin -> Fahrenheit
        return (data - 273.15) * 9/5 + 32  # K to °F
    elif param == "gust":  # m/s -> mph
        return data * 2.23694
    return data  # Return data unchanged for others

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
                data = convert_units(param, grb.values)
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
param_folders = {}
for param in desired_parameters.keys():
    param_folder = os.path.join(output_base_folder, param)
    if not os.path.exists(param_folder):
        os.makedirs(param_folder)
        print(f"Created folder: {param_folder}")
    param_folders[param] = param_folder

for hour in forecast_hours:
    grib_file_name = f"{forecast_prefix}f{hour:02d}.grib2"
    grib_file_path = os.path.join(data_folder, grib_file_name)

    if not os.path.exists(grib_file_path):
        print(f"File not found: {grib_file_path}. Skipping...")
        continue

    print(f"Processing GRIB file: {grib_file_path}")

    try:
        grbs = pygrib.open(grib_file_path)
        for grb in grbs:
            if grb.shortName in desired_parameters and grb.level == 0:
                param = grb.shortName
                param_folder = param_folders[param]

                forecast_time = grb.validDate.strftime("%Y%m%d_%H%M")
                file_name = f"{param}_{forecast_time}.png"
                file_path = os.path.join(param_folder, file_name)

                # 1) Get raw data + convert units
                raw_data = convert_units(param, grb.values)

                # 2) Reproject to Web Mercator
                #    (We assume grb.latlons() returns lat/lon in degrees)
                lats, lons = grb.latlons()  # shape = (ny, nx)
                reproj_data, _, _ = reproject_to_web_mercator(raw_data, lats, lons)

                # 3) Normalize data using global min/max
                min_val = global_min_max[param]["min"]
                max_val = global_min_max[param]["max"]
                normalized_data = (reproj_data - min_val) / (max_val - min_val)
                normalized_data = np.nan_to_num(normalized_data, nan=0.0)
                normalized_data = (normalized_data * 255).clip(0, 255).astype(np.uint8)

                # 4) Create grayscale image
                image = Image.fromarray(normalized_data)

                # 5) Flip the image vertically (if you want North-up in typical screen coords)
                flipped_image = ImageOps.flip(image)

                # 6) Save the image
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

    os.rename(old_folder_path, new_folder_path)
    print(f"Renamed folder: {old_folder_path} -> {new_folder_path}")

print("Image generation completed.")
