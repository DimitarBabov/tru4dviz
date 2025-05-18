# WILL CHANGE


import csv
import glob
import os
import requests
from flask import Flask, jsonify, request, send_file, send_from_directory
from fetch_gfs_data import  PNG_DIR, delete_all_files_in_directories, find_global_min_max, find_grib_file, find_grib_files, get_filtered_gfs_files,  get_latest_gfs_run, get_previous_gfs_run, grib_to_png, renormalize_pngs, save_filtered_files, update_and_renormalize, update_info_files_with_global_min_max
from isobariclines import CreateIsobaricLines

app = Flask(__name__)

@app.route('/')
def home():
    return "Serving... Weather Model Stadium ... Envision Innovative Technologies!"


@app.route('/list-files')
def list_files():
    files = os.listdir('.')
    return '<br>'.join(files)

# Function to load ZIP code data from a text file
def load_zip_code_data(file_path='zip_codes.txt'):
    zip_code_data = {}
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            zip_code = row['ZIP']
            latitude = float(row['Latitude'])
            longitude = float(row['Longitude'])
            zip_code_data[zip_code] = (latitude, longitude)
    return zip_code_data

# Load ZIP code data at the start
zip_code_data = load_zip_code_data()

# Function to get coordinates from ZIP code
def get_coordinates_from_zip(zip_code):
    return zip_code_data.get(zip_code, (None, None))

# Function to get weather observation data from NOAA
def get_observation_data(lat, lon):
    # Get the nearest weather station URL for the given latitude and longitude
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Invalid latitude/longitude or NOAA service issue."}, 400

    data = response.json()

    # Extract observation station URL
    try:
        observation_stations_url = data['properties']['observationStations']
    except KeyError:
        return {"error": "Unable to find observation stations URL."}, 404

    # Make a request to get the list of nearby observation stations
    stations_response = requests.get(observation_stations_url)
    if stations_response.status_code != 200:
        return {"error": "Unable to fetch station list."}, 500

    stations_data = stations_response.json()

    # Get the first station ID from the list of stations
    try:
        station_id = stations_data['features'][0]['properties']['stationIdentifier']
    except (KeyError, IndexError):
        return {"error": "Unable to find any stations in the list."}, 404

    # Get the latest observation data for the station
    observation_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
    obs_response = requests.get(observation_url)
    
    if obs_response.status_code != 200:
        return {"error": "Unable to fetch observation data."}, 500

    obs_data = obs_response.json()

    # Fetch the station name
    station_url = f"https://api.weather.gov/stations/{station_id}"
    station_response = requests.get(station_url)
    if station_response.status_code != 200:
        return {"error": "Unable to fetch station data."}, 500

    station_data = station_response.json()
    station_name = station_data['properties']['name']

    # Add the station name to the weather data
    weather_data = obs_data['properties']
    weather_data['stationName'] = station_name

    return weather_data, 200

# Function to get weather forecast data from NOAA, including icons
def get_forecast_data(lat, lon):
    # Get the forecast grid information for the given latitude and longitude
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Invalid latitude/longitude or NOAA service issue."}, 400

    data = response.json()

    # Extract forecast URL
    try:
        forecast_url = data['properties']['forecast']
        print(forecast_url)
    except KeyError:
        return {"error": "Unable to find forecast URL."}, 404

    # Fetch the forecast data
    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        return {"error": "Unable to fetch forecast data."}, 500

    forecast_data = forecast_response.json()
    
    # Include the icon URL in the forecast periods
    forecast_periods = forecast_data['properties']['periods']
    for period in forecast_periods:
        # period['icon'] contains the URL to the weather icon
        # You can modify this data or use it directly as needed
        period['icon'] = period.get('icon', '')

    return forecast_periods, 200


# Function to get RAw weather forecast data from NOAA, including icons.only DEBUG
def get_forecast_data_raw(lat, lon):
    # Get the forecast grid information for the given latitude and longitude
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Invalid latitude/longitude or NOAA service issue."}, 400

    data = response.json()
    print(response)
    # Extract forecast URL
    try:
        forecast_url = data['properties']['forecast']
        print(forecast_url)
    except KeyError:
        return {"error": "Unable to find forecast URL."}, 404

    # Fetch the forecast data
    forecast_response = requests.get(forecast_url)
    if forecast_response.status_code != 200:
        return {"error": "Unable to fetch forecast data."}, 500

    forecast_data = forecast_response.json()
    return forecast_data, 200

# Route to get weather data by latitude and longitude
@app.route('/weather/latlon', methods=['GET'])
def weather_by_latlon():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required."}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "Invalid latitude or longitude format."}), 400

    # Fetch the weather data
    weather_data, status = get_observation_data(lat, lon)
    return jsonify(weather_data), status

# Route to get weather data by ZIP code
@app.route('/weather/zip', methods=['GET'])
def weather_by_zip():
    zip_code = request.args.get('zip')

    # Get coordinates from ZIP code
    lat, lon = get_coordinates_from_zip(zip_code)

    # Check if valid coordinates were found
    if lat is None or lon is None:
        return jsonify({"error": "Invalid ZIP code or coordinates not found."}), 400

    # Fetch the weather data
    weather_data, status = get_observation_data(lat, lon)
    return jsonify(weather_data), status

# Route to get weather forecast by latitude and longitude
@app.route('/weather/forecast', methods=['GET'])
def weather_forecast():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required."}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "Invalid latitude or longitude format."}), 400

    # Fetch the forecast data
    forecast_data, status = get_forecast_data_raw(lat, lon)
    return jsonify(forecast_data), status

# Route to get weather forecast by ZIP code
@app.route('/weather/forecast/zip', methods=['GET'])
def weather_forecast_by_zip():
    zip_code = request.args.get('zip')

    # Get coordinates from ZIP code
    lat, lon = get_coordinates_from_zip(zip_code)

    # Check if valid coordinates were found
    if lat is None or lon is None:
        return jsonify({"error": "Invalid ZIP code or coordinates not found."}), 400

    # Fetch the forecast data
    forecast_data, status = get_forecast_data(lat, lon)
    return jsonify(forecast_data), status




   
# Example URLs for local testing:
# To get weather data by latitude and longitude:
# http://127.0.0.1:5000/weather/latlon?lat=39.9526&lon=-75.1652
#
# To get weather data by ZIP code:
# http://127.0.0.1:5000/weather/zip?zip=19103
#
# To get weather forecast by latitude and longitude:
# http://127.0.0.1:5000/weather/forecast?lat=39.9526&lon=-75.1652
#
# To get weather forecast by ZIP code:
# http://127.0.0.1:5000/weather/forecast/zip?zip=19103


#US lat,lon boundary
#http://127.0.0.1:5000/extract_data_by_bounds?parameter=HGT&lat_min=24.396308&lat_max=49.384358&lon_min=235.0&lon_max=293.06543

#US adjusted by req
#THIS DOWNLOADS DATA AS PNGS FOR THE US
#http://127.0.0.1:5000/extract_data_by_bounds?parameter=HGT&lat_min=21.13812&lat_max=64.750&lon_min=237.2805&lon_max=312.25


#FETCHING GFS SMALLER CHUNKS

# Flask route to trigger data fetching
@app.route('/fetch_gfs_data', methods=['GET'])
def fetch_gfs_data():
    """
    Fetch the latest filtered GFS data based on query parameters:
    - param: Geophysical parameter (e.g., HGT)
    - level: Pressure level (e.g., "500" for 500 mb or "surface")
    - forecasts: Number of forecast hours to retrieve (e.g., 4)
    """

    try:
        # Step 1: Get query parameters from the request
        param = request.args.get('param', default='HGT')
        level = request.args.get('level', default='500_mb')  # Treating level as string
        num_forecasts = request.args.get('forecasts', default=4, type=int)

        # Step 2: Get the latest date and run
        latest_date, latest_run = get_latest_gfs_run()

        if not latest_date or not latest_run:
            return jsonify({"message": "No GFS data available at the moment"}), 404

        # Step 3: Try downloading filtered files from the latest run, move back if files are not found
        attempts = 0
        max_attempts = 4
        file_data = []

        while attempts < max_attempts:
            file_data = get_filtered_gfs_files(latest_date, latest_run, param, level, num_forecasts)
            if file_data:  # If files were found
                break
            print(f"No files found for {latest_date}/{latest_run}. Trying the previous cycle.")
            latest_date, latest_run = get_previous_gfs_run(latest_date, latest_run)
            attempts += 1

        if not file_data:
            return jsonify({"message": "No valid GFS forecast files found after checking previous cycles"}), 404
        
        #Clean up older files in gfs_data folder and png_data folder to make sure we have latest run
        #cleanup_old_param_files(param+level)

        # Step 4: Save the filtered files
        downloaded_files = save_filtered_files(file_data)

        return jsonify({
            "message": "Filtered GFS data fetched successfully",
            "date": latest_date,
            "run": latest_run,
            "files": downloaded_files
        })

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch GFS data",
            "error": str(e)
        }), 500


#http://127.0.0.1:5000/fetch_gfs_data?param=HGT&level=500_mb&forecasts=4


#http://127.0.0.1:5000/download_grib_png?param=HGT&level=500
#http://127.0.0.1:5000/create_png?param=HGT&level=500&min_lat=21.13812&max_lat=64.750&min_lon=237.2805&max_lon=312.25


@app.route('/generate_pngs', methods=['GET'])
def generate_pngs():
    """
    Route that searches for all corresponding GRIB files in gfs_data,
    converts them to grayscale PNGs within the specified lat/lon bounds,
    creates meta files for each, and returns the PNG download URLs using the same name as the GRIB file.
    After generation, the function also updates the global min/max in .info files and renormalizes PNGs.
    
    Parameters:
    - param: Geophysical parameter (e.g., HGT)
    - level: Pressure level in mb (e.g., 500)
    - min_lat, max_lat, min_lon, max_lon: Lat/lon bounds for extracting the data
    """
    param = request.args.get('param', default='HGT')
    level = request.args.get('level', default='500_mb')
    
    # Latitude and longitude bounds
    lat_min = request.args.get('min_lat', type=float)
    lat_max = request.args.get('max_lat', type=float)
    lon_min = request.args.get('min_lon', type=float)
    lon_max = request.args.get('max_lon', type=float)
    
    if lat_min is None or lat_max is None or lon_min is None or lon_max is None:
        return jsonify({"message": "Please provide valid lat/lon bounds"}), 400
    
    # Step 1: Find all corresponding GRIB files in the gfs_data folder
    grib_files = find_grib_files(param, level)
    
    if not grib_files:
        return jsonify({"message": "No matching GRIB files found"}), 404
    
    # Step 2: For each GRIB file, generate the corresponding PNG and meta file
    results = []
    for grib_file in grib_files:
        # Extract the base name of the GRIB file (without extension)
        base_filename = os.path.splitext(os.path.basename(grib_file))[0]
        
        # Replace '.' with '_' in the base filename
        sanitized_filename = base_filename.replace('.', '_')
        
        # Construct the PNG and meta filenames by changing the extension
        png_filename = f"{sanitized_filename}.png"
        meta_filename = f"{sanitized_filename}.info"
        
        # Convert GRIB to PNG and generate the meta file
        png_filepath, meta_filepath = grib_to_png(grib_file, param, level, lat_min, lat_max, lon_min, lon_max, png_filename)
        
        if png_filepath:
            results.append({
                "png_filename": png_filename,
                "png_download_url": request.url_root + 'download_grib_png/' + png_filename,
                "meta_download_url": request.url_root + 'download_meta_file/' + meta_filename
            })
        else:
            return jsonify({"message": f"Error converting GRIB to PNG for {grib_file}"}), 500

    # Step 3: After generating PNGs, find global min/max and update .info files
    global_min, global_max, info_files = find_global_min_max(param, level)
    
    if global_min is None or global_max is None:
        return jsonify({"message": "Could not calculate global min/max values."}), 500
    
    # Update all .info files with global min/max
    update_info_files_with_global_min_max(info_files, global_min, global_max)
    
    # Step 4: Renormalize all PNGs using the global min/max values
    renormalize_pngs(param, level, global_min, global_max)

    #Creates isobaric lines for hgt
    if(param.startswith("HGT")):
        CreateIsobaricLines()
    
    # Step 5: Return the list of PNG and meta file download URLs
    return jsonify({
        "message": f"{len(results)} PNG(s) and meta file(s) created and renormalized successfully",
        "results": results
    })


# Route to download the meta file for the corresponding PNG based on filename
@app.route('/download_meta_file/<filename>', methods=['GET'])
def download_meta_file(filename):
    """
    Route that allows downloading the meta (.info) file based on the given filename.
    The meta file contains the metadata about the data used to generate the PNG.
    """
    # Expect filename to be passed without extension, add '.info' extension
    meta_filename = f'{filename}'
    meta_filepath = os.path.join(PNG_DIR, meta_filename)
    
    if not os.path.exists(meta_filepath):
        return jsonify({"message": "Meta file not found"}), 404
    
    return send_file(meta_filepath, mimetype='text/plain', as_attachment=True)


# Route to download the PNG file based on filename
@app.route('/download_grib_png/<filename>', methods=['GET'])
def download_grib_png(filename):
    """
    Route to download the PNG file based on the given filename.
    """
    # Expect filename to be passed without extension, add '.png' extension
    png_filename = f'{filename}'
    png_filepath = os.path.join(PNG_DIR, png_filename)
    
    if not os.path.exists(png_filepath):
        return jsonify({"message": "PNG file not found"}), 404
    
    return send_file(png_filepath, mimetype='image/png', as_attachment=True)


@app.route('/renormalize_pngs', methods=['GET'])
def renormalize_pngs_route():
    """
    Flask route to trigger renormalization of PNGs for the given param, level, and date.
    Example URL: /renormalize_pngs?param=HGT&level=500_mb
    """
    # Get query parameters from the request
    param = request.args.get('param')
    level = request.args.get('level')
    
    # Validate that all required parameters are provided
    if not param or not level:
        return jsonify({"error": "Missing required parameters. Please provide 'param', 'level'."}), 400
    
    try:
        # Call the renormalization function
        update_and_renormalize(param, level)
        return jsonify({"status": "success", "message": f"Renormalization completed for {param} {level}."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_png_meta_links', methods=['GET'])
def get_png_meta_links():
    """
    Route that returns a list of links to download the existing PNG and meta files 
    starting with the parameter name (e.g., HGT, ABSV).

    Parameters:
    - param: Geophysical parameter (e.g., HGT)
    - level: Pressure level in mb (e.g., 500)
    """
    param = request.args.get('param', default='HGT')
    level = request.args.get('level', default='500_mb')

    # Search for all PNG and meta files starting with the parameter name in the PNG_DIR folder
    png_files = glob.glob(os.path.join(PNG_DIR, f"{param}_{level}*.png"))
    meta_files = glob.glob(os.path.join(PNG_DIR, f"{param}_{level}*.info"))

    if not png_files and not meta_files:
        return jsonify({"message": "No matching PNG or meta files found"}), 404

    results = []
    for png_file, meta_file in zip(png_files, meta_files):
        # Extract the base name of the files
        png_filename = os.path.basename(png_file)
        meta_filename = os.path.basename(meta_file)

        # Add the download URLs to the results list
        results.append({
            "png_filename": png_filename,
            "png_download_url": request.url_root + 'download_grib_png/' + png_filename,            
            "meta_download_url": request.url_root + 'download_meta_file/' + meta_filename
        })

    # Return the list of PNG and meta file download URLs
    return jsonify({
        "message": f"{len(results)} PNG(s) and meta file(s) found successfully",
        "results": results
    })





@app.route('/get_isobaric_hgt_links', methods=['GET'])
def get_isobaric_hgt_links():
    """
    Route that returns a list of links to download all PNG files 
    starting with "ISOBARIC_HGT" in the PNG_DIR folder.
    """

    # Search for all PNG files starting with "ISOBARIC_HGT" in the PNG_DIR folder
    png_files = glob.glob(os.path.join(PNG_DIR, "ISOBARICHGT*.png"))

    if not png_files:
        return jsonify({"message": "No matching ISOBARICHGT PNG files found"}), 404

    results = []
    for png_file in png_files:
        # Extract the base name of the files
        png_filename = os.path.basename(png_file)

        # Add the download URLs to the results list
        results.append({
            "png_filename": png_filename,
            "png_download_url": request.url_root + 'download_grib_png/' + png_filename
        })

    # Return the list of PNG file download URLs
    return jsonify({
        "message": f"{len(results)} ISOBARICHGT PNG file(s) found successfully",
        "results": results
    })


@app.route('/delete-files', methods=['GET','POST'])
def delete_files_route():
    message, status_code = delete_all_files_in_directories()
    return jsonify({"message": message}), status_code

if __name__ == '__main__':
    # Start the scheduler
    #start_scheduler()
    app.run(debug=True)

