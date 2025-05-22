import netCDF4 as nc
import numpy as np
import pandas as pd
import os
import pathlib

# File paths
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
NC_PATH = os.path.join(SCRIPT_DIR, '../NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')
OUTPUT_CSV = os.path.join(SCRIPT_DIR, 'middle_layers_grid.csv')

# Open the NetCDF file
with nc.Dataset(NC_PATH) as ds:
    # Extract middle layer dimensions
    lat = ds.variables['latitude_mid'][:]
    lon = ds.variables['longitude_mid'][:]
    alt = ds.variables['altitude_mid'][:]
    # Extract parameter variables (3D)
    u = ds.variables['u_mid'][:]
    v = ds.variables['v_mid'][:]
    w = ds.variables['w_mid'][:]
    tke = ds.variables['tke_mid'][:]
    # Extract 2D grid variables
    x_from_origin = ds.variables['x_from_origin_mid'][:]
    y_from_origin = ds.variables['y_from_origin_mid'][:]
    # Prepare data rows
    rows = []
    for k, a in enumerate(alt):
        for i, la in enumerate(lat):
            for j, lo in enumerate(lon):
                row = {
                    'altitude': float(a),
                    'latitude': float(la),
                    'longitude': float(lo),
                    'x_from_origin_mid': float(x_from_origin[i, j]),
                    'y_from_origin_mid': float(y_from_origin[i, j]),
                    'u_mid': float(u[k, i, j]),
                    'v_mid': float(v[k, i, j]),
                    'w_mid': float(w[k, i, j]),
                    'tke_mid': float(tke[k, i, j])
                }
                rows.append(row)
    # Create DataFrame and save
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved middle layer grid with parameters to {OUTPUT_CSV}") 