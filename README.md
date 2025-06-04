# Wind Field Data Processing

**⚠️ WORK IN PROGRESS - This is a prototype project under active development**

This project provides tools for processing and analyzing wind field data from multiple sources (HRRR model and OpenFOAM NC files).

## Project Structure

The project consists of two main components:

### 1. HRRR Data Processing (`/HRRR`)

Tools for downloading and processing High-Resolution Rapid Refresh (HRRR) model data:

- **Data Download**
  - `hrrr_nat_download.py` - Downloads HRRR data for specified parameters
  - `hrrr_nat_download_single.py` - Downloads a single HRRR file
  - `download_from_prev_hours.py` - Downloads data from previous hours

- **Data Processing**
  - `extract_levels_params.py` - Extracts parameters from GRIB2 files
  - `extract_levels_params_to_imgs.py` - Converts parameters to image format
  - `list_nat_params.py` - Lists available parameters in HRRR files
  - `plot_random_gh_profiles.py` - Visualizes random geopotential height profiles

### 2. OpenFOAM NC Data Processing (`/NC_swaps`)

Tools for processing OpenFOAM NetCDF files:

- **Data Extraction**
  - `extract_nc_params.py` - Lists parameters in NC files
  - `extract_[low/middle/high]_layers_to_csv.py` - Extracts layer data to CSV format
  - `extract_nc_all_levels_params_to_imgs.py` - Converts NC data to image format

- **Generated Data**
  - `[low/middle/high]_layers_grid.csv` - Extracted grid data for different layers
  - `[low/mid/high]_levels_img_encoded/` - Encoded image data
  - `nc_params.txt` - List of available parameters in NC files

## Data Processing Pipeline

### HRRR Data
1. Download HRRR GRIB2 files using download scripts
2. Extract parameters and levels using `extract_levels_params.py`
3. Convert to image format using `extract_levels_params_to_imgs.py`
4. (Optional) Generate CSV files for specific analysis

### OpenFOAM NC Data
1. Extract parameters using `extract_nc_params.py`
2. Generate CSV files for different layers using `extract_*_layers_to_csv.py`
3. Convert to image format using `extract_nc_all_levels_params_to_imgs.py`

## Data Encoding Format

The project uses a special image encoding format for wind field data:

- **RGBA Image Format**
  - R channel: U component (normalized)
  - G channel: V component (normalized)
  - B channel: W component (normalized)
  - A channel: Altitude information (1-254 range)
  - White pixels (255,255,255,255) indicate missing/invalid data

- **Metadata JSON Files**
  - Each image has an accompanying JSON file with:
    - Min/max values for denormalization
    - Grid information
    - Spatial reference data
    - Level-specific parameters

## Usage

1. **HRRR Data Processing**
   ```bash
   cd HRRR
   python hrrr_nat_download.py  # Download data
   python extract_levels_params_to_imgs.py  # Process data
   ```

2. **NC Data Processing**
   ```bash
   cd NC_swaps
   python extract_nc_all_levels_params_to_imgs.py  # Process NC data
   ```

## Data Format Details

### CSV Files
- `*_layers_grid.csv`: Contains raw grid data with columns:
  - altitude, latitude, longitude
  - x/y_from_origin
  - u, v, w components
  - Additional parameters specific to data source

### Image Files
- PNG files in RGBA format
- Each pixel represents a grid point
- Channels encode normalized wind components
- Alpha channel encodes altitude information

### JSON Metadata
- Contains ranges for denormalization
- Grid dimensions and spacing
- Spatial reference information
- Level-specific parameters

## Notes

- White pixels in encoded images represent missing data
- All wind components are normalized per level
- Altitude information is encoded in 1-254 range for proper identification of missing data

## Dependencies

- Python 3.x
- NumPy
- Pillow (PIL)
- netCDF4 (for NC files) 