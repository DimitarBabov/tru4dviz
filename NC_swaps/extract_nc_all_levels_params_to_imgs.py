import netCDF4 as nc
import numpy as np
import os
from PIL import Image
import json

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NC_PATH = os.path.join(SCRIPT_DIR, '../NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')
LEVEL_GROUPS = [
    ('low', 'u_low', 'v_low', 'w_low', 'altitude_low', 'latitude_low', 'longitude_low'),
    ('mid', 'u_mid', 'v_mid', 'w_mid', 'altitude_mid', 'latitude_mid', 'longitude_mid'),
    ('high', 'u_high', 'v_high', 'w_high', 'altitude_high', 'latitude_high', 'longitude_high'),
]

with nc.Dataset(NC_PATH) as ds:
    for group, u_name, v_name, w_name, alt_name, lat_name, lon_name in LEVEL_GROUPS:
        OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, f'{group}_levels_img_encoded')
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        lat = ds.variables[lat_name][:]
        lon = ds.variables[lon_name][:]
        alt = ds.variables[alt_name][:]
        u = ds.variables[u_name][:]
        v = ds.variables[v_name][:]
        w = ds.variables[w_name][:]
        # Get bounding box
        min_lat, max_lat = float(np.min(lat)), float(np.max(lat))
        min_lon, max_lon = float(np.min(lon)), float(np.max(lon))
        num_lat = len(lat)
        num_lon = len(lon)
        for k, a in enumerate(alt):
            u_k = u[k].filled(np.nan) if hasattr(u[k], 'filled') else u[k]
            v_k = v[k].filled(np.nan) if hasattr(v[k], 'filled') else v[k]
            w_k = w[k].filled(np.nan) if hasattr(w[k], 'filled') else w[k]
            u_min, u_max = np.nanmin(u_k), np.nanmax(u_k)
            v_min, v_max = np.nanmin(v_k), np.nanmax(v_k)
            w_min, w_max = np.nanmin(w_k), np.nanmax(w_k)
            alt_val = float(a)
            alt_min, alt_max = float(np.min(alt)), float(np.max(alt))
            u_norm = (u_k - u_min) / (u_max - u_min) if u_max > u_min else np.zeros_like(u_k)
            v_norm = (v_k - v_min) / (v_max - v_min) if v_max > v_min else np.zeros_like(v_k)
            w_norm = (w_k - w_min) / (w_max - w_min) if w_max > w_min else np.zeros_like(w_k)
            alt_norm = (alt_val - alt_min) / (alt_max - alt_min) if alt_max > alt_min else 0.0
            # Encode alt_norm in [1, 254]
            alpha = int(1 + alt_norm * 253)
            img_array = np.full((num_lat, num_lon, 4), 255, dtype=np.uint8)
            missing_pixel_count = 0
            for i in range(num_lat):
                for j in range(num_lon):
                    if (
                        np.isnan(u_k[i, j]) or
                        np.isnan(v_k[i, j]) or
                        np.isnan(w_k[i, j])
                    ):
                        missing_pixel_count += 1
                        continue
                    img_array[i, j, 0] = int(np.clip(u_norm[i, j] * 255, 0, 255))
                    img_array[i, j, 1] = int(np.clip(v_norm[i, j] * 255, 0, 255))
                    img_array[i, j, 2] = int(np.clip(w_norm[i, j] * 255, 0, 255))
                    img_array[i, j, 3] = np.clip(alpha, 1, 254)
            img = Image.fromarray(img_array, mode='RGBA')
            img_path = os.path.join(OUTPUT_FOLDER, f"{group}_level{k}_img.png")
            img.save(img_path)
            print(f"Saved RGBA image for {group} level {k} to {img_path}")
            print(f"Missing/encoded pixels for {group} level {k}: {missing_pixel_count} out of {num_lat * num_lon}")
            meta = {
                "group": group,
                "level_index": int(k),
                "altitude": float(alt_val),
                "u_min": float(u_min), "u_max": float(u_max),
                "v_min": float(v_min), "v_max": float(v_max),
                "w_min": float(w_min), "w_max": float(w_max),
                "alt_min": float(alt_min), "alt_max": float(alt_max),
                "min_lat": float(min_lat), "max_lat": float(max_lat),
                "min_lon": float(min_lon), "max_lon": float(max_lon),
                "num_lat": int(num_lat), "num_lon": int(num_lon)
            }
            meta_path = os.path.join(OUTPUT_FOLDER, f"{group}_level{k}_meta.json")
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)
            print(f"Saved meta file for {group} level {k} to {meta_path}") 