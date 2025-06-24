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

if not (os.path.exists(OPENFOAM_NC) and os.path.exists(HRRR_NC)):
    print("One or both NetCDF files not found.")
    exit(1)

of = xr.open_dataset(OPENFOAM_NC)
hrrr = xr.open_dataset(HRRR_NC)

groups = ['low', 'mid', 'high']
for group in groups:
    print(f"\n=== {group.upper()} LEVELS ===")
    for var in ['u', 'v', 'w']:
        of_var = f"{var}_{group}"
        hrrr_var = f"{var}_{group}"
        if of_var in of and hrrr_var in hrrr:
            print(f"\n{of_var}:")
            print_stats("OpenFOAM", of[of_var].values)
            print_stats("HRRR-regrid", hrrr[hrrr_var].values)
            # Try to compute RMSE for overlapping grid (if shapes match)
            if of[of_var].shape == hrrr[hrrr_var].shape:
                rmse_val = rmse(of[of_var].values, hrrr[hrrr_var].values)
                print(f"  RMSE: {rmse_val:.4f}")
            else:
                print(f"  Shapes differ: OpenFOAM {of[of_var].shape}, HRRR {hrrr[hrrr_var].shape}")
        else:
            print(f"  Variable {of_var} or {hrrr_var} not found in datasets.")

of.close()
hrrr.close() 