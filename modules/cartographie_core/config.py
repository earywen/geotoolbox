"""
Cartographie Configuration

Unified configuration for vector and raster data sources.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os
import yaml
import logging

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

def load_styles() -> Dict[str, Any]:
    """Loads export styles from styles.yaml."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(base_dir, "styles.yaml")
    
    if not os.path.exists(style_path):
        logging.warning(f"Sortie styles.yaml introuvable: {style_path}")
        return {}
        
    try:
        with open(style_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logging.error(f"Erreur lecture styles.yaml: {e}")
        return {}
