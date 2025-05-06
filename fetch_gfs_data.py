
import shutil
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pygrib
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


# Directory to store GFS data
#GFS_DIR = "/gfs_data"
#GFS_DIR = "/home/mko0/weatherapp/gfs_data"
GFS_DIR = "gfs_data"
PNG_DIR = "png_data"

def get_latest_gfs_run():
    """Fetch the latest GFS run date and time."""
    base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/'
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the latest available YYYYMMDD directory
    latest_date_dir = None
    for link in soup.find_all('a'):
        if link.get('href').startswith('gfs.'):
            latest_date_dir = link.get('href')

    # Check the latest available run (00, 06, 12, 18)
    latest_run_url = base_url + latest_date_dir
    response = requests.get(latest_run_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    print(link.get('href').strip('/'))
    print(soup.find_all('a'))
    print(link.get('href').strip('/').isdigit())
    available_runs = [link.get('href').strip('/') for link in soup.find_all('a') if link.get('href').strip('/').isdigit()]
    
    if available_runs:
        latest_run_dir = available_runs[-1]
        return latest_date_dir.strip('/'), latest_run_dir
    else:
        return None, None




def get_previous_gfs_run(date, run):
    """Move to the previous GFS run time (e.g., from 12z to 06z or from today to yesterday)."""
    run_times = ['18', '12', '06', '00']
    
    try:
        run_index = run_times.index(run)
        # If not the first run (18z), move back to the previous one
        if run_index > 0:
            return date, run_times[run_index - 1]
        else:
            # Move to the previous day and reset to the latest run (18z)
            previous_date = (datetime.strptime(date, 'gfs.%Y%m%d') - timedelta(days=1)).strftime('gfs.%Y%m%d')
            return previous_date, '18'
    except ValueError:
        return None, None
    
def get_filtered_gfs_files(date, run, param, level, num_forecasts):
    """
    Fetch filtered GFS files based on the parameter, level (string), and forecast range.
    """
    base_url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl'
    forecast_hours = [f'f{str(i).zfill(3)}' for i in range(0, num_forecasts * 6, 6)]  # Limit to specified forecasts
    files = []

    for forecast_hour in forecast_hours:
        # Prepare the 'lev_' parameter dynamically depending on if the level is a string
        level_param = f'lev_{level}'  # Always use string level, e.g., 'lev_surface' or 'lev_500_mb'

        # Build the filtered URL for GFS data
        params = {
            'file': f'gfs.t{run}z.pgrb2.0p25.{forecast_hour}',
            level_param: 'on',  # Set the level parameter as a string
            f'var_{param}': 'on',  # Specify the variable dynamically (e.g., HGT or APCP)
            'dir': f'/{date}/{run}/atmos'  # Correct directory structure
        }

        response = requests.get(base_url, params=params, allow_redirects=True)

        # Check if the file exists and is accessible
        if response.status_code == 200:
            # Append the file name with relevant metadata (param, level, date, run)
            file_name = f'{param}_{level}_{date}_{run}_{forecast_hour}.grb2'
            files.append((file_name, response.content))
        else:
            print(f"File not found: {response.url}")

    return files

def save_filtered_files(file_data):
       
    """Save the filtered GFS files to the specified directory."""    
    os.makedirs(GFS_DIR, exist_ok=True) 

    downloaded_files = []

    for file_name, file_content in file_data:
        file_path = os.path.join(GFS_DIR, file_name)
        
        print(f"Saving: {file_name}")
        with open(file_path, 'wb') as f:
            f.write(file_content)

        downloaded_files.append(file_path)

    return downloaded_files



def find_grib_file(param, level):
    """Search for the corresponding GRIB file in the gfs_data folder."""
    
    for filename in os.listdir(GFS_DIR):
        print(filename)
        print(param)
        print(level)
        if param in filename and f'{level}' in filename and filename.endswith('.grb2'):
            return os.path.join(GFS_DIR, filename)
    return None


def find_grib_files(param, level):
    """Search for all corresponding GRIB files in the gfs_data folder that match param and level."""
    matching_files = []
    
    print(os.getcwd())
    print(os.listdir(os.getcwd()))
    for dir in os.listdir(os.getcwd()):
        if os.path.isdir(dir):
            print(os.listdir(dir))

        #print(f"Checking file: {filename}")

    # Iterate through the files in the GFS_DIR
    for filename in os.listdir(GFS_DIR):
        print(f"Checking file: {filename}")
        
        # Check if both param and level are part of the filename and if it ends with .grb2
        if param in filename and f'{level}' in filename and filename.endswith('.grb2'):
            # If both conditions are satisfied, add the file to the list of matches
            matching_files.append(os.path.join(GFS_DIR, filename))
    
    # Return the list of matching files, or None if no matches found
    return matching_files if matching_files else None

def create_meta_file(png_filename, param, level, lat_min, lat_max, lon_min, lon_max, grib_file, data_min, data_max):
    """Create a meta file with description of the data used to generate the PNG, including min and max values."""
    meta_filename = png_filename.replace('.png', '.info')
    os.makedirs(PNG_DIR, exist_ok=True)     
    meta_filepath = os.path.join(PNG_DIR, meta_filename)
    
    with open(meta_filepath, 'w') as meta_file:
        meta_file.write(f"Parameter: {param}\n")
        meta_file.write(f"Level: {level}\n")
        meta_file.write(f"Latitude bounds: {lat_min} to {lat_max}\n")
        meta_file.write(f"Longitude bounds: {lon_min} to {lon_max}\n")
        meta_file.write(f"Source GRIB file: {grib_file}\n")
        meta_file.write(f"Min value: {data_min}\n")
        meta_file.write(f"Max value: {data_max}\n")
    
    return meta_filepath



def grib_to_png(grib_file, param, level, lat_min, lat_max, lon_min, lon_max, png_filename):
    """
    Convert GRIB data within specific lat/lon bounds to grayscale PNG and create a meta file.
    
    Parameters:
    - grib_file: Path to the GRIB file
    - param: Geophysical parameter (e.g., HGT)
    - level: Pressure level in mb (e.g., 500)
    - lat_min, lat_max, lon_min, lon_max: Latitude and longitude bounds
    - png_filename: Filename for the output PNG file (without path)
    
    Returns:
    - png_filepath: Full path to the generated PNG file
    - meta_filepath: Full path to the generated meta file
    """
    # Open the GRIB file using pygrib
    try:
        grbs = pygrib.open(grib_file)
        
        # Select the first GRIB message (since it's the one we need)
        grb = grbs.message(1)  # First message in the GRIB file
        
        # Extract data for the specific lat/lon boundary using pygrib's .data() method
        data_within_boundary, lats, lons = grb.data(
            lat1=lat_min, lat2=lat_max, lon1=lon_min, lon2=lon_max)
        
        # Get the min and max values of the data
        data_min = np.min(data_within_boundary)
        data_max = np.max(data_within_boundary)
        
        # Normalize the data to the 0-255 range for grayscale
        data_normalized = 255 * (data_within_boundary - data_min) / (data_max - data_min)
        
        # Construct full file paths for PNG and meta file
        png_filepath = os.path.join(PNG_DIR, png_filename)
        meta_filename = png_filename.replace('.png', '.info')
        meta_filepath = os.path.join(PNG_DIR, meta_filename)
        
        # Convert to PIL image (grayscale)
        img = Image.fromarray(data_normalized.astype('uint8'))
        
        # Save PNG in the PNG directory
        os.makedirs(PNG_DIR, exist_ok=True)
        img.save(png_filepath)
        
        # Create a corresponding meta file with details of the PNG and GRIB file
        create_meta_file(png_filename, param, level, lat_min, lat_max, lon_min, lon_max, grib_file, data_min, data_max)
        
        return png_filepath, meta_filepath
    except Exception as e:
        print(f"Error processing GRIB file: {e}")
        return None, None

import os

def find_global_min_max(param, level):
    """
    Iterate through all .info files for the given param and level,
    and find the global min and max values.

    Parameters:
    - param: Geophysical parameter (e.g., 'HGT')
    - level: Pressure level (e.g., '500_mb')

    Returns:
    - global_min: Global minimum value across all forecast hours
    - global_max: Global maximum value across all forecast hours
    - info_files: List of .info file paths
    """
    global_min = float('inf')
    global_max = float('-inf')
    info_files = []

    # Find all the .info files for the given param and level
    for filename in os.listdir(PNG_DIR):
        if filename.endswith('.info') and param in filename and level in filename:
            info_filepath = os.path.join(PNG_DIR, filename)
            info_files.append(info_filepath)

            # Read the .info file to find min and max values
            with open(info_filepath, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if "Min value" in line:
                        file_min = float(line.split(':')[1].strip())
                        global_min = min(global_min, file_min)
                    elif "Max value" in line:
                        file_max = float(line.split(':')[1].strip())
                        global_max = max(global_max, file_max)

    return global_min, global_max, info_files




def update_info_files_with_global_min_max(info_files, global_min, global_max):
    """
    Update each .info file to include the global min and max values.
    
    Parameters:
    - info_files: List of .info file paths
    - global_min: Global minimum value across all forecast hours
    - global_max: Global maximum value across all forecast hours
    """
    for info_filepath in info_files:
        with open(info_filepath, 'a') as f:  # Append global min/max to the file
            f.write(f"Global Min: {global_min}\n")
            f.write(f"Global Max: {global_max}\n")
        print(f"Updated {info_filepath} with global min/max")




def denormalize_data(img_data, local_min, local_max):
    """Denormalize image data back to its original range using local min and max values."""
    return (img_data / 255) * (local_max - local_min) + local_min

def renormalize_data(denormalized_data, global_min, global_max):
    """Normalize denormalized data to the range 0-255 using global min and max values."""
    return 255 * (denormalized_data - global_min) / (global_max - global_min)

def renormalize_pngs(param, level, global_min, global_max):
    """
    Re-normalize the PNG files for the given param and level using the global min and max values.
    
    Parameters:
    - param: Geophysical parameter (e.g., 'HGT')
    - level: Pressure level (e.g., '500_mb')
    - global_min: Global minimum value across all forecast hours
    - global_max: Global maximum value across all forecast hours
    """
    for filename in os.listdir(PNG_DIR):
        if filename.endswith('.png') and param in filename and level in filename:
            png_filepath = os.path.join(PNG_DIR, filename)
            info_filepath = png_filepath.replace('.png', '.info')

            # Read the local min and max from the .info file
            local_min, local_max = None, None
            with open(info_filepath, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if "Min value" in line:
                        local_min = float(line.split(":")[1].strip())
                    elif "Max value" in line:
                        local_max = float(line.split(":")[1].strip())

            if local_min is None or local_max is None:
                print(f"Error: Could not find local min/max in {info_filepath}")
                continue

            # Load the PNG image as a numpy array
            img = Image.open(png_filepath)
            img_data = np.array(img, dtype=np.float32)

            # Denormalize the data using the local min and max values
            denormalized_data = denormalize_data(img_data, local_min, local_max)

            # Renormalize the data using the global min and max values
            renormalized_data = renormalize_data(denormalized_data, global_min, global_max)

            # Clip the values to the valid range of 0–255 to ensure proper PNG format
            renormalized_data = np.clip(renormalized_data, 0, 255)

            # Convert back to uint8 to save as an image
            renormalized_data = renormalized_data.astype('uint8')

            # Save the re-normalized image
            new_img = Image.fromarray(renormalized_data)
            new_img.save(png_filepath)
            print(f"Re-normalized {png_filepath}")



def update_and_renormalize(param, level):
    """
    Find global min and max values across all forecast hours, update info files, 
    and re-normalize the corresponding PNGs.
    
    Parameters:
    - param: Geophysical parameter (e.g., 'HGT')
    - level: Pressure level (e.g., '500_mb')
    - date: GFS date (e.g., '20241009')
    """
    # Step 1: Find global min and max from all .info files
    global_min, global_max, info_files = find_global_min_max(param, level)
    
    if info_files:
        # Step 2: Update each .info file with the global min and max
        update_info_files_with_global_min_max(info_files, global_min, global_max)
        
        # Step 3: Re-normalize the corresponding PNGs using the global min and max
        renormalize_pngs(param, level, global_min, global_max)
    else:
        print(f"No .info files found for {param}, {level}")


def delete_all_files_in_directories():
    for directory in [PNG_DIR, GFS_DIR]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)  # Delete the file
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Delete the directory and its contents
                except Exception as e:
                    return f"Failed to delete {file_path}. Reason: {e}", 500
        else:
            return f"{directory} does not exist.", 404
    return "All files deleted successfully.", 200
