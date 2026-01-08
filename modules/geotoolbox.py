import os
import sys
import time
import json
import logging
import base64
from datetime import datetime
from threading import Thread
from typing import List, Dict, Any, Optional, Tuple, Union

import webview

# CORE IMPORTS
from modules import core
from modules.geotoolbox_core.models import LAYERS_CONFIG
from modules.geotoolbox_core.fetcher import fetch_features
from modules.geotoolbox_core.maths import get_local_slope_vector, get_elevation_ign_only, calculate_geometrics
from modules.geotoolbox_core.exporter import generate_excel_for_layer

# ==========================================
# 1. META-DONNÉES
# ==========================================
TOOL_INFO: Dict[str, str] = {
    "id": "geotoolbox",
    "name": "GéoToolbox",
    "icon": "🌍",
    "description": "Outils de cartographie et scraping BSS/SSP"
}

# ==========================================
# 2. LOGIQUE PREVIEW
# ==========================================
def run_preview_logic(bbox: Dict[str, float], layers_list: List[str]) -> List[Dict[str, Any]]:
    """
    Executes the preview logic for selected layers within a bounding box.
    Fetches features but does not perform heavy geometric calculations.
    """
    results: List[Dict[str, Any]] = []
    window = webview.active_window()
    logging.info(f"Recherche Preview: {layers_list}")

    for index, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        if not config:
            continue
        
        pct = int((index / len(layers_list)) * 100)
        msg = f"Chargement {config['label']}..."
        
        # Event Driven Update
        core.dispatch_event('loader_update', {'percent': pct, 'message': msg})

        rows = fetch_features(layer_key, bbox, mode='preview')
        preview_items: List[Dict[str, Any]] = []
        name_k = config["name_field"].lower()
        
        for r in rows:
            # Basic Latitude Filter to strict check
            if r.get('LATITUDE_APPROX', 0) > 35:
                raw_nom = r.get(name_k)
                if not raw_nom or str(raw_nom).strip() == "" or raw_nom == "None":
                    raw_nom = r.get('bss_id') or r.get('code_bss') or r.get('id') or "Sans nom"
                
                preview_items.append({
                    "nom": str(raw_nom),
                    "color": config["color"],
                    "geometry": r.get('geometry'),
                    "details": r.get('niveau_eau_scrappe')
                })
        
        results.append({
            "layer": config['label'],
            "count": len(rows),
            "items": preview_items
        })

    # Finalize
    core.dispatch_event('loader_update', {'percent': 100, 'message': 'Affichage...'})
    time.sleep(0.5)
    core.dispatch_event('loader_hide', {})
    
    return results

# ==========================================
# 3. LOGIQUE EXPORT (THREADÉE SI POSSIBLE)
# ==========================================
def run_export_logic(bbox: Dict[str, float], layers_list: List[str], folder_name: Optional[str], base_path_ui: Optional[str]) -> Dict[str, Any]:
    """
    Executes the full export logic: fetching, geometric analysis (slope, elevation), and Excel generation.
    """
    # NOTE: In a perfect world, this should be running in a separate thread invoked by the API.
    # For now, we keep the synchronous structure but called via API.

    window = webview.active_window()
    base_path: str = ""

    if base_path_ui and os.path.isdir(base_path_ui):
        base_path = base_path_ui
    elif getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        # Assuming app is 2 levels up relative to this module file if simpler logic fails
        # But safest is standard abspath
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    folder = folder_name.strip() if folder_name else f"Export_{datetime.now().strftime('%H%M%S')}"
    path = os.path.join(base_path, folder)
    os.makedirs(path, exist_ok=True)

    summary: List[Dict[str, Any]] = []

    # --- ETAPE 1 : ANALYSE GLOBALE (0-10%) ---
    logging.info("--- DÉBUT ANALYSE GLOBALE ---")
    
    core.dispatch_event('loader_update', {'percent': 5, 'message': 'Analyse du relief (Pente locale)...'})

    try:
        c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
        c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
    except (KeyError, ValueError, TypeError):
        c_lat, c_lon = 0.0, 0.0

    slope_azimut, slope_val = get_local_slope_vector(c_lat, c_lon)

    core.dispatch_event('loader_update', {'percent': 10, 'message': 'Récupération Altitude de référence...'})
    
    z_center, src_center = get_elevation_ign_only(c_lat, c_lon)

    if z_center:
        logging.info(f"Centre Z={z_center}m ({src_center})")

    # --- ETAPE 2 : BOUCLE SUR LES COUCHES (10-100%) ---
    total_layers = len(layers_list)

    for i, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        if not config:
            continue
            
        progress_start = 10 + int((i / total_layers) * 90)
        msg = f"Traitement {config['label']}..."
        
        core.dispatch_event('loader_update', {'percent': progress_start, 'message': msg})

        rows = fetch_features(layer_key, bbox, mode='export')

        if rows:
            msg_calc = f"Calculs géométriques {config['label']} ({len(rows)} objets)..."
            core.dispatch_event('loader_update', {'percent': progress_start + 5, 'message': msg_calc})

        # SKIP OPTIMIZATION: On ne calcule pas les positions pour les parcelles (Trop lourd)
        if layer_key != "PARCELLE":
             rows = calculate_geometrics(rows, bbox, slope_azimut, z_center)

        core.dispatch_event('loader_update', {'percent': progress_start + 8, 'message': 'Génération Excel...'})

        fname = generate_excel_for_layer(rows, layer_key, path, config)
        if fname:
            summary.append({"layer": config['label'], "count": len(rows), "filename": fname})

    core.dispatch_event('loader_update', {'percent': 100, 'message': 'Export terminé !'})
    time.sleep(0.5)

    return {"folder": path, "summary": summary}

def save_map_image(base64_str: str, folder_path: str) -> Optional[str]:
    """Decodes a Base64 image string and saves it to the specified folder."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]

        img_data = base64.b64decode(base64_str)
        base: str = ""

        if folder_path and os.path.isdir(folder_path):
            base = folder_path
        elif getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(sys.path[0])

        fname = f"Carte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        full_path = os.path.join(base, fname)

        with open(full_path, "wb") as f:
            f.write(img_data)
        return full_path
    except Exception as e:
        logging.error(f"Image Save Error: {e}")
        return None

# ==========================================
# 4. UI LOADER (DÉLÉGUÉ)
# ==========================================
def get_ui_content() -> str:
    """Returns the HTML fragment for the Geotoolbox module."""
    # Note: On Context7 advice, we should move this HTML to assets/index.html or load it efficiently.
    # For Phase 2, we support the legacy dynamic loading via API.
    checkboxes_html = ""
    for k, c in LAYERS_CONFIG.items():
        # Ensure values are safe strings
        color = c.get("color", "#000000")
        label = c.get("label", k)
        
        checkboxes_html += f'''
        <div class="checkbox-wrapper">
            <input type="checkbox" id="chk_{k}" value="{k}" checked>
            <label for="chk_{k}" style="color:{color}">{label}</label>
        </div>
        '''
    template = core.load_template("geotoolbox.html")
    # Basic protection against template errors if None
    if not template:
        return "<div class='error'>Error loading geotoolbox template</div>"
        
    return template.replace("{{CHECKBOXES}}", checkboxes_html)