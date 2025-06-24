import xarray as xr
import numpy as np
import os

OPENFOAM_NC = "NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc"
HRRR_NC = "NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc"

def print_stats(label, arr):
    print(f"  {label}: min={np.nanmin(arr):.4f}, max={np.nanmax(arr):.4f}, mean={np.nanmean(arr):.4f}")

def rmse(a, b):
    mask = ~np.isnan(a) & ~np.isnan(b)
    if np.any(mask):
        return np.sqrt(np.nanmean((a[mask] - b[mask])**2))
    else:
        return np.nan

def extract_origin_from_global_attrs(ds):
    if 'origin for x,y meters' in ds.attrs:
        origin = ds.attrs['origin for x,y meters']
        if isinstance(origin, str):
            # Try to parse string format like "[ 33.0265 -97.2725]"
            try:
                lat, lon = map(float, origin.strip('[]').split())
                return lat, lon
            except:
                print("  Warning: Could not parse origin string:", origin)
        elif isinstance(origin, (list, np.ndarray)):
            return origin[0], origin[1]
    return None, None

def print_origin_info(ds, group):
    """Print both global and variable-level origin information"""
    # Check global attributes
    lat_origin, lon_origin = extract_origin_from_global_attrs(ds)
    if lat_origin is not None:
        print(f"  Global origin: lat={lat_origin:.6f}, lon={lon_origin:.6f}")
    else:
        print("  Global origin attributes not found")
    
    # Check variable attributes
    for var_prefix in ['x_from_origin', 'y_from_origin']:
        var_name = f"{var_prefix}_{group}"
        if var_name in ds:
            attrs = ds[var_name].attrs
            if 'lat_origin' in attrs and 'lon_origin' in attrs:
                print(f"  {var_prefix} origin: lat={attrs['lat_origin']:.6f}, lon={attrs['lon_origin']:.6f}")
            else:
                print(f"  {var_prefix} origin attributes not found")

if not (os.path.exists(OPENFOAM_NC) and os.path.exists(HRRR_NC)):
    print("One or both NetCDF files not found.")
    exit(1)

of = xr.open_dataset(OPENFOAM_NC)
hrrr = xr.open_dataset(HRRR_NC)

print("=== Origin Information Comparison ===")
print("\nOpenFOAM Origin Information:")
of_lat, of_lon = extract_origin_from_global_attrs(of)
if of_lat is not None:
    print(f"  Global: lat={of_lat:.6f}, lon={of_lon:.6f}")
else:
    print("  Global origin not found")

print("\nHRRR Origin Information:")
hrrr_lat, hrrr_lon = extract_origin_from_global_attrs(hrrr)
if hrrr_lat is not None:
    print(f"  Global: lat={hrrr_lat:.6f}, lon={hrrr_lon:.6f}")
else:
    print("  Global origin not found")

if of_lat is not None and hrrr_lat is not None:
    lat_diff = abs(of_lat - hrrr_lat)
    lon_diff = abs(of_lon - hrrr_lon)
    print(f"\nGlobal Origin Difference:")
    print(f"  lat_diff={lat_diff:.6f}, lon_diff={lon_diff:.6f}")

print("\n=== Group-level Comparison ===")
groups = ['low', 'mid', 'high']
for group in groups:
    print(f"\n=== {group.upper()} LEVELS ===")
    
    print("\nOpenFOAM:")
    print_origin_info(of, group)
    
    print("\nHRRR-regrid:")
    print_origin_info(hrrr, group)
    
    for var in ['u', 'v', 'w']:
        of_var = f"{var}_{group}"
        hrrr_var = f"{var}_{group}"
        if of_var in of and hrrr_var in hrrr:
            print(f"\n{of_var}:")
            print_stats("OpenFOAM", of[of_var].values)
            print_stats("HRRR-regrid", hrrr[hrrr_var].values)
            if of[of_var].shape == hrrr[hrrr_var].shape:
                rmse_val = rmse(of[of_var].values, hrrr[hrrr_var].values)
                print(f"  RMSE: {rmse_val:.4f}")
            else:
                print(f"  Shapes differ: OpenFOAM {of[of_var].shape}, HRRR {hrrr[hrrr_var].shape}")
        else:
            print(f"  Variable {of_var} or {hrrr_var} not found in datasets.")
    
    for var in ['x_from_origin', 'y_from_origin']:
        of_var = f"{var}_{group}"
        hrrr_var = f"{var}_{group}"
        if of_var in of and hrrr_var in hrrr:
            print(f"\n{of_var}:")
            print_stats("OpenFOAM", of[of_var].values)
            print_stats("HRRR-regrid", hrrr[hrrr_var].values)
            if of[of_var].shape == hrrr[hrrr_var].shape:
                rmse_val = rmse(of[of_var].values, hrrr[hrrr_var].values)
                print(f"  RMSE: {rmse_val:.4f}")
            else:
                print(f"  Shapes differ: OpenFOAM {of[of_var].shape}, HRRR {hrrr[hrrr_var].shape}")
        else:
            print(f"  Variable {of_var} or {hrrr_var} not found in datasets.")

of.close()
hrrr.close() 