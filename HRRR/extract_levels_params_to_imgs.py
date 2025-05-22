import pygrib
import numpy as np
import os
import pandas as pd
from PIL import Image
import json

# File paths
DATA_FOLDER = "HRRRdata_nat"
GRIB_FILE = "hrrr.t14z.wrfnatf02.grib2"
GRIB_PATH = os.path.join(DATA_FOLDER, GRIB_FILE)

# Parameters of interest
PARAMS = {
    "pres": "Pressure",
    "gh": "Geopotential height",
    "t": "Temperature",
    "u": "U component of wind",
    "v": "V component of wind",
    "w": "Vertical velocity"
}

# Fort Worth bounding box (lon_min, lat_min, lon_max, lat_max)
FORT_WORTH_BBOX = (-97.648, 32.742, -96.898, 33.231)

# Output folder for images
OUTPUT_FOLDER = os.path.join(DATA_FOLDER, "levels_extracted_img_encoded")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Define units for each parameter
PARAM_UNITS = {
    "pres": "Pa",
    "gh": "gpm",
    "t": "K",
    "u": "m/s",
    "v": "m/s",
    "w": "Pa/s"
}

# Open the GRIB2 file and extract arrays for all available levels
lats = lons = None
levels_params = {}
with pygrib.open(GRIB_PATH) as grbs:
    latlons_saved = False
    for grb in grbs:
        if grb.shortName in PARAMS:
            level = grb.level
            if level not in levels_params:
                levels_params[level] = {}
            levels_params[level][grb.shortName] = grb.values
            if not latlons_saved:
                lats, lons = grb.latlons()
                latlons_saved = True

# Only keep levels with all parameters
valid_levels = [level for level, params in levels_params.items() if all(p in params for p in PARAMS)]
print(f"Valid levels with all parameters: {sorted(valid_levels)}")

# Create mask for Fort Worth bounding box
lon_min, lat_min, lon_max, lat_max = FORT_WORTH_BBOX
mask = (
    (lons >= lon_min) & (lons <= lon_max) &
    (lats >= lat_min) & (lats <= lat_max)
)

# Get the shape of the mask
mask_indices = np.where(mask)
lat_indices = np.unique(mask_indices[0])
lon_indices = np.unique(mask_indices[1])
num_lat = len(lat_indices)
num_lon = len(lon_indices)

# Get min/max lat/lon in the mask
min_lat = np.min(lats[mask])
max_lat = np.max(lats[mask])
min_lon = np.min(lons[mask])
max_lon = np.max(lons[mask])

for level in valid_levels:
    level_data = {}
    missing = False
    for short_name in PARAMS:
        arr = levels_params[level][short_name]
        if hasattr(arr, 'filled'):
            arr = arr.filled(np.nan)
        arr_masked = arr[mask]
        level_data[short_name] = arr_masked
    if missing:
        continue
    # Calculate geometric vertical velocity w [m/s]
    R_d = 287.05  # J/kg·K
    g = 9.81      # m/s²
    omega = level_data["w"]
    T = level_data["t"]
    p = level_data["pres"]
    w_geom = -(omega * R_d * T) / (p * g)
    u = level_data["u"]
    v = level_data["v"]
    gh = level_data["gh"]
    # Normalize u, v, w_geom, gh
    u_min, u_max = np.nanmin(u), np.nanmax(u)
    v_min, v_max = np.nanmin(v), np.nanmax(v)
    w_min, w_max = np.nanmin(w_geom), np.nanmax(w_geom)
    gh_min, gh_max = np.nanmin(gh), np.nanmax(gh)
    u_norm = (u - u_min) / (u_max - u_min) if u_max > u_min else np.zeros_like(u)
    v_norm = (v - v_min) / (v_max - v_min) if v_max > v_min else np.zeros_like(v)
    w_norm = (w_geom - w_min) / (w_max - w_min) if w_max > w_min else np.zeros_like(w_geom)
    gh_norm = (gh - gh_min) / (gh_max - gh_min) if gh_max > gh_min else np.zeros_like(gh)
    # Prepare RGBA image array
    img_array = np.full((num_lat, num_lon, 4), 255, dtype=np.uint8)  # Default to missing
    # Fill RGBA channels
    missing_pixel_count = 0
    for idx, (i, j) in enumerate(zip(mask_indices[0], mask_indices[1])):
        lat_idx = np.where(lat_indices == i)[0][0]
        lon_idx = np.where(lon_indices == j)[0][0]
        # Check for missing data
        if (
            np.isnan(u[idx]) or
            np.isnan(v[idx]) or
            np.isnan(w_geom[idx]) or
            np.isnan(gh[idx])
        ):
            print(f"Missing data at (lat_idx={lat_idx}, lon_idx={lon_idx}): u={u[idx]}, v={v[idx]}, w_geom={w_geom[idx]}, gh={gh[idx]}")
            # Already set to 255,255,255,255
            missing_pixel_count += 1
        else:
            img_array[lat_idx, lon_idx, 0] = int(np.clip(u_norm[idx] * 255, 0, 255))
            img_array[lat_idx, lon_idx, 1] = int(np.clip(v_norm[idx] * 255, 0, 255))
            img_array[lat_idx, lon_idx, 2] = int(np.clip(w_norm[idx] * 255, 0, 255))
            # Encode gh_norm in [1, 254]
            alpha = int(1 + gh_norm[idx] * 253)
            img_array[lat_idx, lon_idx, 3] = np.clip(alpha, 1, 254)
    # Save image
    img = Image.fromarray(img_array, mode='RGBA')
    img_path = os.path.join(OUTPUT_FOLDER, f"fort_worth_level{level}_img.png")
    img.save(img_path)
    print(f"Saved RGBA image for level {level} to {img_path}")
    print(f"Missing/encoded pixels for level {level}: {missing_pixel_count} out of {num_lat * num_lon}")
    # Save meta file
    meta = {
        "level": int(level),
        "u_min": float(u_min), "u_max": float(u_max),
        "v_min": float(v_min), "v_max": float(v_max),
        "w_min": float(w_min), "w_max": float(w_max),
        "gh_min": float(gh_min), "gh_max": float(gh_max),
        "min_lat": float(min_lat), "max_lat": float(max_lat),
        "min_lon": float(min_lon), "max_lon": float(max_lon),
        "num_lat": int(num_lat), "num_lon": int(num_lon)
    }
    meta_path = os.path.join(OUTPUT_FOLDER, f"fort_worth_level{level}_meta.json")
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Saved meta file for level {level} to {meta_path}") 