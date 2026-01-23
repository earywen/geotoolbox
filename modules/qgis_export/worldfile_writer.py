"""
World File Writer for SIG Export.

Generates world files (.pgw, .jgw, .tfw) for georeferencing raster images.
A world file is a simple text file that describes the location, scale, and rotation
of a raster image in real-world coordinates.

Format (6 lines):
    Line 1: Pixel size in X direction (usually resolution in meters)
    Line 2: Rotation about Y axis (usually 0)
    Line 3: Rotation about X axis (usually 0)
    Line 4: Pixel size in Y direction (usually negative)
    Line 5: X coordinate of upper-left pixel center
    Line 6: Y coordinate of upper-left pixel center
"""

import os
import math
import logging
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)

# EPSG codes
EPSG_WGS84 = 4326
EPSG_WEB_MERCATOR = 3857
EPSG_RGF93 = 2154  # Lambert-93 France


def wgs84_to_web_mercator(lat: float, lon: float) -> Tuple[float, float]:
    """
    Convert WGS84 (lat/lon) to Web Mercator EPSG:3857 (X/Y in meters).
    
    This is the standard projection used by Google Maps, OpenStreetMap, etc.
    """
    # WGS84 semi-major axis
    a = 6378137.0
    
    # Convert to radians
    lon_rad = math.radians(lon)
    lat_rad = math.radians(lat)
    
    # Web Mercator formulas
    x = a * lon_rad
    y = a * math.log(math.tan(math.pi / 4 + lat_rad / 2))
    
    return x, y


def wgs84_to_lambert93(lat: float, lon: float) -> Tuple[float, float]:
    """
    Convert WGS84 (lat/lon) to RGF93 Lambert-93 (X/Y in meters).
    """
    a = 6378137.0
    e = 0.0818191910428
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    lat_0 = math.radians(46.5)
    lon_0 = math.radians(3.0)
    k_0 = 0.9993
    x_0 = 700000
    y_0 = 6600000
    
    sin_lat = math.sin(lat_rad)
    e_sin = e * sin_lat
    t = math.tan(math.pi/4 - lat_rad/2) / pow((1 - e_sin)/(1 + e_sin), e/2)
    t_0 = math.tan(math.pi/4 - lat_0/2) / pow((1 - e*math.sin(lat_0))/(1 + e*math.sin(lat_0)), e/2)
    
    n = math.sin(lat_0)
    F = (math.cos(lat_0) / math.sqrt(1 - e*e*math.sin(lat_0)**2)) * pow(t_0, -n) / n
    r = a * F * pow(t, n) * k_0
    r_0 = a * F * pow(t_0, n) * k_0
    
    theta = n * (lon_rad - lon_0)
    
    x = x_0 + r * math.sin(theta)
    y = y_0 + r_0 - r * math.cos(theta)
    
    return x, y


def create_world_file(
    image_path: str,
    bbox: Dict[str, float],
    image_width: int,
    image_height: int,
    target_crs: int = EPSG_WEB_MERCATOR
) -> str:
    """
    Create a world file for georeferencing an image.
    
    Args:
        image_path: Path to the image file
        bbox: Dict with min_lat, max_lat, min_lon, max_lon (in WGS84)
        image_width: Image width in pixels
        image_height: Image height in pixels
        target_crs: Target CRS (EPSG code) - default EPSG:3857
        
    Returns:
        Path to created world file
    """
    # Determine world file extension
    ext = os.path.splitext(image_path)[1].lower()
    world_ext_map = {
        '.png': '.pgw',
        '.jpg': '.jgw', 
        '.jpeg': '.jgw',
        '.tif': '.tfw',
        '.tiff': '.tfw',
        '.gif': '.gfw',
        '.bmp': '.bpw',
    }
    world_ext = world_ext_map.get(ext, '.wld')
    world_path = os.path.splitext(image_path)[0] + world_ext
    
    # Get coordinates in target CRS
    if target_crs == EPSG_WEB_MERCATOR:
        x_min, y_max = wgs84_to_web_mercator(bbox['max_lat'], bbox['min_lon'])
        x_max, y_min = wgs84_to_web_mercator(bbox['min_lat'], bbox['max_lon'])
    elif target_crs == EPSG_RGF93:
        x_min, y_max = wgs84_to_lambert93(bbox['max_lat'], bbox['min_lon'])
        x_max, y_min = wgs84_to_lambert93(bbox['min_lat'], bbox['max_lon'])
    else:
        # WGS84 - use lon/lat directly (note: lon=X, lat=Y)
        x_min, y_max = bbox['min_lon'], bbox['max_lat']
        x_max, y_min = bbox['max_lon'], bbox['min_lat']
    
    # Calculate pixel size
    pixel_x = (x_max - x_min) / image_width
    pixel_y = -(y_max - y_min) / image_height  # Negative because Y increases downward
    
    # Upper-left pixel center
    ul_x = x_min + pixel_x / 2
    ul_y = y_max + pixel_y / 2
    
    # Write world file
    with open(world_path, 'w') as f:
        f.write(f"{pixel_x:.10f}\n")   # Pixel X size
        f.write("0.0\n")                # Rotation Y (0 = no rotation)
        f.write("0.0\n")                # Rotation X (0 = no rotation)
        f.write(f"{pixel_y:.10f}\n")   # Pixel Y size (negative)
        f.write(f"{ul_x:.6f}\n")       # Upper-left X
        f.write(f"{ul_y:.6f}\n")       # Upper-left Y
    
    logger.info(f"[SIG Export] Created world file: {world_path} (EPSG:{target_crs})")
    return world_path


def create_prj_file(image_path: str, epsg: int = EPSG_WEB_MERCATOR) -> str:
    """
    Create a .prj file with CRS definition for the image.
    """
    prj_path = os.path.splitext(image_path)[0] + '.prj'
    
    if epsg == EPSG_WEB_MERCATOR:
        wkt = '''PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1],AUTHORITY["EPSG","3857"]]'''
    elif epsg == EPSG_RGF93:
        wkt = '''PROJCS["RGF93 / Lambert-93",GEOGCS["RGF93",DATUM["Reseau_Geodesique_Francais_1993",SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44],PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3],PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000],UNIT["metre",1],AUTHORITY["EPSG","2154"]]'''
    else:
        wkt = '''GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'''
    
    with open(prj_path, 'w') as f:
        f.write(wkt)
    
    logger.info(f"[SIG Export] Created PRJ file: {prj_path} (EPSG:{epsg})")
    return prj_path
