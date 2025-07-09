import netCDF4 as nc

# Open the NetCDF file
nc_file = nc.Dataset('NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')

# Print the file structure
print("File structure:")
for var_name in nc_file.variables:
    var = nc_file.variables[var_name]
    print(f"Variable: {var_name}")
    print(f"  Dimensions: {var.dimensions}")
    print(f"  Shape: {var.shape}")
    print(f"  Data type: {var.dtype}")
    print(f"  Attributes: {var.ncattrs()}")
    print(f"  Attributes: {var.ncattrs()}")

print(nc_file.file_format)