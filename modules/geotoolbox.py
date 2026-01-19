import os
import sys
import time
import logging
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Protocol

# CORE IMPORTS
# CORE IMPORTS
from modules import core
from modules.geotoolbox_core.models import LAYERS_CONFIG
from modules.geotoolbox_core.fetcher import fetch_features
from modules.geotoolbox_core.maths import get_local_slope_vector, get_elevation_ign_only, calculate_geometrics
from modules.geotoolbox_core.exporter import generate_excel_for_layer
import modules.geotoolbox_core.ui as ui_helper

class ProgressReporter(Protocol):
    def update(self, percent: int, message: str) -> None: ...

class CoreEventReporter:
    """Wrapper that dispatches events to the core system."""
    def update(self, percent: int, message: str) -> None:
        core.dispatch_event('loader_update', {'percent': percent, 'message': message})

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
# ==========================================
# 2. LOGIQUE PREVIEW
# ==========================================
def run_preview_logic(bbox: Dict[str, float], layers_list: List[str], reporter: Optional[ProgressReporter] = None) -> List[Dict[str, Any]]:
    """
    Executes the preview logic for selected layers within a bounding box.
    Fetches features but does not perform heavy geometric calculations.
    """
    results: List[Dict[str, Any]] = []
    logging.info(f"Recherche Preview: {layers_list}")
    
    if reporter is None:
        reporter = CoreEventReporter()

    for index, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        if not config:
            continue

        pct = int((index / len(layers_list)) * 100)
        msg = f"Chargement {config['label']}..."
        reporter.update(pct, msg)

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
    reporter.update(100, 'Affichage...')
    core.dispatch_event('loader_hide', {})

    return results

# ==========================================
# 3. LOGIQUE EXPORT (THREADÉE SI POSSIBLE)
# ==========================================

def _prepare_export_directory(folder_name: Optional[str], base_path_ui: Optional[str]) -> str:
    """Prepares the export directory and returns its path."""
    base_path: str = ""

    if base_path_ui and os.path.isdir(base_path_ui):
        base_path = base_path_ui
    elif getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    folder = folder_name.strip() if folder_name else f"Export_{datetime.now().strftime('%H%M%S')}"
    path = os.path.join(base_path, folder)
    os.makedirs(path, exist_ok=True)
    return path

def _perform_global_analysis(bbox: Dict[str, float], reporter: Optional[ProgressReporter] = None) -> tuple[float, float, float]:
    """Performs global analysis (slope, elevation) for the bbox center."""
    if reporter: reporter.update(5, 'Analyse du relief (Pente locale)...')

    try:
        c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
        c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
    except (KeyError, ValueError, TypeError):
        c_lat, c_lon = 0.0, 0.0

    slope_azimut, _ = get_local_slope_vector(c_lat, c_lon)

    if reporter: reporter.update(10, 'Récupération Altitude de référence...')
    z_center, src_center = get_elevation_ign_only(c_lat, c_lon)

    if z_center:
        logging.info(f"Centre Z={z_center}m ({src_center})")
    
    return slope_azimut, z_center

def _process_layer_export(layer_key: str, bbox: Dict[str, float], slope_azimut: float, z_center: float, path: str) -> Dict[str, Any]:
    """Processes a single layer for export."""
    config = LAYERS_CONFIG.get(layer_key)
    if not config:
        return {"status": "skipped", "reason": "Config missing"}

    try:
        rows = fetch_features(layer_key, bbox, mode='export')

        if rows and layer_key != "PARCELLE":
             rows = calculate_geometrics(rows, bbox, slope_azimut, z_center)

        fname = generate_excel_for_layer(rows, layer_key, path, config)
        if fname:
            return {"status": "success", "layer": config['label'], "count": len(rows), "filename": fname}
        return {"status": "empty", "layer": config['label']}
        
    except Exception as e:
        logging.error(f"Error exporting layer {layer_key}: {e}")
        return {"status": "error", "layer": config.get('label', layer_key), "error": str(e)}

def run_export_logic(bbox: Dict[str, float], layers_list: List[str], folder_name: Optional[str], base_path_ui: Optional[str], reporter: Optional[ProgressReporter] = None) -> Dict[str, Any]:
    """
    Executes the full export logic: fetching, geometric analysis (slope, elevation), and Excel generation.
    """
    path = _prepare_export_directory(folder_name, base_path_ui)
    summary: List[Dict[str, Any]] = []

    if reporter is None:
        reporter = CoreEventReporter()

    # --- ETAPE 1 : ANALYSE GLOBALE (0-10%) ---
    logging.info("--- DÉBUT ANALYSE GLOBALE ---")
    
    slope_azimut, z_center = _perform_global_analysis(bbox, reporter)

    # --- ETAPE 2 : BOUCLE SUR LES COUCHES (10-100%) ---
    total_layers = len(layers_list)

    for i, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        if not config:
            continue

        progress_start = 10 + int((i / total_layers) * 90)
        msg = f"Traitement {config['label']}..."
        reporter.update(progress_start, msg)

        # Additional UI update simulation if we wanted to be exact, but simplifying for readability
        reporter.update(progress_start + 5, f"Calculs géométriques {config['label']}...")
        reporter.update(progress_start + 8, 'Génération Excel...')

        result = _process_layer_export(layer_key, bbox, slope_azimut, z_center, path)
        if result['status'] == 'success':
            summary.append(result)
        elif result['status'] == 'error':
             summary.append(result) # We might want to show errors in summary too

    reporter.update(100, 'Export terminé !')
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
    
    checkboxes_html = ui_helper.generate_checkboxes_html(LAYERS_CONFIG)

    template = core.load_template("geotoolbox.html")
    # Basic protection against template errors if None
    if not template:
        return "<div class='error'>Error loading geotoolbox template</div>"

    return template.replace("{{CHECKBOXES}}", checkboxes_html)
