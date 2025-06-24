import numpy as np
import random
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
import os

DATA_FILE = "NCdata/hrrr_elizabethtown_levels_1_8_t13z_f02.npz"
data = np.load(DATA_FILE)
lats = data['lats']  # 2D
lons = data['lons']  # 2D
gh = data['gh']      # 3D: (level, lat, lon)
u = data['u']
v = data['v']
w = data['w']
pres = data['pres']
t = data['t']
levels = data['levels']

nlev, nlat, nlon = gh.shape

# Generate a random (lat, lon, gh) within the bounding box and gh range
rand_lat = random.uniform(lats.min(), lats.max())
rand_lon = random.uniform(lons.min(), lons.max())
rand_gh = random.uniform(0, 870)
print(f"Random point: lat={rand_lat:.4f}, lon={rand_lon:.4f}, gh={rand_gh:.4f}")

# Find bracketing indices in each dimension
lat_diffs = np.abs(lats - rand_lat)
lon_diffs = np.abs(lons - rand_lon)
flat_idx = np.argmin(lat_diffs + lon_diffs)
i_c, j_c = np.unravel_index(flat_idx, lats.shape)
# Find i0/i1, j0/j1
if lats[i_c, j_c] < rand_lat:
    i0, i1 = i_c, min(i_c+1, nlat-1)
else:
    i0, i1 = max(i_c-1, 0), i_c
if lons[i_c, j_c] < rand_lon:
    j0, j1 = j_c, min(j_c+1, nlon-1)
else:
    j0, j1 = max(j_c-1, 0), j_c
# For gh, find k0/k1
gh_profile = gh[:, i_c, j_c]
k_c = np.argmin(np.abs(gh_profile - rand_gh))
if gh_profile[k_c] < rand_gh:
    k0, k1 = k_c, min(k_c+1, nlev-1)
else:
    k0, k1 = max(k_c-1, 0), k_c

# Check if rand_gh is within the range of gh_profile
if rand_gh < np.min(gh_profile) or rand_gh > np.max(gh_profile):
    print(f"Warning: rand_gh={rand_gh:.4f} is outside the range of gh_profile [{np.min(gh_profile):.4f}, {np.max(gh_profile):.4f}]. Returning np.nan for all interpolated values.")
    u_interp = v_interp = w_interp = pres_interp = t_interp = np.nan
else:
    # Gather the 8 corners
    corners = []
    for kk in [k0, k1]:
        for ii in [i0, i1]:
            for jj in [j0, j1]:
                corners.append({
                    'lat': lats[ii, jj],
                    'lon': lons[ii, jj],
                    'gh': gh[kk, ii, jj],
                    'u': u[kk, ii, jj],
                    'v': v[kk, ii, jj],
                    'w': w[kk, ii, jj],
                    'pres': pres[kk, ii, jj],
                    't': t[kk, ii, jj],
                    'k': kk, 'i': ii, 'j': jj
                })
    print("8 corner points (k,i,j): lat, lon, gh, u, v, w, pres, t:")
    for c in corners:
        print(f"({c['k']},{c['i']},{c['j']}): {c['lat']:.4f}, {c['lon']:.4f}, {c['gh']:.4f}, {c['u']:.4f}, {c['v']:.4f}, {c['w']:.4f}, {c['pres']:.2f}, {c['t']:.2f}")

    # Trilinear interpolation
    gh0 = gh[k0, i0, j0]
    gh1 = gh[k1, i0, j0]
    lat0 = lats[i0, j0]
    lat1 = lats[i1, j0]
    lon0 = lons[i0, j0]
    lon1 = lons[i0, j1]
    def interp_weight(x, x0, x1):
        if x1 == x0:
            return 0.0
        return (x - x0) / (x1 - x0)
    wx = interp_weight(rand_lon, lon0, lon1)
    wy = interp_weight(rand_lat, lat0, lat1)
    wz = interp_weight(rand_gh, gh0, gh1)
    def trilinear(arr):
        return (
            arr[0,0,0]*(1-wx)*(1-wy)*(1-wz) +
            arr[0,0,1]*wx*(1-wy)*(1-wz) +
            arr[0,1,0]*(1-wx)*wy*(1-wz) +
            arr[0,1,1]*wx*wy*(1-wz) +
            arr[1,0,0]*(1-wx)*(1-wy)*wz +
            arr[1,0,1]*wx*(1-wy)*wz +
            arr[1,1,0]*(1-wx)*wy*wz +
            arr[1,1,1]*wx*wy*wz
        )
    def get_cube(field_stack):
        return np.array([
            [
                [field_stack[k0, i0, j0], field_stack[k0, i0, j1]],
                [field_stack[k0, i1, j0], field_stack[k0, i1, j1]]
            ],
            [
                [field_stack[k1, i0, j0], field_stack[k1, i0, j1]],
                [field_stack[k1, i1, j0], field_stack[k1, i1, j1]]
            ]
        ])
    u_interp = trilinear(get_cube(u))
    v_interp = trilinear(get_cube(v))
    w_interp = trilinear(get_cube(w))
    pres_interp = trilinear(get_cube(pres))
    t_interp = trilinear(get_cube(t))

print(f"\nTrilinear interpolated values at random point:")
print(f"u = {u_interp}, v = {v_interp}, w = {w_interp}, pres = {pres_interp}, t = {t_interp}")

# OpenFOAM grid parameters
GROUPS = {
    'low':  {'levels': 15,  'lat': 231, 'lon': 211},
    'mid':  {'levels': 3,  'lat': 47,  'lon': 43},
    'high': {'levels': 4,  'lat': 24,  'lon': 22},
}

# Bounding box from OpenFOAM attributes (from inspect script)
LAT_MIN = 33.01599884042969
LAT_MAX = 33.03678894042969
LON_MIN = -97.28399658203125
LON_MAX = -97.2613525390625

# Altitude ranges (from OpenFOAM summaries)
ALTITUDES = {
    'low':  np.linspace(180, 320, GROUPS['low']['levels']),
    'mid':  np.linspace(370, 470, GROUPS['mid']['levels']),
    'high': np.linspace(570, 870, GROUPS['high']['levels']),
}

def find_bracketing_indices(arr, val):
    idx = np.searchsorted(arr, val)
    if idx == 0:
        return 0, 1
    elif idx >= len(arr):
        return len(arr)-2, len(arr)-1
    else:
        return idx-1, idx

def trilinear_interp(lats, lons, gh, field, lat_pt, lon_pt, gh_pt):
    # Find nearest indices in lat/lon
    lat_vals = lats[:,0]
    lon_vals = lons[0,:]
    if not (lat_vals[0] <= lat_pt <= lat_vals[-1]) or not (lon_vals[0] <= lon_pt <= lon_vals[-1]):
        return np.nan
    i0, i1 = find_bracketing_indices(lat_vals, lat_pt)
    j0, j1 = find_bracketing_indices(lon_vals, lon_pt)
    # For gh, use the vertical profile at (i_c, j_c) closest to (lat_pt, lon_pt)
    i_c = np.argmin(np.abs(lat_vals - lat_pt))
    j_c = np.argmin(np.abs(lon_vals - lon_pt))
    gh_profile = gh[:, i_c, j_c]
    if not (np.nanmin(gh_profile) <= gh_pt <= np.nanmax(gh_profile)):
        return np.nan
    k_c = np.argmin(np.abs(gh_profile - gh_pt))
    if gh_profile[k_c] < gh_pt:
        k0, k1 = k_c, min(k_c+1, gh.shape[0]-1)
    else:
        k0, k1 = max(k_c-1, 0), k_c
    # Get 8 corners
    def get_cube(arr):
        return np.array([
            [
                [arr[k0, i0, j0], arr[k0, i0, j1]],
                [arr[k0, i1, j0], arr[k0, i1, j1]]
            ],
            [
                [arr[k1, i0, j0], arr[k1, i0, j1]],
                [arr[k1, i1, j0], arr[k1, i1, j1]]
            ]
        ])
    gh0 = gh[k0, i0, j0]
    gh1 = gh[k1, i0, j0]
    lat0 = lats[i0, j0]
    lat1 = lats[i1, j0]
    lon0 = lons[i0, j0]
    lon1 = lons[i0, j1]
    def interp_weight(x, x0, x1):
        if x1 == x0:
            return 0.0
        return (x - x0) / (x1 - x0)
    wx = interp_weight(lon_pt, lon0, lon1)
    wy = interp_weight(lat_pt, lat0, lat1)
    wz = interp_weight(gh_pt, gh0, gh1)
    cube = get_cube(field)
    return (
        cube[0,0,0]*(1-wx)*(1-wy)*(1-wz) +
        cube[0,0,1]*wx*(1-wy)*(1-wz) +
        cube[0,1,0]*(1-wx)*wy*(1-wz) +
        cube[0,1,1]*wx*wy*(1-wz) +
        cube[1,0,0]*(1-wx)*(1-wy)*wz +
        cube[1,0,1]*wx*(1-wy)*wz +
        cube[1,1,0]*(1-wx)*wy*wz +
        cube[1,1,1]*wx*wy*wz
    )

# Prepare output data
output = {}
for group, params in GROUPS.items():
    lat_grid = np.linspace(LAT_MIN, LAT_MAX, params['lat'])
    lon_grid = np.linspace(LON_MIN, LON_MAX, params['lon'])
    alt_grid = ALTITUDES[group]  # These are the OpenFOAM altitudes for this group (length = OpenFOAM nlev)
    output[group] = {
        'lat': lat_grid,
        'lon': lon_grid,
        'alt': alt_grid,
        'u': np.full((len(alt_grid), len(lat_grid), len(lon_grid)), np.nan),
        'v': np.full((len(alt_grid), len(lat_grid), len(lon_grid)), np.nan),
        'w': np.full((len(alt_grid), len(lat_grid), len(lon_grid)), np.nan),
    }
    for k, gh_pt in enumerate(alt_grid):
        for i, lat_pt in enumerate(lat_grid):
            for j, lon_pt in enumerate(lon_grid):
                output[group]['u'][k,i,j] = trilinear_interp(lats, lons, gh, u, lat_pt, lon_pt, gh_pt)
                output[group]['v'][k,i,j] = trilinear_interp(lats, lons, gh, v, lat_pt, lon_pt, gh_pt)
                output[group]['w'][k,i,j] = trilinear_interp(lats, lons, gh, w, lat_pt, lon_pt, gh_pt)

# Create xarray Dataset with OpenFOAM-matching structure
coords = {}
data_vars = {}
for group, params in GROUPS.items():
    coords[f'latitude_{group}'] = ('latitude_' + group, output[group]['lat'])
    coords[f'longitude_{group}'] = ('longitude_' + group, output[group]['lon'])
    coords[f'altitude_{group}'] = ('altitude_' + group, output[group]['alt'])
    data_vars[f'u_{group}'] = (['altitude_' + group, 'latitude_' + group, 'longitude_' + group], output[group]['u'])
    data_vars[f'v_{group}'] = (['altitude_' + group, 'latitude_' + group, 'longitude_' + group], output[group]['v'])
    data_vars[f'w_{group}'] = (['altitude_' + group, 'latitude_' + group, 'longitude_' + group], output[group]['w'])

# Build dataset
xr_ds = xr.Dataset(data_vars, coords=coords)

# Add units and attributes
for group in GROUPS:
    for var in ['u', 'v', 'w']:
        xr_ds[f'{var}_{group}'].attrs['units'] = 'm/s'
    xr_ds[f'latitude_{group}'].attrs['units'] = 'degrees_north'
    xr_ds[f'longitude_{group}'].attrs['units'] = 'degrees_east'
    xr_ds[f'altitude_{group}'].attrs['units'] = 'm'
xr_ds.attrs['title'] = 'HRRR wind field data regridded to Elizabethtown, TX domain (OpenFOAM grid)'
xr_ds.attrs['source'] = 'HRRR .npz data interpolated to OpenFOAM grid'

# Output path
output_nc = 'NCdata/hrrr-regrid_usa-tx-elizabethtown_2023-02-14T15-00-00_f0hr0min.nc'
os.makedirs(os.path.dirname(output_nc), exist_ok=True)
xr_ds.to_netcdf(output_nc, format='NETCDF4')
print(f"NetCDF file written: {output_nc}")

print("HRRR lats: min=%.6f, max=%.6f" % (lats.min(), lats.max()))
print("HRRR lons: min=%.6f, max=%.6f" % (lons.min(), lons.max()))
for param, arr in zip(['u', 'v', 'w'], [u, v, w]):
    print(f"HRRR {param}: min={np.nanmin(arr):.4f}, max={np.nanmax(arr):.4f}, mean={np.nanmean(arr):.4f}")

for group, params in GROUPS.items():
    lat = np.linspace(LAT_MIN, LAT_MAX, params['lat'])
    lon = np.linspace(LON_MIN, LON_MAX, params['lon'])
    print(f"{group} group target lat: min={lat.min():.6f}, max={lat.max():.6f}")
    print(f"{group} group target lon: min={lon.min():.6f}, max={lon.max():.6f}")

# Debug: HRRR grid stats
print("\n--- HRRR GRID STATS ---")
print(f"lats shape: {lats.shape}, min={lats.min()}, max={lats.max()}")
print(f"lons shape: {lons.shape}, min={lons.min()}, max={lons.max()}")
print(f"gh shape: {gh.shape}, min={gh.min()}, max={gh.max()}")
for param, arr in zip(['u', 'v', 'w'], [u, v, w]):
    print(f"HRRR {param}: min={np.nanmin(arr):.4f}, max={np.nanmax(arr):.4f}, mean={np.nanmean(arr):.4f}, nan count={np.isnan(arr).sum()}")

# Debug: OpenFOAM grid stats
print("\n--- OPENFOAM GRID STATS ---")
for group, params in GROUPS.items():
    lat_grid = output[group]['lat']
    lon_grid = output[group]['lon']
    alt_grid = output[group]['alt']
    print(f"{group} group lat: min={lat_grid.min()}, max={lat_grid.max()}, n={len(lat_grid)}")
    print(f"{group} group lon: min={lon_grid.min()}, max={lon_grid.max()}, n={len(lon_grid)}")
    print(f"{group} group alt: min={alt_grid.min()}, max={alt_grid.max()}, n={len(alt_grid)}")

# Debug: Output nan stats after interpolation
print("\n--- OUTPUT NAN STATS ---")
for group in GROUPS:
    for param in ['u', 'v', 'w']:
        arr = output[group][param]
        total = arr.size
        n_nan = np.isnan(arr).sum()
        print(f"{group} {param}: {n_nan}/{total} ({100*n_nan/total:.2f}%) nan")

# Debug: Sample a few OpenFOAM points and print HRRR gh_profile and interp status
print("\n--- SAMPLE POINTS DEBUG ---")
sample_points = [
    ('low', 0, 0, 0),  # first point
    ('low', GROUPS['low']['levels']//2, GROUPS['low']['lat']//2, GROUPS['low']['lon']//2),  # center
    ('low', GROUPS['low']['levels']-1, GROUPS['low']['lat']-1, GROUPS['low']['lon']-1),  # last
]
for group, k, i, j in sample_points:
    lat_pt = output[group]['lat'][i]
    lon_pt = output[group]['lon'][j]
    gh_pt = output[group]['alt'][k]
    lat_vals = lats[:,0]
    lon_vals = lons[0,:]
    i_c = np.argmin(np.abs(lat_vals - lat_pt))
    j_c = np.argmin(np.abs(lon_vals - lon_pt))
    gh_profile = gh[:, i_c, j_c]
    print(f"Sample {group} (k={k},i={i},j={j}): lat={lat_pt}, lon={lon_pt}, alt={gh_pt}")
    print(f"  HRRR gh_profile: min={np.nanmin(gh_profile)}, max={np.nanmax(gh_profile)}")
    if not (np.nanmin(gh_profile) <= gh_pt <= np.nanmax(gh_profile)):
        print("  OUT OF BOUNDS: will be nan")
    else:
        print("  IN BOUNDS: should interpolate") 