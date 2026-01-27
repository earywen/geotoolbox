"""
Data Models and Layer Configuration

Contains LAYER_CATEGORIES (hierarchical structure) and data models for vector/raster sources.

Migrated from: modules/geotoolbox_core/models.py
Extended: 2026-01 - Full layer catalog with 6 categories
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class GeoFeature(BaseModel):
    id: str
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON Geometry
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    def to_ui_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for UI consumption."""
        return {**self.properties, "geometry": self.geometry, "id": self.id}


# ==========================================
# CONFIGURATION DES COUCHES VECTORIELLES
# ==========================================

# Base layer template for reducing repetition
def _layer(label: str, url_key: str, layer_name: str, color: str, 
           layer_type: str, name_field: str, 
           wfs_version: str = "1.1.0", fmt: str = "GML2",
           columns_mapping: Optional[Dict[str, str]] = None,
           id_field: Optional[str] = None,
           heavy: bool = False) -> Dict[str, Any]:
    """Helper to create layer config with consistent structure."""
    cfg = {
        "label": label,
        "url_key": url_key,
        "layer_name": layer_name,
        "wfs_version": wfs_version,
        "format": fmt,
        "color": color,
        "type": layer_type,
        "name_field": name_field,
    }
    if columns_mapping:
        cfg["columns_mapping"] = columns_mapping
    if id_field:
        cfg["id_field"] = id_field
    if heavy:
        cfg["heavy"] = True
    return cfg


# ==========================================
# LAYER CATEGORIES - Hierarchical Structure
# ==========================================
LAYER_CATEGORIES: Dict[str, Dict[str, Any]] = {
    # ================================================
    # 🌿 ENVIRONNEMENT - Zones naturelles protégées
    # ================================================
    "environment": {
        "label": "🌿 Environnement",
        "icon": "leaf",
        "description": "Zones naturelles et espaces protégés",
        "layers": {
            # ZNIEFF (via Carmen INPN)
            "ZNIEFF1": _layer(
                "ZNIEFF Type 1", "carmen_wfs_url", "Znieff1",
                "#16a34a", "polygon", "NOM",
                columns_mapping={"NOM": "Nom", "ID_MNHN": "Identifiant"}
            ),
            "ZNIEFF2": _layer(
                "ZNIEFF Type 2", "carmen_wfs_url", "Znieff2",
                "#15803d", "polygon", "NOM",
                columns_mapping={"NOM": "Nom", "ID_MNHN": "Identifiant"}
            ),
            # Natura 2000 (via Carmen INPN)
            "NATURA_ZPS": _layer(
                "Natura 2000 - ZPS (Oiseaux)", "carmen_wfs_url", 
                "Zones_de_protection_speciale",
                "#84cc16", "polygon", "NOM_SITE",
                columns_mapping={"NOM_SITE": "Nom", "SITECODE": "Code"}
            ),
            "NATURA_SIC": _layer(
                "Natura 2000 - SIC (Habitats)", "carmen_wfs_url",
                "Sites_d_importance_communautaire",
                "#65a30d", "polygon", "NOM_SITE",
                columns_mapping={"NOM_SITE": "Nom", "SITECODE": "Code"}
            ),
            # Parcs et Réserves (via Géoplateforme)
            "PNR": _layer(
                "Parcs Naturels Régionaux", "ign_wfs_url",
                "PROTECTEDAREAS.PNR:pnr",
                "#059669", "polygon", "nom", wfs_version="2.0.0",
                columns_mapping={"nom": "Nom", "date_crea": "Création"}
            ),
            "PN": _layer(
                "Parcs Nationaux", "ign_wfs_url",
                "PROTECTEDAREAS.PN:pn",
                "#047857", "polygon", "nom", wfs_version="2.0.0",
                columns_mapping={"nom": "Nom"}
            ),
            "RNN": _layer(
                "Réserves Naturelles Nationales", "ign_wfs_url",
                "PROTECTEDAREAS.RNN:rnn",
                "#10b981", "polygon", "nom", wfs_version="2.0.0"
            ),
            "RNR": _layer(
                "Réserves Naturelles Régionales", "ign_wfs_url",
                "PROTECTEDAREAS.RNR:rnr",
                "#34d399", "polygon", "nom", wfs_version="2.0.0"
            ),
            "APB": _layer(
                "Arrêtés Protection Biotope", "ign_wfs_url",
                "PROTECTEDAREAS.APB:apb",
                "#6ee7b7", "polygon", "nom", wfs_version="2.0.0"
            ),
            "CEN": _layer(
                "Sites Conservatoire Littoral", "ign_wfs_url",
                "PROTECTEDAREAS.CDL:cdl",
                "#2dd4bf", "polygon", "nom", wfs_version="2.0.0"
            ),
            "RAMSAR": _layer(
                "Zones Humides RAMSAR", "ign_wfs_url",
                "PROTECTEDAREAS.RAMSAR:ramsar",
                "#0d9488", "polygon", "nom", wfs_version="2.0.0"
            ),
            # Forêt
            "FORET": _layer(
                "BD Forêt v2", "ign_wfs_url",
                "LANDCOVER.FORESTINVENTORY.V2:formation_vegetale",
                "#22c55e", "polygon", "essence", wfs_version="2.0.0",
                heavy=True
            ),
        }
    },
    
    # ================================================
    # 💧 EAUX - Hydrologie et eaux souterraines
    # ================================================
    "water": {
        "label": "💧 Eaux",
        "icon": "droplets",
        "description": "Hydrographie et eaux souterraines",
        "layers": {
            # Surface water (via IGN)
            "COURS_EAU": _layer(
                "Cours d'eau (BD TOPO)", "ign_wfs_url",
                "BDTOPO_V3:cours_d_eau",
                "#0ea5e9", "line", "toponyme", wfs_version="2.0.0",
                columns_mapping={"toponyme": "Nom", "nature": "Nature"}
            ),
            "PLAN_EAU": _layer(
                "Plans d'eau (BD TOPO)", "ign_wfs_url",
                "BDTOPO_V3:plan_d_eau",
                "#0284c7", "polygon", "toponyme", wfs_version="2.0.0",
                columns_mapping={"toponyme": "Nom", "nature": "Nature"}
            ),
            "TRONCON_HYDRO": _layer(
                "Tronçons hydrographiques", "ign_wfs_url",
                "BDTOPO_V3:troncon_hydrographique",
                "#38bdf8", "line", "toponyme", wfs_version="2.0.0"
            ),
            # BCAE
            "BCAE": _layer(
                "Cours d'eau BCAE", "ign_wfs_url",
                "HYDROGRAPHY.BCAE.LATEST:cours_d_eau",
                "#06b6d4", "line", "toponyme", wfs_version="2.0.0"
            ),
            # Groundwater (via BRGM)
            "BSS": _layer(
                "Ouvrages BSS (Forages)", "brgm_wfs_url",
                "BSS_EAU_POINT",
                "#3b82f6", "point", "designation",
                id_field="bss_id",
                columns_mapping={"code_bss": "Code", "designation": "Nom", "z_orifice": "Alt"}
            ),
            # BRGM ADES - these require WMS GetFeatureInfo (marked for future)
            "QUALITO": _layer(
                "Qualité Eaux Souterraines (ADES)", "brgm_ades_url",
                "point_eau_qualito",
                "#8b5cf6", "point", "code_bss",
                columns_mapping={"code_bss": "Code BSS", "masse_eau": "Masse d'eau"}
            ),
            "PIEZO": _layer(
                "Piézomètres (ADES)", "brgm_ades_url",
                "point_eau_piezo",
                "#a855f7", "point", "code_bss",
                columns_mapping={"code_bss": "Code BSS", "niveau": "Niveau"}
            ),
        }
    },
    
    # ================================================
    # ⚠️ RISQUES - Pollution et dangers
    # ================================================
    "risks": {
        "label": "⚠️ Risques & Pollution",
        "icon": "alert-triangle",
        "description": "Sites pollués et zones à risque",
        "layers": {
            # Sites pollués (Georisques)
            "SSP": _layer(
                "Sites Pollués (CASIAS/BASOL)", "georisques_url",
                "SSP_ETS_GE_POINT",
                "#ef4444", "point", "nom_etablissement",
                columns_mapping={"code_metier": "ID", "nom_etablissement": "Nom", "etat_activite": "Etat"}
            ),
            "SIS": _layer(
                "Secteurs Information Sols", "georisques_url",
                "SSP_CLASSIF_SIS_GE",
                "#fb923c", "polygon", "nom_etablissement"
            ),
            "SUP": _layer(
                "Servitudes Utilité Publique", "georisques_url",
                "SSP_CLASSIF_SUP_GE",
                "#d946ef", "polygon", "nom_etablissement"
            ),
            # PPR (Georisques - communes)
            "PPRI": _layer(
                "PPR Inondation (Communes)", "georisques_url",
                "PPRN_COMMUNE_RISQINOND_APPROUV",
                "#3b82f6", "polygon", "nom_commune",
                columns_mapping={"nom_commune": "Nom", "code_insee": "INSEE"}
            ),
            "PPRN": _layer(
                "PPR Naturels (Communes)", "georisques_url",
                "PPRN_COMMUNE_RISQNAT_APPROUV",
                "#6366f1", "polygon", "nom_commune",
                columns_mapping={"nom_commune": "Nom", "code_insee": "INSEE"}
            ),
            "PPRT": _layer(
                "PPR Technologiques (Communes)", "georisques_url",
                "PPRT_COMMUNE_RISQIND_APPROUV",
                "#a855f7", "polygon", "nom_commune",
                columns_mapping={"nom_commune": "Nom", "code_insee": "INSEE"}
            ),
            "PPRFEU": _layer(
                "PPR Feux de Forêt (Communes)", "georisques_url",
                "PPRN_COMMUNE_FEU_APPROUV",
                "#dc2626", "polygon", "nom_commune",
                columns_mapping={"nom_commune": "Nom", "code_insee": "INSEE"}
            ),
            # ICPE / Établissements pollueurs (BRGM)
            "ICPE": _layer(
                "Établissements Pollueurs (ICPE)", "brgm_georisques_url",
                "ETABLISSEMENTS_POLLUEURS",
                "#f97316", "point", "nom_etablissement",
                columns_mapping={"nom_etablissement": "Nom", "code_aiot": "Code AIOT"}
            ),
        }
    },
    
    # ================================================
    # 🏠 PARCELLAIRE & URBANISME
    # ================================================
    "cadastre": {
        "label": "🏠 Parcellaire & Urbanisme",
        "icon": "home",
        "description": "Cadastre et documents d'urbanisme",
        "layers": {
            "PARCELLE": _layer(
                "Parcelles cadastrales", "ign_wfs_url",
                "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle",
                "#eab308", "polygon", "label_parcelle", wfs_version="2.0.0",
                columns_mapping={"numero": "Numéro", "section": "Section", "commune": "Commune"}
            ),
            "SECTION": _layer(
                "Sections cadastrales", "ign_wfs_url",
                "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:section",
                "#ca8a04", "polygon", "label", wfs_version="2.0.0"
            ),
            "FEUILLE": _layer(
                "Feuilles cadastrales", "ign_wfs_url",
                "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:feuille",
                "#a16207", "polygon", "label", wfs_version="2.0.0"
            ),
            "COMMUNE": _layer(
                "Communes (Admin Express)", "ign_wfs_url",
                "ADMINEXPRESS-COG.LATEST:commune",
                "#f59e0b", "polygon", "nom", wfs_version="2.0.0",
                columns_mapping={"nom": "Nom", "insee_com": "INSEE"}
            ),
            "EPCI": _layer(
                "EPCI (Intercommunalités)", "ign_wfs_url",
                "ADMINEXPRESS-COG.LATEST:epci",
                "#d97706", "polygon", "nom", wfs_version="2.0.0"
            ),
            "DEPARTEMENT": _layer(
                "Départements", "ign_wfs_url",
                "ADMINEXPRESS-COG.LATEST:departement",
                "#b45309", "polygon", "nom", wfs_version="2.0.0"
            ),
            "REGION": _layer(
                "Régions", "ign_wfs_url",
                "ADMINEXPRESS-COG.LATEST:region",
                "#92400e", "polygon", "nom", wfs_version="2.0.0"
            ),
        }
    },
    
    # ================================================
    # 🗺️ BD TOPO - Infrastructure et bâti
    # ================================================
    "bdtopo": {
        "label": "🗺️ BD TOPO",
        "icon": "map",
        "description": "Bâtiments, routes, réseaux",
        "layers": {
            "BATIMENT": _layer(
                "Bâtiments", "ign_wfs_url",
                "BDTOPO_V3:batiment",
                "#64748b", "polygon", "usage_1", wfs_version="2.0.0",
                columns_mapping={"usage_1": "Usage", "hauteur": "Hauteur"},
                heavy=True
            ),
            "CONSTRUCTION": _layer(
                "Constructions surfaciques", "ign_wfs_url",
                "BDTOPO_V3:construction_surfacique",
                "#475569", "polygon", "nature", wfs_version="2.0.0"
            ),
            "ROUTE": _layer(
                "Routes", "ign_wfs_url",
                "BDTOPO_V3:troncon_de_route",
                "#71717a", "line", "nom_1", wfs_version="2.0.0",
                columns_mapping={"nom_1": "Nom", "importance": "Importance"},
                heavy=True
            ),
            "VOIE_FERREE": _layer(
                "Voies ferrées", "ign_wfs_url",
                "BDTOPO_V3:troncon_de_voie_ferree",
                "#52525b", "line", "nature", wfs_version="2.0.0"
            ),
            "LIGNE_ELECTRIQUE": _layer(
                "Lignes électriques", "ign_wfs_url",
                "BDTOPO_V3:ligne_electrique",
                "#fbbf24", "line", "tension", wfs_version="2.0.0",
                columns_mapping={"tension": "Tension (kV)"}
            ),
            "CANALISATION": _layer(
                "Canalisations", "ign_wfs_url",
                "BDTOPO_V3:canalisation",
                "#a3a3a3", "line", "nature", wfs_version="2.0.0"
            ),
            "VEGETATION": _layer(
                "Zones de végétation", "ign_wfs_url",
                "BDTOPO_V3:zone_de_vegetation",
                "#4ade80", "polygon", "nature", wfs_version="2.0.0",
                heavy=True
            ),
            "TERRAIN_SPORT": _layer(
                "Terrains de sport", "ign_wfs_url",
                "BDTOPO_V3:terrain_de_sport",
                "#22d3ee", "polygon", "nature", wfs_version="2.0.0"
            ),
            "CIMETIERE": _layer(
                "Cimetières", "ign_wfs_url",
                "BDTOPO_V3:cimetiere",
                "#9ca3af", "polygon", "nature", wfs_version="2.0.0"
            ),
            "RESERVOIR": _layer(
                "Réservoirs", "ign_wfs_url",
                "BDTOPO_V3:reservoir",
                "#60a5fa", "polygon", "nature", wfs_version="2.0.0"
            ),
        }
    },
    
    # ================================================
    # 🌍 OCCUPATION DU SOL
    # ================================================
    "landcover": {
        "label": "🌍 Occupation du Sol",
        "icon": "globe",
        "description": "Couverture et usage du sol",
        "heavy_category": True,
        "layers": {
            # OCSGE layers are not currently available on national WFS
            # "OCSGE_COUVERTURE": _layer(
            #     "OCS GE - Couverture", "ign_wfs_url",
            #     "OCSGE.COUVERTURE.LATEST:couverture_du_sol",
            #     "#8b5cf6", "polygon", "code_cs", wfs_version="2.0.0",
            #     heavy=True
            # ),
            # "OCSGE_USAGE": _layer(
            #     "OCS GE - Usage", "ign_wfs_url",
            #     "OCSGE.USAGE.LATEST:usage_du_sol",
            #     "#a78bfa", "polygon", "code_us", wfs_version="2.0.0",
            #     heavy=True
            # ),
            "CLC18": _layer(
                "Corine Land Cover 2018", "ign_wfs_url",
                "LANDCOVER.CLC18_FR:clc18_fr",
                "#c084fc", "polygon", "code_18", wfs_version="2.0.0",
                columns_mapping={"code_18": "Code CLC", "label_fr": "Libellé"},
                heavy=True
            ),
            "CLC12": _layer(
                "Corine Land Cover 2012", "ign_wfs_url",
                "LANDCOVER.CLC12_FR:clc12_fr",
                "#d8b4fe", "polygon", "code_12", wfs_version="2.0.0",
                heavy=True
            ),
            "RPG": _layer(
                "Registre Parcellaire Graphique", "ign_wfs_url",
                "RPG.LATEST:parcelles_graphiques",
                "#84cc16", "polygon", "code_cultu", wfs_version="2.0.0",
                columns_mapping={"code_cultu": "Culture"},
                heavy=True
            ),
        }
    },
}


# ==========================================
# PROFILS PRÉDÉFINIS
# ==========================================
PRESET_PROFILES: Dict[str, Dict[str, Any]] = {
    "env_complet": {
        "label": "🌿 Environnement Complet",
        "description": "Zones protégées, ZNIEFF, Natura 2000, Parcs",
        "layers": [
            "ZNIEFF1", "ZNIEFF2", "NATURA_ZPS", "NATURA_SIC",
            "PNR", "PN", "RNN", "RNR", "APB", "RAMSAR"
        ]
    },
    "ssp_risques": {
        "label": "⚠️ SSP & Risques",
        "description": "Sites pollués, SIS, SUP, PPR, ICPE",
        "layers": [
            "SSP", "SIS", "SUP", "PPRI", "PPRN", "PPRT", "PPRFEU", "ICPE", "PARCELLE"
        ]
    },
    "hydro": {
        "label": "💧 Étude Hydro",
        "description": "Forages BSS, qualité eau, hydrographie",
        "layers": [
            "BSS", "QUALITO", "PIEZO", "COURS_EAU", "PLAN_EAU", "BCAE"
        ]
    },
    "cadastre_complet": {
        "label": "🏠 Cadastre Complet",
        "description": "Parcelles, sections, communes, EPCI",
        "layers": [
            "PARCELLE", "SECTION", "FEUILLE", "COMMUNE", "EPCI"
        ]
    },
    "infrastructure": {
        "label": "🗺️ Infrastructure",
        "description": "Bâtiments, routes, réseaux",
        "layers": [
            "BATIMENT", "ROUTE", "VOIE_FERREE", "LIGNE_ELECTRIQUE"
        ]
    }
}


# ==========================================
# LEGACY FLAT CONFIG - For backward compatibility
# ==========================================
def get_flat_layers_config() -> Dict[str, Dict[str, Any]]:
    """
    Returns flat LAYERS_CONFIG for backward compatibility.
    Flattens all categories into single dict.
    """
    flat = {}
    for cat_key, cat_data in LAYER_CATEGORIES.items():
        for layer_key, layer_config in cat_data.get("layers", {}).items():
            flat[layer_key] = layer_config
    return flat


# Backward compatibility alias
LAYERS_CONFIG = get_flat_layers_config()
