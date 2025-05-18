import os
import shutil
import requests
from herbie import Herbie
from datetime import datetime, timedelta, UTC
import concurrent.futures
from tqdm import tqdm

def download_forecast_hour(args):
    forecast_datetime_aware, hour, data_folder = args
    forecast_hour = f"f{hour:02d}"

    try:
        # Convert to tz-naive (Herbie expects naive datetime in UTC)
        forecast_datetime_naive = forecast_datetime_aware.replace(tzinfo=None)

        # Create Herbie instance
        H = Herbie(
            forecast_datetime_naive,
            model="hrrr",
            product="nat",  # This is for wrfnat files
            fxx=hour,
            save_dir=os.path.join(data_folder, "temp"),
            verbose=False,
        )

        # Download GRIB2 file
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
            print(f"\nWarning: Failed to fetch .idx file for {forecast_hour} (HTTP {response.status_code})")
            idx_path = None

        # Move GRIB and IDX files to target directory
        final_grib_path = os.path.join(data_folder, os.path.basename(grib_path))
        shutil.move(grib_path, final_grib_path)

        if idx_path and os.path.exists(idx_path):
            final_idx_path = os.path.join(data_folder, os.path.basename(idx_path))
            shutil.move(idx_path, final_idx_path)

        return True

    except Exception as e:
        print(f"\nError processing {forecast_hour}: {e}")
        return False

# --- Setup section ---

# Time setup
current_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
forecast_datetime = current_time - timedelta(hours=24)
print(f"Using forecast date: {forecast_datetime:%Y-%m-%d %H:%M}")

# Output directory
data_folder = os.path.join(os.getcwd(), "HRRRdata_nat")  # Different folder for nat files
os.makedirs(data_folder, exist_ok=True)
print(f"Saving data to: {data_folder}")

# Forecast hours to download
forecast_hours = range(2, 8)  # f02 to f07
download_args = [(forecast_datetime, hour, data_folder) for hour in forecast_hours]

# --- Download in parallel ---
print("Starting parallel downloads...")
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = list(tqdm(
        executor.map(download_forecast_hour, download_args),
        total=len(download_args),
        desc="Downloading HRRR native data"
    ))

# Summary
successful_downloads = sum(results)
print(f"\nDownload Summary:")
print(f"Successfully downloaded: {successful_downloads}/{len(forecast_hours)} forecast hours")
if successful_downloads < len(forecast_hours):
    print("Some downloads failed. See messages above.") 