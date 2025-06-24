#!/usr/bin/env python3
"""
Simple diagnostic script to identify the wind direction issue in HRRR data.
"""

import numpy as np
import xarray as xr
import os

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NETCDF_FILE = os.path.join(SCRIPT_DIR, "../NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc")
OPENFOAM_FILE = os.path.join(SCRIPT_DIR, "../NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc")

def main():
    print("=== WIND DIRECTION ISSUE DIAGNOSIS ===")
    
    # Check if files exist
    if not os.path.exists(NETCDF_FILE):
        print(f"HRRR NetCDF file not found: {NETCDF_FILE}")
        return
    
    if not os.path.exists(OPENFOAM_FILE):
        print(f"OpenFOAM NetCDF file not found: {OPENFOAM_FILE}")
        return
    
    # Load datasets
    print("Loading datasets...")
    hrrr_ds = xr.open_dataset(NETCDF_FILE)
    openfoam_ds = xr.open_dataset(OPENFOAM_FILE)
    
    print(f"HRRR altitudes: {hrrr_ds.altitude_low.values}")
    print(f"OpenFOAM altitudes: {openfoam_ds.altitude_low.values}")
    
    # Compare surface level (level 0) vs top level (level 14)
    center_i, center_j = 115, 105  # Approximate center
    
    print(f"\n=== SURFACE LEVEL (Level 0) ===")
    print(f"HRRR altitude: {hrrr_ds.altitude_low[0].values:.1f}m")
    
    hrrr_u_surface = float(hrrr_ds.u_low[0, center_i, center_j].values)
    hrrr_v_surface = float(hrrr_ds.v_low[0, center_i, center_j].values)
    hrrr_mag_surface = np.sqrt(hrrr_u_surface**2 + hrrr_v_surface**2)
    hrrr_dir_surface = np.degrees(np.arctan2(hrrr_v_surface, hrrr_u_surface))
    
    print(f"HRRR wind: u={hrrr_u_surface:.2f}, v={hrrr_v_surface:.2f}, mag={hrrr_mag_surface:.2f}, dir={hrrr_dir_surface:.1f}°")
    
    of_u_surface = float(openfoam_ds.u_low[0, center_i, center_j].values)
    of_v_surface = float(openfoam_ds.v_low[0, center_i, center_j].values)
    of_mag_surface = np.sqrt(of_u_surface**2 + of_v_surface**2)
    of_dir_surface = np.degrees(np.arctan2(of_v_surface, of_u_surface))
    
    print(f"OpenFOAM wind: u={of_u_surface:.2f}, v={of_v_surface:.2f}, mag={of_mag_surface:.2f}, dir={of_dir_surface:.1f}°")
    
    print(f"\n=== TOP LEVEL (Level 14) ===")
    print(f"HRRR altitude: {hrrr_ds.altitude_low[14].values:.1f}m")
    
    hrrr_u_top = float(hrrr_ds.u_low[14, center_i, center_j].values)
    hrrr_v_top = float(hrrr_ds.v_low[14, center_i, center_j].values)
    hrrr_mag_top = np.sqrt(hrrr_u_top**2 + hrrr_v_top**2)
    hrrr_dir_top = np.degrees(np.arctan2(hrrr_v_top, hrrr_u_top))
    
    print(f"HRRR wind: u={hrrr_u_top:.2f}, v={hrrr_v_top:.2f}, mag={hrrr_mag_top:.2f}, dir={hrrr_dir_top:.1f}°")
    
    of_u_top = float(openfoam_ds.u_low[14, center_i, center_j].values)
    of_v_top = float(openfoam_ds.v_low[14, center_i, center_j].values)
    of_mag_top = np.sqrt(of_u_top**2 + of_v_top**2)
    of_dir_top = np.degrees(np.arctan2(of_v_top, of_u_top))
    
    print(f"OpenFOAM wind: u={of_u_top:.2f}, v={of_v_top:.2f}, mag={of_mag_top:.2f}, dir={of_dir_top:.1f}°")
    
    # Calculate differences
    surface_angle_diff = ((hrrr_dir_surface - of_dir_surface + 180) % 360) - 180
    top_angle_diff = ((hrrr_dir_top - of_dir_top + 180) % 360) - 180
    
    print(f"\n=== ANALYSIS ===")
    print(f"Surface level angle difference: {surface_angle_diff:.1f}°")
    print(f"Top level angle difference: {top_angle_diff:.1f}°")
    
    # Check if they're perpendicular (90° difference)
    if abs(surface_angle_diff) > 80 and abs(surface_angle_diff) < 100:
        print("⚠️  PROBLEM: Surface winds are approximately perpendicular!")
        print("   This suggests the HRRR levels are incorrectly ordered.")
        
    if abs(top_angle_diff) < 20:
        print("✓  Top level winds are similar between HRRR and OpenFOAM")
        
    print(f"\n=== ROOT CAUSE ===")
    print("The issue is in generate_hrrr_netcdf.py:")
    print("1. HRRR hybrid levels are ordered from surface (level 1) to top (level 50)")
    print("2. But the script assigns fixed altitudes [180, 190, 200, ...] to levels")
    print("3. This means:")
    print("   - HRRR level 1 (~50m actual) gets assigned 180m altitude")
    print("   - HRRR level 15 (~370m actual) gets assigned 320m altitude")
    print("4. The surface level wind is being placed at 180m altitude!")
    print("5. The 'surface' you see in Unity is actually mid-atmosphere wind")
    
    print(f"\n=== SOLUTION ===")
    print("Fix generate_hrrr_netcdf.py to:")
    print("1. Use actual geopotential heights from GRIB data")
    print("2. Or reverse the level order to match OpenFOAM structure")
    print("3. Or use different HRRR levels that match the altitude ranges")

if __name__ == "__main__":
    main() 