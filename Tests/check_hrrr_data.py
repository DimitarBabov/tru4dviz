import netCDF4 as nc
import numpy as np

# Check HRRR data
ds = nc.Dataset('NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc')
print('HRRR data inspection:')

for level in ['low', 'mid', 'high']:
    u = ds.variables[f'u_{level}'][:]
    v = ds.variables[f'v_{level}'][:]
    w = ds.variables[f'w_{level}'][:]
    
    print(f'\n{level.upper()} level:')
    print(f'  Shape: {u.shape}')
    print(f'  Has mask: {hasattr(u, "mask")}')
    
    # Print first 20 values regardless of mask status
    print(f'  First 20 u values (raw): {u.flatten()[:20]}')
    print(f'  First 20 v values (raw): {v.flatten()[:20]}')
    print(f'  First 20 w values (raw): {w.flatten()[:20]}')
    
    if hasattr(u, 'mask'):
        valid_u = np.sum(~u.mask)
        valid_v = np.sum(~v.mask)
        valid_w = np.sum(~w.mask)
        print(f'  Valid u values: {valid_u}/{u.size}')
        print(f'  Valid v values: {valid_v}/{v.size}')
        print(f'  Valid w values: {valid_w}/{w.size}')
        
        # Print first 20 mask values
        print(f'  First 20 u mask values: {u.mask.flatten()[:20]}')
        print(f'  First 20 v mask values: {v.mask.flatten()[:20]}')
        print(f'  First 20 w mask values: {w.mask.flatten()[:20]}')
        
        if valid_u > 0:
            u_filled = u.filled(np.nan)
            print(f'  U stats: min={np.nanmin(u_filled):.3f}, max={np.nanmax(u_filled):.3f}')
    else:
        print(f'  No mask - checking for NaN values')
        nan_u = np.sum(np.isnan(u))
        print(f'  NaN u values: {nan_u}/{u.size}')
        if nan_u < u.size:
            print(f'  U stats: min={np.nanmin(u):.3f}, max={np.nanmax(u):.3f}')

ds.close()

# Also check OpenFOAM for comparison
print('\n' + '='*50)
print('OpenFOAM data inspection:')

ds = nc.Dataset('NCdata/openfoam_usa-tx-elizabethtown_2023-02-14T15-00-00.nc')

for level in ['low', 'mid', 'high']:
    u = ds.variables[f'u_{level}'][:]
    
    print(f'\n{level.upper()} level:')
    print(f'  Shape: {u.shape}')
    print(f'  Has mask: {hasattr(u, "mask")}')
    
    # Print first 20 values for comparison
    print(f'  First 20 u values (raw): {u.flatten()[:20]}')
    
    if hasattr(u, 'mask'):
        valid_u = np.sum(~u.mask)
        print(f'  Valid u values: {valid_u}/{u.size}')
        print(f'  First 10 u mask values: {u.mask.flatten()[:10]}')
        if valid_u > 0:
            u_filled = u.filled(np.nan)
            print(f'  U stats: min={np.nanmin(u_filled):.3f}, max={np.nanmax(u_filled):.3f}')
    else:
        nan_u = np.sum(np.isnan(u))
        print(f'  NaN u values: {nan_u}/{u.size}')
        if nan_u < u.size:
            print(f'  U stats: min={np.nanmin(u):.3f}, max={np.nanmax(u):.3f}')

ds.close() 