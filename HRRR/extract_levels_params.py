import pygrib
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.table as tbl

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

# Output folder for numpy arrays
OUTPUT_FOLDER = os.path.join(DATA_FOLDER, "levels_extracted")
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
            # Save lat/lon arrays from the first found parameter
            if not latlons_saved:
                lats, lons = grb.latlons()
                np.save(os.path.join(OUTPUT_FOLDER, "latitudes.npy"), lats)
                np.save(os.path.join(OUTPUT_FOLDER, "longitudes.npy"), lons)
                latlons_saved = True

# Only keep levels with all parameters
valid_levels = [level for level, params in levels_params.items() if all(p in params for p in PARAMS)]
print(f"Valid levels with all parameters: {sorted(valid_levels)}")

# Save .npy files for valid levels only
for level in valid_levels:
    for short_name in PARAMS:
        arr = levels_params[level][short_name]
        if hasattr(arr, 'filled'):
            arr = arr.filled(np.nan)
        np.save(os.path.join(OUTPUT_FOLDER, f"{short_name}_lev{level}.npy"), arr)
        print(f"  Saved {short_name}_lev{level}.npy, shape: {arr.shape}, min: {np.nanmin(arr)}, max: {np.nanmax(arr)}")

print(f"Extraction complete. Arrays saved in {OUTPUT_FOLDER}")

# Load arrays
if lats is None or lons is None:
    lats = np.load(os.path.join(OUTPUT_FOLDER, "latitudes.npy"))
    lons = np.load(os.path.join(OUTPUT_FOLDER, "longitudes.npy"))

# Create mask for Fort Worth bounding box
lon_min, lat_min, lon_max, lat_max = FORT_WORTH_BBOX
mask = (
    (lons >= lon_min) & (lons <= lon_max) &
    (lats >= lat_min) & (lats <= lat_max)
)

# Create separate CSVs for each valid level
all_w = []
all_u = []
all_v = []
level_stats = []
for level in valid_levels:
    level_flat_data = {
        "latitude": lats[mask],
        "longitude": lons[mask],
    }
    missing = False
    for short_name in PARAMS:
        arr_path = os.path.join(OUTPUT_FOLDER, f"{short_name}_lev{level}.npy")
        col_name = f"{short_name}[{PARAM_UNITS[short_name]}]"
        if os.path.exists(arr_path):
            level_flat_data[col_name] = np.load(arr_path)[mask]
        else:
            print(f"Warning: {short_name}_lev{level}.npy not found, skipping level {level}.")
            missing = True
            break
    if missing:
        continue
    df_level = pd.DataFrame(level_flat_data)
    # Calculate geometric vertical velocity w [m/s]
    # w = -(omega * R_d * T) / (p * g)
    R_d = 287.05  # J/kg·K
    g = 9.81      # m/s²
    omega = df_level[f"w[Pa/s]"]
    T = df_level[f"t[K]"]
    p = df_level[f"pres[Pa]"]
    w_geom = -(omega * R_d * T) / (p * g)
    # Rename 'w[Pa/s]' to 'omega[Pa/s]' and add 'w[m/s]'
    df_level = df_level.rename(columns={f"w[Pa/s]": "omega[Pa/s]"})
    df_level["w[m/s]"] = w_geom.round(3)
    # Remove pressure, temperature, and omega columns from output
    df_level = df_level.drop(columns=[f"pres[Pa]", f"t[K]", "omega[Pa/s]"])
    df_level = df_level.round(3)
    # Print statistics for this level
    w_min, w_max = np.nanmin(w_geom), np.nanmax(w_geom)
    u_min, u_max = np.nanmin(df_level["u[m/s]"]), np.nanmax(df_level["u[m/s]"])
    v_min, v_max = np.nanmin(df_level["v[m/s]"]), np.nanmax(df_level["v[m/s]"])
    print(f"Level {level}: w[m/s] min={w_min:.3f}, max={w_max:.3f}; u[m/s] min={u_min:.3f}, max={u_max:.3f}; v[m/s] min={v_min:.3f}, max={v_max:.3f}")
    all_w.append(w_geom)
    all_u.append(df_level["u[m/s]"])
    all_v.append(df_level["v[m/s]"])
    level_stats.append([level, w_min, w_max, u_min, u_max, v_min, v_max])
    csv_path = os.path.join(OUTPUT_FOLDER, f"fort_worth_level{level}_params.csv")
    df_level.to_csv(csv_path, index=False)
    print(f"CSV file saved to {csv_path}")

# Print overall statistics
if all_w:
    all_w_flat = np.concatenate(all_w)
    all_u_flat = np.concatenate(all_u)
    all_v_flat = np.concatenate(all_v)
    print(f"\nOverall: w[m/s] min={np.nanmin(all_w_flat):.3f}, max={np.nanmax(all_w_flat):.3f}")
    print(f"Overall: u[m/s] min={np.nanmin(all_u_flat):.3f}, max={np.nanmax(all_u_flat):.3f}")
    print(f"Overall: v[m/s] min={np.nanmin(all_v_flat):.3f}, max={np.nanmax(all_v_flat):.3f}")
    # Plot distributions
    plt.figure(figsize=(12,8))
    plt.hist(all_w_flat, bins=100, alpha=0.5, label='w [m/s]')
    plt.hist(all_u_flat, bins=100, alpha=0.5, label='u [m/s]')
    plt.hist(all_v_flat, bins=100, alpha=0.5, label='v [m/s]')
    plt.xlabel('Value')
    plt.ylabel('Count')
    plt.title('Distribution of w, u, v for all levels (Fort Worth)')
    plt.legend()
    # Add min/max table for each level (skip every other level for readability)
    col_labels = ['Level', 'w_min', 'w_max', 'u_min', 'u_max', 'v_min', 'v_max']
    table_vals = [[str(lv), f"{wmin:.2f}", f"{wmax:.2f}", f"{umin:.2f}", f"{umax:.2f}", f"{vmin:.2f}", f"{vmax:.2f}"]
                  for i, (lv, wmin, wmax, umin, umax, vmin, vmax) in enumerate(level_stats) if i % 2 == 0]
    the_table = plt.table(cellText=table_vals, colLabels=col_labels, loc='bottom', cellLoc='center', bbox=[0.0, -1.2, 1, 1.1])
    plt.subplots_adjust(left=0.1, bottom=0.55)
    plt.tight_layout()
    plt.savefig('w_u_v_stats.png', bbox_inches='tight')
    print(f"Distribution plot saved to w_u_v_stats.png") 