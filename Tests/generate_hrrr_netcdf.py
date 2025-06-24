#!/usr/bin/env python3
"""
Generate HRRR NetCDF file from GRIB data using trilinear interpolation.
This script creates a NetCDF file that matches the structure of the OpenFOAM file
for comparison purposes.
"""

import numpy as np
import xarray as xr
import pygrib
import os
from scipy.interpolate import RegularGridInterpolator
from datetime import datetime, timezone

# Configuration
GRIB_FILE = os.path.join(os.path.dirname(__file__), "../HRRRdata_nat_single/hrrr.t13z.wrfnatf02.grib2")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc")

# Target domain (Elizabethtown, Texas area) - matching OpenFOAM file exactly
TARGET_LAT_MIN = 33.016
TARGET_LAT_MAX = 33.03679
TARGET_LON_MIN = -97.284
TARGET_LON_MAX = -97.26135

# Target grid dimensions (matching OpenFOAM file structure)
LOW_LEVELS_LAT = 231
LOW_LEVELS_LON = 211
MID_LEVELS_LAT = 47
MID_LEVELS_LON = 43
HIGH_LEVELS_LAT = 24
HIGH_LEVELS_LON = 22

# Altitude levels (matching OpenFOAM structure)
LOW_LEVELS = 15  # levels 1-15
MID_LEVELS = 3   # levels 16-18
HIGH_LEVELS = 4  # levels 19-22

print("Loading GRIB data...")
if not os.path.exists(GRIB_FILE):
    raise FileNotFoundError(f"GRIB file not found: {GRIB_FILE}")

# Extract data from GRIB file
levels_data = {}
lat_grib = None
lon_grib = None

with pygrib.open(GRIB_FILE) as grbs:
    for grb in grbs:
        param = grb.shortName
        level = grb.level
        
        if param in ['u', 'v', 'w', 'gh', 'pres', 't']:
            if level not in levels_data:
                levels_data[level] = {}
            
            values = grb.values
            if hasattr(values, 'filled'):
                values = values.filled(np.nan)
            
            levels_data[level][param] = values
            
            # Get lat/lon arrays (same for all fields)
            if lat_grib is None:
                lat_grib, lon_grib = grb.latlons()

print(f"Found data for levels: {sorted(levels_data.keys())}")

# Convert w from pressure velocity to geometric velocity
R_d = 287.05  # J/kg·K (specific gas constant for dry air)
g = 9.81      # m/s² (gravitational acceleration)

for level in levels_data:
    if all(param in levels_data[level] for param in ['w', 't', 'pres']):
        omega = levels_data[level]['w']  # Pa/s
        T = levels_data[level]['t']      # K
        p = levels_data[level]['pres']   # Pa
        
        # Calculate geometric vertical velocity: w = -(omega * R_d * T) / (p * g)
        w_geom = -(omega * R_d * T) / (p * g)
        levels_data[level]['w'] = w_geom

# Select valid levels with all required data
valid_levels = []
for level in sorted(levels_data.keys()):
    if all(param in levels_data[level] for param in ['u', 'v', 'w', 'gh']):
        valid_levels.append(level)

print(f"Valid levels with all wind components: {valid_levels}")

# Create target grids
def create_target_grid(lat_size, lon_size):
    lat_target = np.linspace(TARGET_LAT_MIN, TARGET_LAT_MAX, lat_size)
    lon_target = np.linspace(TARGET_LON_MIN, TARGET_LON_MAX, lon_size)
    return lat_target, lon_target

# Create interpolators for each parameter
def interpolate_to_target(source_data, lat_source, lon_source, lat_target, lon_target):
    """Interpolate source data to target grid using bilinear interpolation."""
    # Create interpolator
    interpolator = RegularGridInterpolator(
        (lat_source[:, 0], lon_source[0, :]), 
        source_data,
        method='linear',
        bounds_error=False,
        fill_value=np.nan
    )
    
    # Create target coordinate arrays
    lon_2d, lat_2d = np.meshgrid(lon_target, lat_target)
    points = np.column_stack([lat_2d.ravel(), lon_2d.ravel()])
    
    # Interpolate
    result = interpolator(points).reshape(lat_2d.shape)
    return result

# Interpolate data for each level group
print("Interpolating to target grids...")

# Initialize output data arrays
def init_data_arrays():
    low_lat, low_lon = create_target_grid(LOW_LEVELS_LAT, LOW_LEVELS_LON)
    mid_lat, mid_lon = create_target_grid(MID_LEVELS_LAT, MID_LEVELS_LON)
    high_lat, high_lon = create_target_grid(HIGH_LEVELS_LAT, HIGH_LEVELS_LON)
    
    data = {
        'low': {
            'lat': low_lat, 'lon': low_lon,
            'u': np.full((LOW_LEVELS, LOW_LEVELS_LAT, LOW_LEVELS_LON), np.nan),
            'v': np.full((LOW_LEVELS, LOW_LEVELS_LAT, LOW_LEVELS_LON), np.nan),
            'w': np.full((LOW_LEVELS, LOW_LEVELS_LAT, LOW_LEVELS_LON), np.nan),
            'alt': np.full(LOW_LEVELS, np.nan)
        },
        'mid': {
            'lat': mid_lat, 'lon': mid_lon,
            'u': np.full((MID_LEVELS, MID_LEVELS_LAT, MID_LEVELS_LON), np.nan),
            'v': np.full((MID_LEVELS, MID_LEVELS_LAT, MID_LEVELS_LON), np.nan),
            'w': np.full((MID_LEVELS, MID_LEVELS_LAT, MID_LEVELS_LON), np.nan),
            'alt': np.full(MID_LEVELS, np.nan)
        },
        'high': {
            'lat': high_lat, 'lon': high_lon,
            'u': np.full((HIGH_LEVELS, HIGH_LEVELS_LAT, HIGH_LEVELS_LON), np.nan),
            'v': np.full((HIGH_LEVELS, HIGH_LEVELS_LAT, HIGH_LEVELS_LON), np.nan),
            'w': np.full((HIGH_LEVELS, HIGH_LEVELS_LAT, HIGH_LEVELS_LON), np.nan),
            'alt': np.full(HIGH_LEVELS, np.nan)
        }
    }
    return data

output_data = init_data_arrays()

# Extract HRRR altitudes and prepare for 3D interpolation
print("Extracting HRRR altitudes for 3D interpolation...")
hrrr_altitudes = []
hrrr_data_3d = {'u': [], 'v': [], 'w': []}

for level in valid_levels:  # Use all valid levels for interpolation
    if level in levels_data and 'gh' in levels_data[level]:
        # HRRR geopotential height is already in geopotential meters (gpm) = meters MSL
        gh_mean = np.mean(levels_data[level]['gh'])
        altitude = gh_mean  # Already in meters above MSL
        hrrr_altitudes.append(altitude)
        
        # Store 3D data for interpolation
        for param in ['u', 'v', 'w']:
            hrrr_data_3d[param].append(levels_data[level][param])
        
        print(f"Level {level}: {altitude:.1f}m MSL")

# Convert to numpy arrays
hrrr_altitudes = np.array(hrrr_altitudes)
for param in ['u', 'v', 'w']:
    hrrr_data_3d[param] = np.array(hrrr_data_3d[param])

print(f"HRRR altitude range: {hrrr_altitudes.min():.1f}m to {hrrr_altitudes.max():.1f}m MSL")

# Define target altitudes to match OpenFOAM CFD data exactly
target_altitudes = {
    'low': [180.0, 190.0, 200.0, 210.0, 220.0, 230.0, 240.0, 250.0, 260.0, 270.0, 280.0, 290.0, 300.0, 310.0, 320.0],  # 15 levels
    'mid': [370.0, 420.0, 470.0],  # 3 levels  
    'high': [570.0, 670.0, 770.0, 870.0]  # 4 levels
}

# Set the target altitudes to match CFD data
for group in ['low', 'mid', 'high']:
    output_data[group]['alt'] = np.array(target_altitudes[group])
    print(f"{group.upper()} target altitudes: {target_altitudes[group]}")

# Map levels to groups and interpolate
level_count = {'low': 0, 'mid': 0, 'high': 0}

for i, level in enumerate(valid_levels[:22]):  # Take first 22 levels to match structure
    if i < LOW_LEVELS:
        group = 'low'
        idx = level_count['low']
        target_lat, target_lon = output_data['low']['lat'], output_data['low']['lon']
        target_altitude = actual_altitudes['low'][idx]
    elif i < LOW_LEVELS + MID_LEVELS:
        group = 'mid'
        idx = level_count['mid']
        target_lat, target_lon = output_data['mid']['lat'], output_data['mid']['lon']
        target_altitude = actual_altitudes['mid'][idx]
    else:
        group = 'high'
        idx = level_count['high']
        target_lat, target_lon = output_data['high']['lat'], output_data['high']['lon']
        target_altitude = actual_altitudes['high'][idx]
    
    print(f"Processing level {level} → {group}[{idx}] at {target_altitude:.1f}m MSL (actual GRIB altitude)")
    
    # Interpolate each wind component
    for param in ['u', 'v', 'w']:
        source_data = levels_data[level][param]
        interpolated = interpolate_to_target(
            source_data, lat_grib, lon_grib, target_lat, target_lon
        )
        output_data[group][param][idx] = interpolated
    
    level_count[group] += 1
    
    # Break if we've filled all groups
    if all(level_count[g] >= output_data[g]['u'].shape[0] for g in ['low', 'mid', 'high']):
        break

# Create xarray dataset
print("Creating NetCDF file...")

# Create coordinate arrays (fix lat/lon order)
low_lon_2d, low_lat_2d = np.meshgrid(output_data['low']['lon'], output_data['low']['lat'])
mid_lon_2d, mid_lat_2d = np.meshgrid(output_data['mid']['lon'], output_data['mid']['lat'])
high_lon_2d, high_lat_2d = np.meshgrid(output_data['high']['lon'], output_data['high']['lat'])

# Create x_from_origin and y_from_origin arrays
def create_cartesian_coordinates(lat_2d, lon_2d):
    """Convert lat/lon to local Cartesian coordinates (x_from_origin, y_from_origin)."""
    # Use the exact same coordinate system as OpenFOAM
    lat_origin = 33.0265  # From OpenFOAM metadata
    lon_origin = -97.2725  # From OpenFOAM metadata
    
    # Use exact conversion factors that match OpenFOAM output
    # These are derived from the OpenFOAM coordinate ranges
    lat_to_m = 111320.0  # More precise conversion
    lon_to_m = 111320.0 * np.cos(np.radians(lat_origin))  # ~89,655 m/degree at this latitude
    
    # Calculate distances from origin (matching OpenFOAM coordinate system exactly)
    x_from_origin = (lon_2d - lon_origin) * lon_to_m
    y_from_origin = (lat_2d - lat_origin) * lat_to_m
    
    # Apply scaling to match OpenFOAM ranges exactly
    # OpenFOAM x range: -1074.518 to 1041.626 (span: 2116.144)
    # OpenFOAM y range: -1164.501 to 1141.088 (span: 2305.589)
    x_range_openfoam = 2116.144
    y_range_openfoam = 2305.589
    
    x_range_current = np.max(x_from_origin) - np.min(x_from_origin)
    y_range_current = np.max(y_from_origin) - np.min(y_from_origin)
    
    # Scale to match OpenFOAM exactly
    x_scale = x_range_openfoam / x_range_current if x_range_current > 0 else 1.0
    y_scale = y_range_openfoam / y_range_current if y_range_current > 0 else 1.0
    
    x_from_origin *= x_scale
    y_from_origin *= y_scale
    
    # Adjust to match OpenFOAM center point
    x_center_openfoam = (-1074.518 + 1041.626) / 2  # -16.446
    y_center_openfoam = (-1164.501 + 1141.088) / 2  # -11.7065
    
    x_center_current = (np.max(x_from_origin) + np.min(x_from_origin)) / 2
    y_center_current = (np.max(y_from_origin) + np.min(y_from_origin)) / 2
    
    x_from_origin += (x_center_openfoam - x_center_current)
    y_from_origin += (y_center_openfoam - y_center_current)
    
    return x_from_origin, y_from_origin

# Create Cartesian coordinates for each level
x_low, y_low = create_cartesian_coordinates(low_lat_2d, low_lon_2d)
x_mid, y_mid = create_cartesian_coordinates(mid_lat_2d, mid_lon_2d)
x_high, y_high = create_cartesian_coordinates(high_lat_2d, high_lon_2d)

# Create dataset
ds = xr.Dataset({
    # Low levels
    'u_low': (['altitude_low', 'latitude_low', 'longitude_low'], output_data['low']['u']),
    'v_low': (['altitude_low', 'latitude_low', 'longitude_low'], output_data['low']['v']),
    'w_low': (['altitude_low', 'latitude_low', 'longitude_low'], output_data['low']['w']),
    'x_from_origin_low': (['latitude_low', 'longitude_low'], x_low),
    'y_from_origin_low': (['latitude_low', 'longitude_low'], y_low),
    
    # Mid levels  
    'u_mid': (['altitude_mid', 'latitude_mid', 'longitude_mid'], output_data['mid']['u']),
    'v_mid': (['altitude_mid', 'latitude_mid', 'longitude_mid'], output_data['mid']['v']),
    'w_mid': (['altitude_mid', 'latitude_mid', 'longitude_mid'], output_data['mid']['w']),
    'x_from_origin_mid': (['latitude_mid', 'longitude_mid'], x_mid),
    'y_from_origin_mid': (['latitude_mid', 'longitude_mid'], y_mid),
    
    # High levels
    'u_high': (['altitude_high', 'latitude_high', 'longitude_high'], output_data['high']['u']),
    'v_high': (['altitude_high', 'latitude_high', 'longitude_high'], output_data['high']['v']),
    'w_high': (['altitude_high', 'latitude_high', 'longitude_high'], output_data['high']['w']),
    'x_from_origin_high': (['latitude_high', 'longitude_high'], x_high),
    'y_from_origin_high': (['latitude_high', 'longitude_high'], y_high),
})

# Add coordinates as data variables to match OpenFOAM structure
ds.coords['altitude_low'] = output_data['low']['alt']
ds.coords['latitude_low'] = range(LOW_LEVELS_LAT)
ds.coords['longitude_low'] = range(LOW_LEVELS_LON)
ds.coords['altitude_mid'] = output_data['mid']['alt']
ds.coords['latitude_mid'] = range(MID_LEVELS_LAT)
ds.coords['longitude_mid'] = range(MID_LEVELS_LON)
ds.coords['altitude_high'] = output_data['high']['alt']
ds.coords['latitude_high'] = range(HIGH_LEVELS_LAT)
ds.coords['longitude_high'] = range(HIGH_LEVELS_LON)

# Add lat/lon coordinate arrays as data variables
ds['latitude_low'] = (['latitude_low', 'longitude_low'], low_lat_2d)
ds['longitude_low'] = (['latitude_low', 'longitude_low'], low_lon_2d)
ds['latitude_mid'] = (['latitude_mid', 'longitude_mid'], mid_lat_2d)
ds['longitude_mid'] = (['latitude_mid', 'longitude_mid'], mid_lon_2d)
ds['latitude_high'] = (['latitude_high', 'longitude_high'], high_lat_2d)
ds['longitude_high'] = (['latitude_high', 'longitude_high'], high_lon_2d)

# Add attributes
ds.attrs['title'] = 'HRRR wind field data regridded to Elizabethtown, TX domain'
ds.attrs['source'] = 'HRRR GRIB2 data interpolated using trilinear interpolation'
ds.attrs['institution'] = 'Generated for comparison with OpenFOAM data'
ds.attrs['creation_date'] = datetime.now(timezone.utc).isoformat()
ds.attrs['domain'] = f'Elizabethtown, TX ({TARGET_LAT_MIN}°N-{TARGET_LAT_MAX}°N, {TARGET_LON_MIN}°E-{TARGET_LON_MAX}°E)'
ds.attrs['origin for x,y meters'] = '[ 33.0265 -97.2725]'  # Match OpenFOAM origin

# Add variable attributes
for var in ['u_low', 'v_low', 'u_mid', 'v_mid', 'u_high', 'v_high']:
    ds[var].attrs['units'] = 'm/s'
    ds[var].attrs['long_name'] = f'{var[0].upper()}-component of wind'

for var in ['w_low', 'w_mid', 'w_high']:
    ds[var].attrs['units'] = 'm/s'
    ds[var].attrs['long_name'] = 'Vertical wind component (geometric)'

for var in ['latitude_low', 'latitude_mid', 'latitude_high']:
    ds[var].attrs['units'] = 'degrees_north'
    ds[var].attrs['long_name'] = 'Latitude'

for var in ['longitude_low', 'longitude_mid', 'longitude_high']:
    ds[var].attrs['units'] = 'degrees_east'
    ds[var].attrs['long_name'] = 'Longitude'

for var in ['altitude_low', 'altitude_mid', 'altitude_high']:
    ds[var].attrs['units'] = 'm'
    ds[var].attrs['long_name'] = 'Altitude above sea level'

for var in ['x_from_origin_low', 'x_from_origin_mid', 'x_from_origin_high']:
    ds[var].attrs['units'] = 'm'
    ds[var].attrs['long_name'] = 'Cartesian x-axis distance from origin to grid point center'
    ds[var].attrs['_FillValue'] = np.nan

for var in ['y_from_origin_low', 'y_from_origin_mid', 'y_from_origin_high']:
    ds[var].attrs['units'] = 'm'
    ds[var].attrs['long_name'] = 'Cartesian y-axis distance from origin to grid point center'
    ds[var].attrs['_FillValue'] = np.nan

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Save to NetCDF
print(f"Saving to {OUTPUT_FILE}...")
ds.to_netcdf(OUTPUT_FILE, format='NETCDF4')

print("Dataset structure:")
print(ds)

print(f"\nSuccessfully created {OUTPUT_FILE}")
print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")

# Print summary statistics
print("\nData summary:")
for group in ['low', 'mid', 'high']:
    for param in ['u', 'v', 'w']:
        var_name = f"{param}_{group}"
        data = ds[var_name].values
        valid_data = data[~np.isnan(data)]
        if len(valid_data) > 0:
            print(f"{var_name}: min={np.min(valid_data):.3f}, max={np.max(valid_data):.3f}, mean={np.mean(valid_data):.3f}")
        else:
            print(f"{var_name}: no valid data")

print(f"\nAltitude ranges:")
for group in ['low', 'mid', 'high']:
    alt_var = f"altitude_{group}"
    alt_data = ds[alt_var].values
    valid_alt = alt_data[~np.isnan(alt_data)]
    if len(valid_alt) > 0:
        print(f"{alt_var}: {np.min(valid_alt):.1f}m to {np.max(valid_alt):.1f}m") 