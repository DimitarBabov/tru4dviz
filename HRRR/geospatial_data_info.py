import pygrib

# Path to your GRIB2 file
grib_file_path = "HRRRdata/hrrr.t12z.wrfsfcf00.grib2"  # Replace with your file path

# Open the GRIB2 file
grbs = pygrib.open(grib_file_path)

# Print grid projection details for the first message
grb = grbs.message(1)  # Read the first message
print("\n### Grid Projection Details ###")
print(f"Grid Type: {grb.gridType}")
print(f"Grid Description: {grb.gridDefinitionDescription}")
print(f"Projection Parameters: {grb.projparams}")
print(f"Latitude of Origin: {grb.latitudeOfFirstGridPointInDegrees}")
print(f"Longitude of Origin: {grb.longitudeOfFirstGridPointInDegrees}")
print(f"Shape of Grid: {grb.Ni} x {grb.Nj}")
print(f"Resolution: {grb.Dx}m x {grb.Dy}m")  # Grid spacing in meters

# Get latitude and longitude arrays for the grid
lats, lons = grb.latlons()

# Calculate min/max latitude and longitude
min_lat = lats.min()
max_lat = lats.max()
min_lon = lons.min()
max_lon = lons.max()

# Print min/max latitude and longitude
print("\n### Latitude and Longitude Range ###")
print(f"Min Latitude: {min_lat}, Max Latitude: {max_lat}")
print(f"Min Longitude: {min_lon}, Max Longitude: {max_lon}")

grbs.close()
