"""
GeoJSON Writer for SIG Export.

Converts fetched GéoToolbox rows to GeoJSON format with EPSG:3857 projection.
"""

import json
import os
import math
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def wgs84_to_web_mercator(lon: float, lat: float) -> Tuple[float, float]:
    """
    Convert WGS84 (lon, lat) to Web Mercator EPSG:3857 (X, Y in meters).
    """
    a = 6378137.0  # WGS84 semi-major axis
    
    x = a * math.radians(lon)
    y = a * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    
    return x, y


def convert_geometry_to_3857(geometry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a GeoJSON geometry from WGS84 to Web Mercator.
    Returns None if conversion fails.
    """
    if not geometry:
        return None
    
    geom_type = geometry.get('type', '')
    coords = geometry.get('coordinates')
    
    if not coords:
        return None
    
    try:
        if geom_type == 'Point':
            if len(coords) >= 2 and coords[0] is not None and coords[1] is not None:
                x, y = wgs84_to_web_mercator(float(coords[0]), float(coords[1]))
                return {"type": "Point", "coordinates": [x, y]}
        
        elif geom_type == 'MultiPoint':
            new_coords = [list(wgs84_to_web_mercator(float(c[0]), float(c[1]))) for c in coords if c and len(c) >= 2]
            if new_coords:
                return {"type": "MultiPoint", "coordinates": new_coords}
        
        elif geom_type == 'LineString':
            new_coords = [list(wgs84_to_web_mercator(float(c[0]), float(c[1]))) for c in coords if c and len(c) >= 2]
            if new_coords:
                return {"type": "LineString", "coordinates": new_coords}
        
        elif geom_type == 'MultiLineString':
            new_coords = [[list(wgs84_to_web_mercator(float(c[0]), float(c[1]))) for c in line if c and len(c) >= 2] for line in coords if line]
            if new_coords:
                return {"type": "MultiLineString", "coordinates": new_coords}
        
        elif geom_type == 'Polygon':
            new_coords = [[list(wgs84_to_web_mercator(float(c[0]), float(c[1]))) for c in ring if c and len(c) >= 2] for ring in coords if ring]
            if new_coords:
                return {"type": "Polygon", "coordinates": new_coords}
        
        elif geom_type == 'MultiPolygon':
            new_coords = [[[list(wgs84_to_web_mercator(float(c[0]), float(c[1]))) for c in ring if c and len(c) >= 2] for ring in poly if ring] for poly in coords if poly]
            if new_coords:
                return {"type": "MultiPolygon", "coordinates": new_coords}
    
    except (TypeError, ValueError, IndexError) as e:
        logger.warning(f"Failed to convert geometry: {e}")
        return None
    
    # Unknown type, return as-is
    return geometry


def rows_to_geojson(rows: List[Dict[str, Any]], layer_name: str = "layer") -> Dict[str, Any]:
    """
    Convert fetched rows to GeoJSON FeatureCollection in EPSG:3857.
    
    Args:
        rows: List of row dictionaries from fetcher (must contain 'geometry' key with WGS84 coords)
        layer_name: Name for the layer
        
    Returns:
        GeoJSON FeatureCollection dict with coordinates in EPSG:3857
    """
    features = []
    
    for row in rows:
        geometry = row.get('geometry')
        if not geometry:
            continue
        
        # Convert geometry to EPSG:3857
        converted_geometry = convert_geometry_to_3857(geometry)
        
        # Copy properties (all fields except geometry and internal fields)
        properties = {
            k: v for k, v in row.items() 
            if k not in ('geometry', 'LATITUDE_APPROX', 'LONGITUDE_APPROX', 'boundedBy')
            and v is not None
        }
        
        features.append({
            "type": "Feature",
            "geometry": converted_geometry,
            "properties": properties
        })
    
    return {
        "type": "FeatureCollection",
        "name": layer_name,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::3857"}
        },
        "features": features
    }


def export_geojson(
    rows: List[Dict[str, Any]], 
    output_path: str,
    layer_name: Optional[str] = None
) -> bool:
    """
    Export rows to a GeoJSON file in EPSG:3857.
    
    Args:
        rows: List of row dictionaries with geometry (WGS84)
        output_path: Full path for output .geojson file
        layer_name: Optional layer name (defaults to filename)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if not layer_name:
            layer_name = os.path.splitext(os.path.basename(output_path))[0]
        
        geojson_data = rows_to_geojson(rows, layer_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        
        feature_count = len(geojson_data.get('features', []))
        logger.info(f"[SIG Export] Created {output_path} ({feature_count} features, EPSG:3857)")
        return True
        
    except Exception as e:
        logger.error(f"[SIG Export] Failed to export GeoJSON: {e}")
        return False
