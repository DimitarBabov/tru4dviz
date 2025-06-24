import xarray as xr
import numpy as np

OPENFOAM_NC = "NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc"

# Open the dataset
ds = xr.open_dataset(OPENFOAM_NC)

# Print global attributes
print("=== Global Attributes ===")
for attr in ds.attrs:
    print(f"{attr}: {ds.attrs[attr]}")

# Print variables and their attributes
print("\n=== Variables and Attributes ===")
for var in ds.variables:
    print(f"\n{var}:")
    print("  Attributes:")
    for attr in ds[var].attrs:
        print(f"    {attr}: {ds[var].attrs[attr]}")
    print("  Shape:", ds[var].shape)
    if ds[var].size < 10:  # Print small arrays fully
        print("  Values:", ds[var].values)

ds.close() 