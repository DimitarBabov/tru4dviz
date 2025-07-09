# NetCDF to Image Encoding Process

This document describes the file paths and structure for encoding wind field data from NetCDF files into RGBA images with accompanying metadata JSON files.

## File Locations

### Script Location
- Encoding script: `NC_swaps/extract_nc_all_levels_params_to_imgs.py`

### Input Files (NCdata/)
- OpenFOAM CFD data: `NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc`
- HRRR weather data: `NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc`
- Difference data: `NCdata/diff_cfd_usa-tx-elizabethtown_2023-02-14T15-00-00.nc`

### Output Directories (NC_swaps/)

For CFD data:
```
NC_swaps/
├── low_levels_img_encoded_cfd/
├── mid_levels_img_encoded_cfd/
└── high_levels_img_encoded_cfd/
```

For HRRR data:
```
NC_swaps/
├── low_levels_img_encoded_hrrr/
├── mid_levels_img_encoded_hrrr/
└── high_levels_img_encoded_hrrr/
```

For difference data:
```
NC_swaps/
├── low_levels_img_encoded_diff-cfd-hrrr/
├── mid_levels_img_encoded_diff-cfd-hrrr/
└── high_levels_img_encoded_diff-cfd-hrrr/
```

Each output directory contains:
- PNG images: `{level}_level{k}_img.png`
- Metadata files: `{level}_level{k}_meta.json`

Where:
- `{level}` is one of: low, mid, high
- `{k}` is the level index within the group

## Data Encoding

The encoding process converts wind field data (u, v, w components) into RGBA images:
- Red channel (R): Normalized u-component of wind
- Green channel (G): Normalized v-component of wind
- Blue channel (B): Normalized w-component of wind
- Alpha channel (A): Normalized altitude encoded in range [1, 254]

Missing data points are encoded as RGBA(255, 255, 255, 255).

## Metadata Structure

Each image has an accompanying JSON metadata file containing:
```json
{
  "group": "low|mid|high",
  "level_index": 0,
  "altitude": 10.0,
  "u_min": -10.0, "u_max": 10.0,
  "v_min": -10.0, "v_max": 10.0,
  "w_min": -5.0, "w_max": 5.0,
  "alt_min": 0.0, "alt_max": 100.0,
  "min_lat": 32.0, "max_lat": 34.0,
  "min_lon": -98.0, "max_lon": -96.0,
  "num_lat": 100, "num_lon": 100,
  "debug_scale": 1,
  "min_x_from_origin": -1000.0,
  "max_x_from_origin": 1000.0,
  "min_y_from_origin": -1000.0,
  "max_y_from_origin": 1000.0,
  "lat_origin": 33.0265,
  "lon_origin": -97.2725
}
```

## Requirements and Dependencies

### Python Packages
```
netCDF4     # For reading NetCDF files
numpy       # For numerical operations
Pillow      # For image processing (import PIL)
```

### Installation
You can install the required packages using pip:
```bash
pip install netCDF4 numpy Pillow
```

### Python Version
- Python 3.6 or higher recommended

### System Requirements
- Sufficient disk space for output images and metadata files
  - Each level generates two files:
    - PNG image file (~100KB-1MB depending on grid size)
    - JSON metadata file (~1KB)
  
