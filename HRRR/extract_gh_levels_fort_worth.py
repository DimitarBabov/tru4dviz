import numpy as np
import os
import pandas as pd
import re

# File paths
DATA_FOLDER = "HRRRdata_nat"
OUTPUT_FOLDER = os.path.join(DATA_FOLDER, "levels_extracted")

# Fort Worth bounding box (lon_min, lat_min, lon_max, lat_max)
FORT_WORTH_BBOX = (-97.648, 32.742, -96.898, 33.231)

# Load lat/lon arrays
lats = np.load(os.path.join(OUTPUT_FOLDER, "latitudes.npy"))
lons = np.load(os.path.join(OUTPUT_FOLDER, "longitudes.npy"))

# Create mask for Fort Worth bounding box
lon_min, lat_min, lon_max, lat_max = FORT_WORTH_BBOX
mask = (
    (lons >= lon_min) & (lons <= lon_max) &
    (lats >= lat_min) & (lats <= lat_max)
)

# Find all available gh_lev*.npy files
gh_files = [f for f in os.listdir(OUTPUT_FOLDER) if re.match(r"gh_lev\d+\.npy", f)]
levels = sorted([int(re.findall(r"gh_lev(\d+)\.npy", f)[0]) for f in gh_files])

# Prepare data dictionary
flat_data = {
    "latitude": lats[mask],
    "longitude": lons[mask],
}

# Add gh for each available level
for level in levels:
    arr_path = os.path.join(OUTPUT_FOLDER, f"gh_lev{level}.npy")
    col_name = f"gh[gpm]_lev{level}"
    if os.path.exists(arr_path):
        flat_data[col_name] = np.load(arr_path)[mask]
    else:
        print(f"Warning: gh_lev{level}.npy not found, filling with NaN.")
        flat_data[col_name] = np.full(flat_data["latitude"].shape, np.nan)

# Create DataFrame and save as CSV
df = pd.DataFrame(flat_data)
df = df.round(3)
csv_path = os.path.join(OUTPUT_FOLDER, "fort_worth_gh_levels.csv")
df.to_csv(csv_path, index=False)
print(f"CSV file saved to {csv_path}") 