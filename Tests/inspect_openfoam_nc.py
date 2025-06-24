import xarray as xr
import sys
import os

# Path to the OpenFOAM NetCDF file
OPENFOAM_NC = "NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc"

if not os.path.exists(OPENFOAM_NC):
    print(f"File not found: {OPENFOAM_NC}")
    sys.exit(1)

# Open the NetCDF file
print(f"Opening: {OPENFOAM_NC}")
ds = xr.open_dataset(OPENFOAM_NC)

# Print global attributes
print("\nGlobal attributes:")
for k, v in ds.attrs.items():
    print(f"  {k}: {v}")

# Print dimensions
print("\nDimensions:")
for dim, size in ds.dims.items():
    print(f"  {dim}: {size}")

# Print variable names and shapes
print("\nVariables:")
for var in ds.variables:
    print(f"  {var}: {ds[var].shape}, dtype={ds[var].dtype}")

# Print a summary of each variable (min, max, mean for numeric arrays)
print("\nVariable summaries:")
for var in ds.variables:
    arr = ds[var]
    if hasattr(arr, 'values') and hasattr(arr.values, 'dtype') and arr.values.dtype.kind in 'fi':
        vals = arr.values
        print(f"  {var}: min={vals.min():.4f}, max={vals.max():.4f}, mean={vals.mean():.4f}")
    else:
        print(f"  {var}: non-numeric or not summarized")

ds.close() 