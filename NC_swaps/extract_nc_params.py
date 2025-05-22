import netCDF4 as nc
import os
import pathlib

# File path
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
NC_PATH = os.path.join(SCRIPT_DIR, '../NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')
OUTPUT_TXT = os.path.join(SCRIPT_DIR, 'nc_params.txt')

with nc.Dataset(NC_PATH) as ds, open(OUTPUT_TXT, 'w') as f:
    f.write(f"Variables in {NC_PATH}:\n")
    for var_name in ds.variables:
        var = ds.variables[var_name]
        f.write(f"{var_name}: shape={var.shape}, dtype={var.dtype}, dimensions={var.dimensions}\n")
    f.write("\nGlobal attributes:\n")
    for attr in ds.ncattrs():
        f.write(f"{attr}: {getattr(ds, attr)}\n") 