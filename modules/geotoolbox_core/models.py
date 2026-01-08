import os

# ==========================================
# CONFIGURATION DES COUCHES
# ==========================================
LAYERS_CONFIG = {
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
    "PARCELLE": {
        "label": "Parcelles (IGN)",
        "url_key": "ign_wfs_url", 
        "layer_name": "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle",
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
        "format": "GML2",
        "color": "#0ea5e9",
        "type": "line",
        "name_field": "toponyme",
        "columns_mapping": {"toponyme": "Nom", "nature": "Nature"}
    }
}
