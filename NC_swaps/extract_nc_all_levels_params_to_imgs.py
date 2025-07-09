import netCDF4 as nc
import numpy as np
import os
from PIL import Image
import json

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define both NetCDF files to process - both have the same structure
NC_FILES = [
    {
        'name': 'openfoam',
        'output_prefix': 'cfd',
        'path': os.path.join(SCRIPT_DIR, '../NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')
    },
    {
        'name': 'hrrr', 
        'output_prefix': 'hrrr',
        'path': os.path.join(SCRIPT_DIR, '../NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc')
    },
    {
        'name': 'difference',
        'output_prefix': 'diff-cfd-hrrr',
        'path': os.path.join(SCRIPT_DIR, '../NCdata/diff_cfd_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')
    }
]

# Both files have the same level structure
LEVEL_GROUPS = [
    ('low', 'u_low', 'v_low', 'w_low', 'altitude_low', 'latitude_low', 'longitude_low'),
    ('mid', 'u_mid', 'v_mid', 'w_mid', 'altitude_mid', 'latitude_mid', 'longitude_mid'),
    ('high', 'u_high', 'v_high', 'w_high', 'altitude_high', 'latitude_high', 'longitude_high'),
]

def process_nc_file(file_config):
    """Process a single NetCDF file"""
    nc_path = file_config['path']
    file_name = file_config['name']
    output_prefix = file_config['output_prefix']
    
    print(f"\n=== Processing {file_name.upper()} file ===")
    print(f"File: {nc_path}")
    
    if not os.path.exists(nc_path):
        print(f"Warning: File not found: {nc_path}")
        return
    
    with nc.Dataset(nc_path) as ds:
        print(f"Variables in {file_name}: {list(ds.variables.keys())}")
        
        # Get lat_origin and lon_origin from global attributes if available
        lat_origin = None
        lon_origin = None
        if hasattr(ds, 'origin for x,y meters'):
            origin = getattr(ds, 'origin for x,y meters')
            if isinstance(origin, str):
                # Parse string like '[ 33.0265 -97.2725]'
                import re
                nums = re.findall(r'[-+]?\d*\.\d+|\d+', origin)
                if len(nums) >= 2:
                    lat_origin = float(nums[0])
                    lon_origin = float(nums[1])
            elif hasattr(origin, '__len__') and len(origin) >= 2:
                lat_origin = float(origin[0])
                lon_origin = float(origin[1])
        
        # Process each level group
        for group, u_name, v_name, w_name, alt_name, lat_name, lon_name in LEVEL_GROUPS:
            print(f"\nProcessing {file_name} - {group} group...")
            
            # Check if all required variables exist
            required_vars = [u_name, v_name, w_name, lat_name, lon_name, alt_name]
            missing_vars = [var for var in required_vars if var not in ds.variables]
            if missing_vars:
                print(f"  Skipping {group}: Missing variables {missing_vars}")
                continue
            
            # Create output folder with new naming scheme
            OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, f'{group}_levels_img_encoded_{output_prefix}')
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            
            # Get all variables inside the with block
            lat = ds.variables[lat_name][:]
            lon = ds.variables[lon_name][:]
            u = ds.variables[u_name][:]
            v = ds.variables[v_name][:]
            w = ds.variables[w_name][:]
            alt = ds.variables[alt_name][:]
            
            # Handle x_from_origin and y_from_origin
            x_name = f"x_from_origin_{group}"
            y_name = f"y_from_origin_{group}"
            if x_name in ds.variables and y_name in ds.variables:
                x_from_origin = ds.variables[x_name][:]
                y_from_origin = ds.variables[y_name][:]
            else:
                # Generate from lat/lon if not available
                x_from_origin = None
                y_from_origin = None
            
            # Get bounding box
            min_lat, max_lat = float(np.min(lat)), float(np.max(lat))
            min_lon, max_lon = float(np.min(lon)), float(np.max(lon))
            alt_min = float(np.min(alt))
            alt_max = float(np.max(alt))
            num_lat = len(lat) if lat.ndim == 1 else lat.shape[0]
            num_lon = len(lon) if lon.ndim == 1 else lon.shape[1]
            
            print(f"  Grid: {num_lat} x {num_lon}")
            print(f"  Lat range: {min_lat:.6f} to {max_lat:.6f}")
            print(f"  Lon range: {min_lon:.6f} to {max_lon:.6f}")
            print(f"  Levels: {len(alt)}")
            
            # Process each level
            for k, a in enumerate(alt):
                print(f"    Processing level {k} (altitude: {a})...")
                
                # Extract data for this level (3D: level, lat, lon)
                u_k = u[k] if hasattr(u[k], 'filled') else u[k]
                v_k = v[k] if hasattr(v[k], 'filled') else v[k]
                w_k = w[k] if hasattr(w[k], 'filled') else w[k]
                
                # Handle masked arrays
                if hasattr(u_k, 'filled'):
                    u_k = u_k.filled(np.nan)
                if hasattr(v_k, 'filled'):
                    v_k = v_k.filled(np.nan)
                if hasattr(w_k, 'filled'):
                    w_k = w_k.filled(np.nan)
                
                # Normalize per level
                u_min, u_max = np.nanmin(u_k), np.nanmax(u_k)
                v_min, v_max = np.nanmin(v_k), np.nanmax(v_k)
                w_min, w_max = np.nanmin(w_k), np.nanmax(w_k)
                alt_val = float(a)
                
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
                print(f"    Saved: {img_path}")
                print(f"    Missing pixels: {missing_pixel_count}/{num_lat * num_lon}")
                
                # Compute min/max x_from_origin and y_from_origin
                if x_from_origin is not None and y_from_origin is not None:
                    min_x_from_origin = float(np.nanmin(x_from_origin))
                    max_x_from_origin = float(np.nanmax(x_from_origin))
                    min_y_from_origin = float(np.nanmin(y_from_origin))
                    max_y_from_origin = float(np.nanmax(y_from_origin))
                else:
                    # Use lat/lon as fallback
                    min_x_from_origin = min_lon
                    max_x_from_origin = max_lon
                    min_y_from_origin = min_lat
                    max_y_from_origin = max_lat
                
                meta = {
                    #"source": file_name,
                    "group": group,
                    "level_index": int(k),
                    "altitude": float(alt_val),
                    "u_min": float(u_min), "u_max": float(u_max),
                    "v_min": float(v_min), "v_max": float(v_max),
                    "w_min": float(w_min), "w_max": float(w_max),
                    "alt_min": float(alt_min), "alt_max": float(alt_max),
                    "min_lat": float(min_lat), "max_lat": float(max_lat),
                    "min_lon": float(min_lon), "max_lon": float(max_lon),
                    "num_lat": int(num_lat), "num_lon": int(num_lon),
                    "debug_scale": 1,
                    "min_x_from_origin": min_x_from_origin,
                    "max_x_from_origin": max_x_from_origin,
                    "min_y_from_origin": min_y_from_origin,
                    "max_y_from_origin": max_y_from_origin,
                    "lat_origin": lat_origin,
                    "lon_origin": lon_origin
                }
                
                meta_path = os.path.join(OUTPUT_FOLDER, f"{group}_level{k}_meta.json")
                with open(meta_path, 'w') as f:
                    json.dump(meta, f, indent=2)
                print(f"    Saved metadata: {meta_path}")

# Process both files
for file_config in NC_FILES:
    process_nc_file(file_config)

print("\n=== Processing Complete ===")
print("Both OpenFOAM and HRRR data have been processed and encoded to images.")
print("Output folders:")
print("  - low_levels_img_encoded_cfd/")
print("  - mid_levels_img_encoded_cfd/")
print("  - high_levels_img_encoded_cfd/")
print("  - low_levels_img_encoded_hrrr/")
print("  - mid_levels_img_encoded_hrrr/")
print("  - high_levels_img_encoded_hrrr/")
print("  - low_levels_img_encoded_diff-cfd-hrrr/")
print("  - mid_levels_img_encoded_diff-cfd-hrrr/")
print("  - high_levels_img_encoded_diff-cfd-hrrr/") 