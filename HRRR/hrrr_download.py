import os
import shutil  # To move the downloaded file
from herbie import Herbie

# Define the forecast start datetime and HRRR model parameters
forecast_date = "2025-01-06 12:00"  # Example date and time
model = "hrrr"
product = "sfc"  # Surface fields
forecast_hours = range(0, 19)  # Forecast hours from f00 to f18

# Define the desired folder for storing the data
current_dir = os.getcwd()  # Get the current working directory
data_folder = os.path.join(current_dir, "HRRRdata")  # Desired folder
if not os.path.exists(data_folder):
    os.makedirs(data_folder)
    print(f"Created folder: {data_folder}")
else:
    print(f"Using existing folder: {data_folder}")

# Loop through each forecast hour and download data
for hour in forecast_hours:
    forecast_hour = f"f{hour:02d}"  # Format as f00, f01, ..., f18
    print(f"Downloading HRRR data for {forecast_date}, forecast hour {forecast_hour}...")
    
    try:
        # Create a Herbie instance for the specific forecast hour
        H = Herbie(forecast_date, model=model, product=product, fxx=hour)

        # Download HRRR data to the default location (home directory)
        grib_file = H.download()  # The file will initially download to the default Herbie directory
        grib_file_path = str(grib_file)  # Ensure the path is a string
        print(f"File downloaded to: {grib_file_path}")

        # Move the downloaded file to the desired folder (HRRRdata)
        destination_file_path = os.path.join(data_folder, os.path.basename(grib_file_path))  # Construct destination path
        shutil.move(grib_file_path, destination_file_path)
        print(f"File moved to: {destination_file_path}")
    except Exception as e:
        print(f"Failed to download data for {forecast_hour}: {e}")

print("All requested HRRR forecast data downloaded successfully!")
