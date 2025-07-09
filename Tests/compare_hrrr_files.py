import netCDF4 as nc
import numpy as np
import os
from pathlib import Path

def compare_variables(ds1, ds2, file1_name, file2_name):
    """Compare variables between two datasets"""
    vars1 = set(ds1.variables.keys())
    vars2 = set(ds2.variables.keys())
    
    print("\n=== Variable Comparison ===")
    print(f"Variables only in {file1_name}:", vars1 - vars2)
    print(f"Variables only in {file2_name}:", vars2 - vars1)
    print("Common variables:", vars1.intersection(vars2))
    
    return vars1.intersection(vars2)

def compare_dimensions(ds1, ds2, file1_name, file2_name):
    """Compare dimensions between two datasets"""
    dims1 = {dim: len(ds1.dimensions[dim]) for dim in ds1.dimensions}
    dims2 = {dim: len(ds2.dimensions[dim]) for dim in ds2.dimensions}
    
    print("\n=== Dimension Comparison ===")
    print(f"Dimensions in {file1_name}:", dims1)
    print(f"Dimensions in {file2_name}:", dims2)
    
    # Compare common dimensions
    common_dims = set(dims1.keys()).intersection(set(dims2.keys()))
    mismatched_dims = []
    for dim in common_dims:
        if dims1[dim] != dims2[dim]:
            mismatched_dims.append((dim, dims1[dim], dims2[dim]))
    
    if mismatched_dims:
        print("\nMismatched dimensions:")
        for dim, size1, size2 in mismatched_dims:
            print(f"  {dim}: {size1} vs {size2}")

def format_float(value):
    """Format float with 6 decimal places"""
    if isinstance(value, (float, np.float32, np.float64)):
        return f"{value:.6f}"
    return str(value)

def compare_variable_data(ds1, ds2, var_name):
    """Compare data for a specific variable between two datasets"""
    var1 = ds1.variables[var_name][:]
    var2 = ds2.variables[var_name][:]
    
    if var1.shape != var2.shape:
        print(f"\n{var_name}: Shape mismatch - {var1.shape} vs {var2.shape}")
        return
    
    # Handle masked arrays
    if hasattr(var1, 'mask'):
        var1 = var1.filled(np.nan)
    if hasattr(var2, 'mask'):
        var2 = var2.filled(np.nan)
    
    # Compare data
    diff = var1 - var2
    abs_diff = np.abs(diff)
    
    # Handle potential NaN values
    valid_mask = ~np.isnan(diff)
    if np.any(valid_mask):
        max_diff = np.max(abs_diff[valid_mask])
        mean_diff = np.mean(abs_diff[valid_mask])
        std_diff = np.std(abs_diff[valid_mask])
        
        print(f"\n{var_name} differences:")
        print(f"  Max absolute difference: {format_float(max_diff)}")
        print(f"  Mean absolute difference: {format_float(mean_diff)}")
        print(f"  Std of absolute difference: {format_float(std_diff)}")
        
        # Count elements with significant differences
        threshold = 1e-10  # Adjust this threshold as needed
        significant_diffs = np.sum(abs_diff > threshold)
        if significant_diffs > 0:
            print(f"  Number of elements with differences > {threshold}: {significant_diffs}")
            
            # Print some example differences if there are significant ones
            if significant_diffs > 0:
                # Find indices of largest differences
                flat_indices = np.argsort(abs_diff.ravel())[-5:]  # Get indices of 5 largest differences
                print("\n  Top 5 largest differences:")
                for idx in reversed(flat_indices):
                    # Convert flat index to multi-dimensional index
                    multi_idx = np.unravel_index(idx, abs_diff.shape)
                    print(f"    At index {multi_idx}:")
                    print(f"      File1: {format_float(var1[multi_idx])}")
                    print(f"      File2: {format_float(var2[multi_idx])}")
                    print(f"      Diff:  {format_float(diff[multi_idx])}")
    else:
        print(f"\n{var_name}: All elements are NaN in the difference")

def compare_attribute_values(val1, val2):
    """Compare two attribute values, handling numpy arrays properly"""
    if isinstance(val1, np.ndarray) or isinstance(val2, np.ndarray):
        val1_arr = np.array(val1)
        val2_arr = np.array(val2)
        if val1_arr.shape != val2_arr.shape:
            return True
        return not np.array_equal(val1_arr, val2_arr)
    return val1 != val2

def main():
    # Define file paths
    base_dir = Path(__file__).parent.parent / 'NCdata'
    file1 = base_dir / 'hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc'
    file2 = base_dir / 'hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min__.nc'
    
    print(f"Comparing files:")
    print(f"File 1: {file1}")
    print(f"File 2: {file2}")
    
    # Check if files exist
    if not file1.exists():
        print(f"Error: {file1} does not exist")
        return
    if not file2.exists():
        print(f"Error: {file2} does not exist")
        return
    
    # Open both files
    with nc.Dataset(file1) as ds1, nc.Dataset(file2) as ds2:
        # Compare global attributes
        print("\n=== Global Attributes Comparison ===")
        attrs1 = set(ds1.ncattrs())
        attrs2 = set(ds2.ncattrs())
        print("Attributes only in file1:", attrs1 - attrs2)
        print("Attributes only in file2:", attrs2 - attrs1)
        
        # Compare common attributes
        common_attrs = attrs1.intersection(attrs2)
        print("\nCommon attributes with different values:")
        for attr in common_attrs:
            val1 = getattr(ds1, attr)
            val2 = getattr(ds2, attr)
            if compare_attribute_values(val1, val2):
                print(f"  {attr}:")
                print(f"    File1: {format_float(val1)}")
                print(f"    File2: {format_float(val2)}")
        
        # Compare variables and their data
        common_vars = compare_variables(ds1, ds2, file1.name, file2.name)
        compare_dimensions(ds1, ds2, file1.name, file2.name)
        
        print("\n=== Data Comparison ===")
        for var_name in common_vars:
            compare_variable_data(ds1, ds2, var_name)

if __name__ == "__main__":
    main() 