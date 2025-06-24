import os
import pygrib
import numpy as np

# Define the path to the GRIB2 file
data_folder = "HRRRdata_nat"  # Folder where the native GRIB2 files are stored
grib_file_name = "hrrr.t15z.wrfnatf02.grib2"  # Replace with your native GRIB2 file name
grib_file_path = os.path.join(data_folder, grib_file_name)

# Define output file path
output_file = "hrrr_nat_parameters.txt"

# Check if the GRIB2 file exists
if not os.path.exists(grib_file_path):
    raise FileNotFoundError(f"GRIB2 file not found: {grib_file_path}")

print(f"Reading native GRIB2 file: {grib_file_path}")
print(f"Results will also be written to: {output_file}")

# Helper function to safely get attributes
def safe_get_attr(obj, attr, default="Not available"):
    try:
        return getattr(obj, attr)
    except (AttributeError, KeyError):
        return default

# Helper function to format level information
def format_level_info(grb):
    level_type = safe_get_attr(grb, 'typeOfLevel', "unknown")
    level = safe_get_attr(grb, 'level', "unknown")
    
    # For pressure levels, convert to hPa/mb if in Pa
    if level_type == 'isobaricInhPa' and isinstance(level, (int, float)) and level > 1100:
        level = level / 100
    
    # For height levels, add units
    if level_type == 'heightAboveGround':
        return f"{level_type} at {level} m"
    elif level_type == 'isobaricInhPa':
        return f"{level_type} at {level} hPa"
    else:
        return f"{level_type} at {level}"

# Open the output file for writing
with open(output_file, 'w') as f:
    f.write(f"HRRR Native Grid Parameters from file: {grib_file_path}\n\n")
    
    # Open the GRIB2 file using pygrib
    try:
        grbs = pygrib.open(grib_file_path)
        
        # Try to get grid information
        try:
            first_grb = grbs[1]
            
            grid_info = "\n### Grid Information ###\n"
            
            try:
                grid_size = f"Grid Size: {safe_get_attr(first_grb, 'Ni')}x{safe_get_attr(first_grb, 'Nj')} points\n"
                grid_info += grid_size
            except Exception as e:
                grid_info += f"Grid Size: Could not determine ({str(e)})\n"
            
            # Extract lat/lon bounds
            try:
                lats, lons = first_grb.latlons()
                
                lat_min = np.nanmin(lats)
                lat_max = np.nanmax(lats)
                lon_min = np.nanmin(lons)
                lon_max = np.nanmax(lons)
                
                geo_extent = (
                    f"Geographic Extent:\n"
                    f"  Latitude:  min={lat_min:.4f}°, max={lat_max:.4f}°\n"
                    f"  Longitude: min={lon_min:.4f}°, max={lon_max:.4f}°\n"
                    f"  Grid shape: {lats.shape}\n"
                )
                grid_info += geo_extent
            except Exception as e:
                grid_info += f"Geographic Extent: Could not determine ({str(e)})\n"
            
            print(grid_info)
            f.write(grid_info)
            
        except Exception as e:
            grid_error = f"\n### Grid Information ###\nCould not extract grid information: {str(e)}\n"
            print(grid_error)
            f.write(grid_error)
        
        # Reset file pointer
        grbs.seek(0)
        
        # Organize parameters by level type
        params_by_level = {}
        
        for grb in grbs:
            level_type = safe_get_attr(grb, 'typeOfLevel', "unknown")
            if level_type not in params_by_level:
                params_by_level[level_type] = []
            
            short_name = safe_get_attr(grb, 'shortName', "unknown")
            name = safe_get_attr(grb, 'name', "unknown")
            level = safe_get_attr(grb, 'level', "unknown")
            
            params_by_level[level_type].append({
                'message': grb.messagenumber,
                'short_name': short_name,
                'name': name,
                'level': level
            })
        
        # Write organized parameters
        header = "\n### List of Parameters by Level Type ###\n"
        print(header)
        f.write(header)
        
        for level_type, params in sorted(params_by_level.items()):
            section = f"\n{level_type} Parameters:"
            print(section)
            f.write(section + "\n")
            
            # Sort parameters by level if numeric
            try:
                params.sort(key=lambda x: float(x['level']) if isinstance(x['level'], (int, float, str)) else x['level'])
            except:
                params.sort(key=lambda x: x['message'])
            
            for param in params:
                line = f"Message {param['message']}: {param['short_name']} ({param['name']}) - Level: {param['level']}"
                print(line)
                f.write(line + "\n")
        
        # Add summary information
        summary = f"\n### Summary ###\n"
        summary += f"Total number of parameters: {len(grbs)}\n"
        summary += f"Number of level types: {len(params_by_level)}\n"
        summary += "\nLevel types and parameter counts:\n"
        for level_type, params in sorted(params_by_level.items()):
            summary += f"- {level_type}: {len(params)} parameters\n"
        
        print(summary)
        f.write(summary)
        
        grbs.close()
        print(f"\nSuccessfully wrote parameter list to {output_file}")

    except Exception as e:
        error_msg = f"An error occurred while reading the GRIB2 file: {e}"
        print(error_msg)
        f.write("\n" + error_msg + "\n") 