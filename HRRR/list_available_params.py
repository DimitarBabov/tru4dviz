import os
import pygrib

# Define the path to the GRIB2 file
data_folder = "HRRRdata"  # Folder where the GRIB2 file is stored
grib_file_name = "hrrr.t12z.wrfsfcf00.grib2"  # Replace with your GRIB2 file name
grib_file_path = os.path.join(data_folder, grib_file_name)

# Check if the GRIB2 file exists
if not os.path.exists(grib_file_path):
    raise FileNotFoundError(f"GRIB2 file not found: {grib_file_path}")

print(f"Reading GRIB2 file: {grib_file_path}")

# Open the GRIB2 file using pygrib
try:
    grbs = pygrib.open(grib_file_path)
    
    print("\n### List of Parameters in the GRIB2 File ###")
    for grb in grbs:
        print(f"Message {grb.messagenumber}: {grb.shortName} ({grb.name}) - {grb.typeOfLevel} at {grb.level}")

    print("\n### Key Information ###")
    print("Each message contains:")
    print("- Parameter name and description")
    print("- Level type and value (e.g., surface, 2 m above ground)")
    print("- Forecast time")

    grbs.close()

except Exception as e:
    print(f"An error occurred while reading the GRIB2 file: {e}")
