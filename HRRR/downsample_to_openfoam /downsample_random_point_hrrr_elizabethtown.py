import numpy as np
import random

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