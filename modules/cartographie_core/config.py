"""
Cartographie Configuration

Unified configuration for vector and raster data sources.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# Re-export layer configurations
from .models import LAYERS_CONFIG, LAYER_CATEGORIES, PRESET_PROFILES


@dataclass
class ExportOptions:
    """Options for unified export."""
    include_vectors: bool = True
    include_rasters: bool = True
    include_emprise: bool = True
    generate_qgis: bool = False
    vector_layers: Optional[List[str]] = None  # None = all layers
    raster_sources: Optional[List[str]] = None  # None = all sources
    

# Raster source configuration
RASTER_CONFIG = {
    "pva": {
        "label": "Photos Aériennes (PVA)",
        "description": "Photos aériennes historiques IGN",
        "enabled": True
    },
    "mosaics": {
        "label": "Mosaïques IGN",
        "description": "Orthophotos mosaïquées géoréférencées",
        "enabled": True
    }
}
