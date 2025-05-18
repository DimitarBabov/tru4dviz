# HRRR Fort Worth Data Extraction and Analysis

This project provides scripts and a workflow for extracting, processing, and visualizing vertical profile data from HRRR model GRIB2 files, focused on the Fort Worth, Texas area.

## Workflow Overview

1. **Extract all available levels and parameters from HRRR GRIB2 files**
    - Parameters: Pressure (`pres`), Geopotential Height (`gh`), Temperature (`t`), U/V Wind Components (`u`, `v`), Vertical Velocity (`w`).
    - For each parameter and each available model level, a separate `.npy` file is generated (e.g., `gh_lev1.npy`, `t_lev2.npy`, etc.).
    - Latitude and longitude arrays are also saved as `.npy` files.
    - Only levels where **all parameters are available** are processed and saved.

2. **Generate CSVs for the Fort Worth area**
    - For each valid level, a CSV is created (e.g., `fort_worth_level1_params.csv`) containing only grid points within the Fort Worth bounding box.
    - Each CSV includes columns: `latitude`, `longitude`, and all parameters for that level (with units in brackets, e.g., `gh[gpm]`).
    - Only levels with complete parameter data are included.

3. **Generate a CSV of geopotential height profiles for all available levels**
    - The script `extract_gh_levels_fort_worth.py` creates a CSV (`fort_worth_gh_levels.csv`) with columns: `latitude`, `longitude`, and `gh[gpm]_levX` for all available levels.

4. **Plot random geopotential height profiles**
    - The script `plot_random_gh_profiles.py` randomly selects 5 grid points from `fort_worth_gh_levels.csv` and plots their geopotential height profiles as a function of model level.
    - The plot is saved as `random_gh_profiles.png`.

## Scripts

- **extract_levels_params.py**
    - Extracts all available levels and parameters from the HRRR GRIB2 file.
    - Saves each parameter/level as a separate `.npy` file, only for levels where all parameters are present.
    - Generates CSVs for the Fort Worth area for each valid level.

- **extract_gh_levels_fort_worth.py**
    - Loads all available `gh_levX.npy` files and creates a CSV with geopotential height profiles for all grid points in the Fort Worth area.

- **plot_random_gh_profiles.py**
    - Loads `fort_worth_gh_levels.csv`, randomly selects 5 grid points, and plots their geopotential height profiles across all available levels.
    - Saves the plot as `random_gh_profiles.png`.

## Data Details

- **Fort Worth bounding box:**
    - Longitude: -97.648 to -96.898
    - Latitude: 32.742 to 33.231
- **Model levels:**
    - All available levels in the GRIB2 file are processed, but only those with complete parameter data are included in outputs.
- **Parameter units:**
    - `pres[Pa]`, `gh[gpm]`, `t[K]`, `u[m/s]`, `v[m/s]`, `w[Pa/s]`

## Usage Notes

- All scripts are designed to be run from the `HRRR` directory.
- Ensure the HRRR GRIB2 file is present in `HRRRdata_nat` and named appropriately.
- The scripts are robust to missing data: only complete levels are processed.
- Masked (missing) values in the GRIB2 data are saved as `np.nan` in the `.npy` files and CSVs.
- The plotting script sets the x-axis to model levels 0–50 (or the maximum available).

## Example Workflow

1. Run `extract_levels_params.py` to extract and save all parameter/level `.npy` files and Fort Worth CSVs.
2. Run `extract_gh_levels_fort_worth.py` to generate a CSV of geopotential height profiles for all available levels.
3. Run `plot_random_gh_profiles.py` to visualize 5 random vertical profiles from the Fort Worth area.

---

If you have questions or want to extend the workflow, see the scripts for further customization or contact the author. 

## Next Steps

1. **Convert w (omega, pressure vertical velocity) to W (geometric vertical velocity)**
    - Implement a script or function to convert the `w` parameter (Pa/s) to the geometric vertical velocity (W, m/s) for each grid point and level, using the appropriate thermodynamic relationships and model metadata.
    - Add the resulting W values to the data outputs for further analysis and visualization.

2. **Optimize data storage and CSV structure**
    - Change the workflow to generate a single `.npy` file per parameter containing all levels, rather than one file per level. This will improve efficiency and make it easier to work with the data in bulk.
    - Update the CSV generation scripts to use this new structure and to allow flexible selection of levels.

3. **Prepare data for Unity visualization**
    - Create scripts to generate 3D mesh data (vertices and triangles) from the gridded model output, suitable for import into Unity or other 3D engines.
    - This will enable interactive visualization of the atmospheric profiles and fields in a 3D environment. 