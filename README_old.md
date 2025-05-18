THIS IS GOING TO HELP FOR THE FLASK APP and UNITY CLIENT APP

# Tru4D Viz - HRRR Weather Visualization Application

A powerful web application for visualizing weather data using the HRRR (High-Resolution Rapid Refresh) weather model. This application provides various weather visualization capabilities including precipitation types, wind data, temperature, and more.

## Features

- Download and process HRRR weather data
- Generate PNG visualizations of weather parameters
- Visualize different types of precipitation (rain, snow, ice pellets, freezing rain)
- Process and colorize weather data for improved visualization
- Reproject weather data to web-friendly formats
- Query weather observations from NOAA by latitude/longitude or ZIP code

## Technologies

- Python 3
- Flask web framework
- Matplotlib for data visualization
- PyGrib for processing GRIB weather data files
- Herbie for downloading HRRR data
- Pillow for image processing
- NumPy for numerical operations

## HRRR Data Processing Pipeline

1. Download HRRR data using `hrrr_download.py`
2. Convert GRIB2 files to PNG images with `hrrr_to_png.py`
3. Process and colorize precipitation data using `process_precip_trimmed_colored_params.py`
4. Process and colorize wind and temperature data with `process_wind_temp_trimmed_colored.py`

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/DimitarBabov/tru4dviz.git
   cd tru4dviz
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

## Directory Structure

- `HRRR/` - Contains scripts for downloading and processing HRRR data
- `HRRRdata/` - Directory for storing downloaded HRRR GRIB2 files
- `HRRRImages/` - Directory for storing initial PNG visualizations
- `HRRRImages_Final/` - Directory for storing processed/colorized visualizations

## API Endpoints

- `/weather/latlon` - Get weather data by latitude and longitude
- `/weather/zip` - Get weather data by ZIP code
- `/weather/forecast` - Get weather forecast by latitude and longitude
- And more...

## License

[Specify your license here]

## Author

Dimitar Babov

## Acknowledgements

- NOAA for providing HRRR weather data
- Herbie library for HRRR data access 