import os
import shutil
from herbie import Herbie
from datetime import datetime
import requests

# --- User input section ---
# Set the cycle datetime and forecast hour here
cycle_datetime_str = "2023-02-14T15:00:00"  # ISO format
forecast_hour = 2  # e.g., 2 for f02

# Parse the datetime
cycle_datetime = datetime.fromisoformat(cycle_datetime_str)

# Output directory
data_folder = os.path.join(os.getcwd(), "HRRRdata_nat_single")
os.makedirs(data_folder, exist_ok=True)

# Download HRRR native file for the given cycle and forecast hour
try:
    print(f"Downloading HRRR native data for cycle {cycle_datetime} hour f{forecast_hour:02d}")
    H = Herbie(
        cycle_datetime,
        model="hrrr",
        product="nat",
        fxx=forecast_hour,
        save_dir=os.path.join(data_folder, "temp"),
        verbose=True,
    )
    grib_path = H.download()
    if grib_path is None or not os.path.exists(grib_path):
        raise Exception("GRIB file not downloaded or not found.")

    # Download .idx file using Herbie.idx URL
    idx_url = H.idx
    idx_path = str(grib_path) + ".idx"
    response = requests.get(idx_url)
    if response.status_code == 200:
        with open(idx_path, "wb") as f:
            f.write(response.content)
    else:
        print(f"\nWarning: Failed to fetch .idx file (HTTP {response.status_code})")
        idx_path = None

    # Move GRIB and IDX files to target directory
    final_grib_path = os.path.join(data_folder, os.path.basename(grib_path))
    shutil.move(grib_path, final_grib_path)
    if idx_path and os.path.exists(idx_path):
        final_idx_path = os.path.join(data_folder, os.path.basename(idx_path))
        shutil.move(idx_path, final_idx_path)
    print(f"Download complete. Files saved to {data_folder}")
except Exception as e:
    print(f"Error: {e}") 