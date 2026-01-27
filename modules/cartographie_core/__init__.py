"""
Cartographie Core Package

This package contains the core logic for geospatial data extraction,
combining vector and raster processing capabilities.

Modules:
- vector_fetcher: WFS requests for vector data (BSS, BDLisa, etc.)
- vector_export: Excel and GeoJSON export for vectors
- raster_fetcher: WMS/PVA download for aerial imagery
- raster_processor: Image processing (crop, rotation, georef)
- maths: Geometric calculations
- models: Data models and layer configurations
- parsers: XML/JSON parsing
- config: Unified configuration
"""

# Vector exports (always available)
from .models import LAYERS_CONFIG, LAYER_CATEGORIES, PRESET_PROFILES
from .config import ExportOptions, RASTER_CONFIG
from .parsers import parse_gml_response, parse_wfs_response
from .maths import get_elevation_ign_only, get_local_slope_vector, calculate_geometrics
from .vector_fetcher import fetch_features
from .vector_export import generate_excel_for_layer

# Raster exports
from .raster_fetcher import IGN_MOSAICS, download_wms, process_all_pva, ensure_folder

# Raster processor with optional OpenCV import
try:
    from .raster_processor import create_georeferenced_pva, process_pva_image
except ImportError:
    # OpenCV not available
    create_georeferenced_pva = None
    process_pva_image = None

__all__ = [
    # Config
    'LAYERS_CONFIG',
    'LAYER_CATEGORIES',
    'PRESET_PROFILES',
    'RASTER_CONFIG',
    'ExportOptions',
    # Vector
    'fetch_features',
    'generate_excel_for_layer',
    'parse_gml_response',
    'parse_wfs_response',
    # Maths
    'calculate_geometrics',
    'get_local_slope_vector',
    'get_elevation_ign_only',
    # Raster
    'download_wms',
    'process_all_pva',
    'IGN_MOSAICS',
    'create_georeferenced_pva',
    'process_pva_image',
]
