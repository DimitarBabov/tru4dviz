import xarray as xr
import numpy as np
import os
from datetime import datetime

def print_point_comparison(hrrr_ds, of_ds, diff_ds, group, lat_val, lon_val, alt_val):
    """Print comparison of wind components at a specific point."""
    print(f"\n=== Wind Components Comparison for {group} group ===")
    print(f"Location: latitude: {lat_val:.4f}, longitude: {lon_val:.4f}, altitude: {alt_val:.1f}m")
    
    # Find nearest altitude index
    alt_coords = hrrr_ds[f'altitude_{group}']
    alt_idx = np.abs(alt_coords - alt_val).argmin()
    actual_alt = float(alt_coords[alt_idx])
    
    print("\nWind Components:")
    print(f"{'Component':<10} {'HRRR':>10} {'OpenFOAM':>10} {'Difference':>10}")
    print("-" * 42)
    
    for var in ['u', 'v', 'w']:
        var_name = f'{var}_{group}'
        
        # Get values from each dataset
        hrrr_val = float(hrrr_ds[var_name].isel({f'altitude_{group}': alt_idx}).sel(
            {f'latitude_{group}': lat_val, f'longitude_{group}': lon_val},
            method='nearest'
        ).values)
        
        of_val = float(of_ds[var_name].isel({f'altitude_{group}': alt_idx}).sel(
            {f'latitude_{group}': lat_val, f'longitude_{group}': lon_val},
            method='nearest'
        ).values)
        
        diff_val = float(diff_ds[var_name].isel({f'altitude_{group}': alt_idx}).sel(
            {f'latitude_{group}': lat_val, f'longitude_{group}': lon_val},
            method='nearest'
        ).values)
        
        print(f"{var:<10} {hrrr_val:>10.4f} {of_val:>10.4f} {diff_val:>10.4f}")

def create_diff_dataset(hrrr_ds, of_ds, group):
    """Create a dataset containing differences between HRRR and OpenFOAM data for a specific group."""
    diff_data = {}
    
    # Copy coordinates and dimensions from OpenFOAM dataset
    for coord in [f'latitude_{group}', f'longitude_{group}', f'altitude_{group}',
                 f'x_from_origin_{group}', f'y_from_origin_{group}']:
        if coord in of_ds:
            diff_data[coord] = of_ds[coord].copy()
    
    # Calculate differences for u, v, w
    for var in ['u', 'v', 'w']:
        var_name = f'{var}_{group}'
        hrrr_var = hrrr_ds[var_name].values
        of_var = of_ds[var_name].values
        
        # Create difference array with same shape
        diff = np.full_like(hrrr_var, np.nan)
        
        # Calculate difference where both arrays have valid data
        valid_mask = ~np.isnan(hrrr_var) & ~np.isnan(of_var)
        diff[valid_mask] = hrrr_var[valid_mask] - of_var[valid_mask]
        
        # Create DataArray with the difference data
        diff_data[var_name] = xr.DataArray(
            data=diff,
            dims=of_ds[var_name].dims,  # Use OpenFOAM dimensions
            coords=of_ds[var_name].coords,  # Use OpenFOAM coordinates
            attrs=of_ds[var_name].attrs
        )
        
        # Update attributes specific to the difference data
        diff_data[var_name].attrs['description'] = f'Difference between HRRR and OpenFOAM {var} component (HRRR - OpenFOAM)'
        diff_data[var_name].attrs['units'] = 'm/s'
    
    return diff_data

def main():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Input file paths
    hrrr_nc = "NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc"
    of_nc = "NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc"
    
    # Check if input files exist
    if not (os.path.exists(hrrr_nc) and os.path.exists(of_nc)):
        print("Error: One or both input NetCDF files not found.")
        print(f"Looking for files:")
        print(f"  - {os.path.abspath(hrrr_nc)}")
        print(f"  - {os.path.abspath(of_nc)}")
        return
    
    # Open datasets
    hrrr_ds = xr.open_dataset(hrrr_nc)
    of_ds = xr.open_dataset(of_nc)
    
    # Extract datetime from HRRR filename for consistency
    datetime_str = "2023-02-14T15-00-00"  # From the source filename
    
    # Create output filename matching source format
    output_nc = f"NCdata/diff_hrr_cfd_usa-tx-elizabethtown_{datetime_str}.nc"
    
    # Initialize empty dictionary for all differences
    all_diff_data = {}
    
    # Process each group (low, mid, high)
    for group in ['low', 'mid', 'high']:
        print(f"\n=== Processing {group} group ===")
        
        # Calculate differences
        diff_data = create_diff_dataset(hrrr_ds, of_ds, group)
        all_diff_data.update(diff_data)
        
        # Create temporary dataset for differences
        temp_ds = xr.Dataset(diff_data)
        
        # Print comparison at specific points
        if group == 'low':
            points = [(33.0287, -97.2751, 420.0)]
        elif group == 'mid':
            points = [(33.0287, -97.2751, 600.0)]
        else:  # high
            points = [(33.0287, -97.2751, 800.0)]
            
        for lat, lon, alt in points:
            print_point_comparison(hrrr_ds, of_ds, temp_ds, group, lat, lon, alt)
    
    # Create new dataset with differences
    diff_ds = xr.Dataset(all_diff_data)
    
    # Copy global attributes from HRRR dataset
    diff_ds.attrs = hrrr_ds.attrs.copy()
    diff_ds.attrs['description'] = 'Difference between HRRR and OpenFOAM data (HRRR - OpenFOAM)'
    diff_ds.attrs['created'] = datetime_str
    diff_ds.attrs['hrrr_source'] = os.path.basename(hrrr_nc)
    diff_ds.attrs['openfoam_source'] = os.path.basename(of_nc)
    
    # Save to netCDF file
    print(f"\nSaving differences to: {output_nc}")
    diff_ds.to_netcdf(output_nc)
    
    # Close datasets
    hrrr_ds.close()
    of_ds.close()
    diff_ds.close()
    
    print("Done! Difference file created successfully.")

if __name__ == "__main__":
    main() 