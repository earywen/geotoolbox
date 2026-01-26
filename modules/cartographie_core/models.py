"""
Data Models and Layer Configuration

Contains LAYERS_CONFIG and data models for vector/raster sources.

Migrated from: modules/geotoolbox_core/models.py
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class GeoFeature(BaseModel):
    id: str
    geometry: Optional[Dict[str, Any]] = None # GeoJSON Geometry
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    def to_ui_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for UI consumption."""
        return {**self.properties, "geometry": self.geometry, "id": self.id}


# ==========================================
# CONFIGURATION DES COUCHES VECTORIELLES
# ==========================================
LAYERS_CONFIG: Dict[str, Dict[str, Any]] = {
    "SSP": {
        "label": "Sites Pollués (CASIAS/BASOL)",
        "url_key": "georisques_url",
        "layer_name": "ms:SSP_ETS_GE_POINT",
        "format": "GML2",
        "color": "#ef4444",
        "type": "point",
        "name_field": "nom_etablissement",
        "columns_mapping": {"code_metier": "ID", "nom_etablissement": "Nom", "etat_activite": "Etat"}
    },
    "SIS": {
        "label": "Secteurs Information Sols (SIS)",
        "url_key": "georisques_url",
        "layer_name": "ms:SSP_CLASSIF_SIS_GE",
        "format": "GML2",
        "color": "#fb923c",
        "type": "polygon",
        "name_field": "nom_etablissement"
    },
    "SUP": {
        "label": "Servitudes Utilité Publique (SUP)",
        "url_key": "georisques_url",
        "layer_name": "ms:SSP_CLASSIF_SUP_GE",
        "format": "GML2",
        "color": "#d946ef",
        "type": "polygon",
        "name_field": "nom_etablissement"
    },
    "BSS": {
        "label": "Ouvrages BSS (Forages Eau)",
        "url_key": "brgm_wfs_url",
        "layer_name": "BSS_EAU_POINT",
        "format": "GML2",
        "color": "#3b82f6",
        "type": "point",
        "id_field": "bss_id",
        "name_field": "designation",
        "columns_mapping": {"code_bss": "Code", "designation": "Nom", "z_orifice": "Alt"}
    },
    # BDLISA Removed as requested

    "PARCELLE": {
        "label": "Parcelles (IGN)",
        "url_key": "ign_wfs_url",
        "layer_name": "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle",
        "wfs_version": "2.0.0",
        "format": "GML2",
        "color": "#eab308",
        "type": "polygon",
        "name_field": "label_parcelle",
        "columns_mapping": {"numero": "Numéro", "section": "Section", "commune": "Com"}
    },
    "EAU": {
        "label": "Cours d'eau (IGN)",
        "url_key": "ign_wfs_url",
        "layer_name": "BDTOPO_V3:cours_d_eau",
        "wfs_version": "2.0.0",
        "format": "GML2",
        "color": "#0ea5e9",
        "type": "line",
        "name_field": "toponyme",
        "columns_mapping": {"toponyme": "Nom", "nature": "Nature"}
    },
    "ZNIEFF1": {
        "label": "ZNIEFF Type 1",
        "url_key": "carmen_wfs_url",
        "layer_name": "Znieff1",
        "wfs_version": "1.1.0", # Required for INPN
        "format": "GML2",
        "color": "#16a34a", # Green
        "type": "polygon",
        "name_field": "NOM",
        "columns_mapping": {"NOM": "Nom", "ID_MNHN": "Identifiant"}
    },
    "ZNIEFF2": {
        "label": "ZNIEFF Type 2",
        "url_key": "carmen_wfs_url",
        "layer_name": "Znieff2",
        "wfs_version": "1.1.0",
        "format": "GML2",
        "color": "#15803d", # Dark Green
        "type": "polygon",
        "name_field": "NOM",
        "columns_mapping": {"NOM": "Nom", "ID_MNHN": "Identifiant"}
    },
    "NATURA": {
        "label": "Natura 2000 (ZPS)",
        "url_key": "carmen_wfs_url",
        "layer_name": "Zones_de_protection_speciale",
        "wfs_version": "1.1.0",
        "format": "GML2",
        "color": "#84cc16", # Lime
        "type": "polygon",
        "name_field": "NOM_SITE",
        "columns_mapping": {"NOM_SITE": "Nom", "SITECODE": "Code"}
    },
    "PPRI": {
        "label": "Communes (PPR Inondation)",
        "url_key": "georisques_url",
        "layer_name": "PPRN_COMMUNE_RISQINOND_APPROUV",
        "format": "GML2",
        "color": "#3b82f6", # Blue
        "type": "polygon",
        "name_field": "nom_commune",
        "columns_mapping": {"nom_commune": "Nom", "code_insee": "INSEE"}
    }
}
