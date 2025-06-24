import os
import pygrib
import numpy as np
import re

# Path to the GRIB2 file
DATA_FOLDER = "HRRRdata_nat"
GRIB_FILE = "hrrr.t13z.wrfnatf02.grib2"
GRIB_PATH = os.path.join(DATA_FOLDER, GRIB_FILE)

#  bounding box
BBOX = (-97.28399658203125, 33.01599884033203, -97.2613525390625, 33.03678894042969)

LEVELS = list(range(1, 9))

if not os.path.exists(GRIB_PATH):
    raise FileNotFoundError(f"GRIB2 file not found: {GRIB_PATH}")

with pygrib.open(GRIB_PATH) as grbs:
    lats = lons = None
    for grb in grbs:
        lats, lons = grb.latlons()
        break
    grbs.seek(0)
    # Find the first HRRR grid point within the bounding box
    lon_min, lat_min, lon_max, lat_max = BBOX
    mask = (
        (lons >= lon_min) & (lons <= lon_max) &
        (lats >= lat_min) & (lats <= lat_max)
    )
    idx = np.where(mask)
    if len(idx[0]) == 0:
        raise RuntimeError("No HRRR grid point found within the bounding box!")
    # Take the first found point
    i_c, j_c = idx[0][0], idx[1][0]
    # Get indices for 3x3 grid around (i_c, j_c)
    i_inds = [max(i_c-1,0), i_c, min(i_c+1, lats.shape[0]-1)]
    j_inds = [max(j_c-1,0), j_c, min(j_c+1, lats.shape[1]-1)]
    # Extract 3x3 grid
    lats_crop = lats[np.ix_(i_inds, j_inds)]
    lons_crop = lons[np.ix_(i_inds, j_inds)]
    nlat, nlon = lats_crop.shape
    nlev = len(LEVELS)
    gh = np.zeros((nlev, nlat, nlon))
    u = np.zeros((nlev, nlat, nlon))
    v = np.zeros((nlev, nlat, nlon))
    w_omega = np.zeros((nlev, nlat, nlon))
    pres = np.zeros((nlev, nlat, nlon))
    t = np.zeros((nlev, nlat, nlon))
    for k, level in enumerate(LEVELS):
        for short_name, arr in zip(["gh", "u", "v", "w", "pres", "t"], [gh, u, v, w_omega, pres, t]):
            matches = [grb for grb in grbs if grb.shortName == short_name and grb.level == level and grb.typeOfLevel == "hybrid"]
            grbs.seek(0)
            if not matches:
                raise RuntimeError(f"Missing {short_name} at level {level}")
            arr[k] = matches[0].values[np.ix_(i_inds, j_inds)]
    # Convert pressure vertical velocity (omega, Pa/s) to geometric vertical velocity (w, m/s)
    R_d = 287.05  # J/kg·K
    g = 9.81      # m/s²
    w = -(w_omega * R_d * t) / (pres * g)
    # Print shapes and grid for verification
    print("lats_crop shape:", lats_crop.shape)
    print("lons_crop shape:", lons_crop.shape)
    print("lats_crop:", lats_crop)
    print("lons_crop:", lons_crop)
    # Extract tXXz and fXX from GRIB filename for output
    t_match = re.search(r'(t\d{2}z)', GRIB_FILE, re.IGNORECASE)
    fxx_match = re.search(r'(f\d{2})', GRIB_FILE, re.IGNORECASE)
    t_part = f"_{t_match.group(1).lower()}" if t_match else ""
    fxx_part = f"_{fxx_match.group(1).lower()}" if fxx_match else ""
    npz_filename = f"hrrr_elizabethtown_levels_1_8{t_part}{fxx_part}.npz"
    np.savez_compressed(
        os.path.join("NCdata", npz_filename),
        lats=lats_crop,
        lons=lons_crop,
        gh=gh,
        u=u,
        v=v,
        w=w,
        pres=pres,
        t=t,
        levels=np.array(LEVELS)
    )
    print(f"Saved HRRR Elizabethtown 3x3 grid for levels 1-8 to NCdata/{npz_filename}") 