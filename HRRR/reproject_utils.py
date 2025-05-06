import numpy as np
import rasterio
from rasterio.transform import from_bounds 
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS

def reproject_to_web_mercator(data_array, lats, lons, resampling=Resampling.nearest):
    """
    Reprojects a 2D NumPy array (data_array) from its given lat/lon arrays
    (in degrees) to Web Mercator (EPSG:3857).

    Parameters:
        data_array : 2D numpy array of your parameter values, shape = (ny, nx)
        lats, lons : 2D arrays of same shape as data_array, storing each pixel's latitude & longitude
        resampling : Rasterio's Resampling enum (nearest, bilinear, etc.)

    Returns:
        reprojected_data : 2D numpy array in Web Mercator projection
        dst_transform    : The affine transform of the output data
        dst_crs          : The CRS (Web Mercator)
    """

    # 1) Source CRS (we assume lat/lon in degrees => EPSG:4326)
    src_crs = CRS.from_epsg(4326)

    # 2) Destination CRS: Web Mercator
    dst_crs = CRS.from_epsg(3857)#.from_string("+proj=merc +a=6378137 +b=6378137")  # or from_epsg(3857)

    # Dimensions
    ny, nx = data_array.shape

    # Compute approximate bounding box in degrees
    lat_min, lat_max = lats.min(), lats.max()
    lon_min, lon_max = lons.min(), lons.max()

   

    # Build an affine transform for the *source* in lat/lon
    # top-left corner is (lon_min, lat_max),
    # each pixel is roughly ( (lon_max - lon_min)/nx, (lat_min - lat_max)/ny )
    src_transform = from_bounds(lon_min, lat_min, lon_max, lat_max, width=nx, height=ny)

    # Prepare a rasterio-like profile for the source data in memory
    src_profile = {
        "driver": "GTiff",
        "height": ny,
        "width": nx,
        "count": 1,
        "dtype": str(data_array.dtype),
        "crs": src_crs,
        "transform": src_transform,
    }

    # 3) Use rasterio to calculate the default transform for the destination
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs, dst_crs, nx, ny, *[lon_min, lat_min, lon_max, lat_max]
    )

    # 4) Allocate array for the destination
    reprojected_data = np.zeros((dst_height, dst_width), dtype=data_array.dtype)

    # 5) Perform the reprojection
    reproject(
        source=data_array,
        destination=reprojected_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=resampling
    )

    return reprojected_data, dst_transform, dst_crs
