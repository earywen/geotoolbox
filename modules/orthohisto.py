import os
import math
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Dict, Any, Optional, Callable, Tuple

from modules import core

# ==========================================
# 1. META-DONNÉES
# ==========================================
TOOL_INFO: Dict[str, str] = {
    "id": "orthohisto",
    "name": "Chronologie Complète",
    "icon": "⏳",
    "description": "Extraction automatique 1920-2024"
}

IGN_MOSAICS: List[Tuple[str, str]] = [
    ("1950-1965", "ORTHOIMAGERY.ORTHOPHOTOS.1950-1965"),
    ("1965-1980", "ORTHOIMAGERY.ORTHOPHOTOS.1965-1980"),
    ("1980-1995", "ORTHOIMAGERY.ORTHOPHOTOS.1980-1995"),
    ("2000-2005", "ORTHOIMAGERY.ORTHOPHOTOS2000-2005"),
    ("2006-2010", "ORTHOIMAGERY.ORTHOPHOTOS2006-2010"),
    ("2011-2015", "ORTHOIMAGERY.ORTHOPHOTOS2011-2015"),
    ("2016-2020", "ORTHOIMAGERY.ORTHOPHOTOS2016-2020"),
    ("2021", "ORTHOIMAGERY.ORTHOPHOTOS2021"),
    ("2022", "ORTHOIMAGERY.ORTHOPHOTOS2022"),
    ("2023", "ORTHOIMAGERY.ORTHOPHOTOS2023"),
]

# ==========================================
# 2. LOGIQUE MÉTIER
# ==========================================
def ensure_folder(path: Optional[str]) -> str:
    """Creates directory if it doesn't exist. Defaults to user dir if path is None/Empty."""
    if not path or not path.strip():
        base = core.get_user_dir()
        path = os.path.join(base, f"Chronologie_{datetime.now().strftime('%Y%m%d_%H%M')}")
    
    os.makedirs(path, exist_ok=True)
    return path

def download_wms(layer_name: str, filename: str, bbox: str, bbox_dict: Optional[Dict[str, float]] = None) -> str:
    """Downloads a WMS tile for the given layer and bbox. Generates world file if bbox_dict provided."""
    wms_base = core.CONFIG.get('orthohisto', {}).get('wms_url')
    # Use 2500x2500 for good resolution
    url = (f"{wms_base}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=image/png"
           f"&TRANSPARENT=true&LAYERS={layer_name}&STYLES=&CRS=EPSG:4326"
           f"&BBOX={bbox}&WIDTH=2500&HEIGHT=2500")

    logging.info(f"[Mosaïque] Téléchargement {layer_name}...")
    try:
        session = core.get_session()
        r = session.get(url, timeout=60)

        if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
            if len(r.content) < 10000:
                logging.warning(f"[Mosaïque] {layer_name} est vide (probablement blanche)")
                return "Vide"

            with open(filename, 'wb') as f:
                f.write(r.content)
            
            # Generate world file for georeferencing
            if bbox_dict:
                try:
                    from modules.qgis_export.worldfile_writer import create_world_file, create_prj_file, EPSG_WEB_MERCATOR
                    create_world_file(filename, bbox_dict, 2500, 2500, target_crs=EPSG_WEB_MERCATOR)
                    create_prj_file(filename, epsg=EPSG_WEB_MERCATOR)
                    logging.info(f"[Mosaïque] {layer_name} -> OK (géoréférencé EPSG:3857)")
                except Exception as e:
                    logging.warning(f"[Mosaïque] World file failed for {layer_name}: {e}")
            else:
                logging.info(f"[Mosaïque] {layer_name} -> OK")
            
            return "OK"
        else:
            logging.error(f"[Mosaïque] Erreur HTTP {r.status_code} pour {layer_name}")

    except Exception as e:
        logging.error(f"[Mosaïque] Exception {layer_name}: {e}")

    return "Erreur"

def download_file_stream(url: str, filepath: str, 
                         progress_callback: Optional[Callable[[float, str], None]] = None,
                         base_pct: float = 0, pct_range: float = 0, label: str = "") -> int:
    """Downloads a file in chunks. Returns bytes downloaded on success, -1 on error."""
    try:
        session = core.get_session()
        with session.get(url, stream=True, timeout=60) as r:
            if r.status_code == 404:
                logging.warning(f"[Mission] 404 Non trouvé: {url}")
                return -1
            r.raise_for_status()
            
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = downloaded / total_size
                        # Global percent = base + (progress * range)
                        global_pct = base_pct + (progress * pct_range)
                        
                        # Throttle updates: send every ~160KB (20 chunks) to reduce event spam
                        if downloaded % (8192 * 20) == 0: 
                             progress_callback(global_pct, f"{label} ({int(progress*100)}%)")
            
            return downloaded
    except Exception as e:
        logging.error(f"[Mission] Erreur DL {os.path.basename(filepath)}: {e}")
        return -1

def download_mission_tif(year: int, info: Dict[str, Any], folder_path: str, dl_base: str) -> Dict[str, str]:
    """Helper to download a single mission TIF."""
    try:
        base_name = f"{year}_Mission.tif"
        target = os.path.join(folder_path, base_name)
        
        # Construct TIF URL directly
        url_tif = f"{dl_base}/{info['ds_id']}/{info['img_id']}.tif"
        
        # We pass None for callback to avoid granular spam, we track mission completion instead
        bytes_dl = download_file_stream(url_tif, target, progress_callback=None)
        
        if bytes_dl >= 0:
            size_mb = bytes_dl / (1024 * 1024)
            return {"annee": str(year), "status": f"Mission OK ({size_mb:.1f} Mo)"}
        else:
            return {"annee": str(year), "status": "Echec TIF"}
            
    except Exception as e:
        return {"annee": str(year), "status": f"Erreur: {str(e)}"}

def process_missions(lat: float, lon: float, folder_path: str, radius_m: int,
                     callback: Optional[Callable[[float, str], None]] = None,
                     current_prog: float = 0) -> List[Dict[str, str]]:
    """Fetches historic missions via WFS (< 1960) using Parallel Execution."""

    if callback:
        callback(current_prog, "Recherche Missions anciennes...")
    logging.info(f"Recherche WFS Missions anciennes autour de {lat}, {lon} ({radius_m}m)")

    # 1 deg de Latitude ~= 111.111 km
    delta_lat = float(radius_m) / 111111.0

    # 1 deg de Longitude dépend de la Latitude
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 0.0001:
        cos_lat = 0.0001
    delta_lon = delta_lat / cos_lat

    bbox = f"{lon-delta_lon},{lat-delta_lat},{lon+delta_lon},{lat+delta_lat}"

    wfs_base = core.CONFIG.get('orthohisto', {}).get('wfs_url')
    params = {
        "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
        "TYPENAMES": "pva:image", "SRSNAME": "CRS:84", "BBOX": f"{bbox},CRS:84",
        "OUTPUTFORMAT": "application/json"
    }

    candidates: Dict[int, Dict[str, Any]] = {}

    try:
        session = core.get_session()
        resp = session.get(wfs_base, params=params, timeout=30).json()
        features = resp.get('features', [])
        logging.info(f"WFS: {len(features)} clichés bruts trouvés dans la zone")

        for f in features:
            props = f.get('properties', {})
            d = props.get('date_cliche') or props.get('date') or props.get('date_prise_vue')
            if not d:
                continue
            try:
                year = int(str(d).split('-')[0])
            except (ValueError, IndexError):
                continue

            if year < 1960:
                geo = f.get('geometry', {})
                dist = 999.0
                if geo.get('type') == 'Point':
                    p_lon, p_lat = geo.get('coordinates')
                    dist = math.sqrt((p_lon - lon)**2 + (p_lat - lat)**2)

                ds_id = props.get('dataset_identifier')
                img_id = props.get('image_identifier')
                if ds_id and img_id:
                    if year not in candidates or candidates[year]['dist'] > dist:
                        candidates[year] = {
                            'dist': dist, 'year': year, 'date': d,
                            'ds_id': ds_id, 'img_id': img_id
                        }

        logging.info(f"WFS: {len(candidates)} années retenues (<1960) après filtrage")

    except Exception as e:
        logging.error(f"Erreur WFS Missions: {str(e)}")
        return [{"annee": "Erreur", "status": f"WFS: {str(e)}"}]

    logs: List[Dict[str, str]] = []
    total = len(candidates)
    if total == 0:
        return logs

    # Parallel Processing using ThreadPoolExecutor
    # Strategy: 0-50% progress distributed among N missions
    step = 50.0 / total
    dl_base = core.CONFIG.get('orthohisto', {}).get('download_url')
    
    # Use max_workers=4 to match user request/bandwidth limits
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for year, info in candidates.items():
            f = executor.submit(download_mission_tif, year, info, folder_path, dl_base)
            futures[f] = year
            
        done_count = 0
        for f in as_completed(futures):
            done_count += 1
            res = f.result()
            logs.append(res)
            
            # Update global progress
            new_pct = current_prog + (done_count * step)
            if callback:
                # Show Year in loader
                y_lbl = res.get('annee', '?')
                # Check for explicit success message
                r_status = res.get('status', '')
                status_short = "OK" if "OK" in r_status else "Échec"
                
                # Extract size if present in status string "Mission OK (12.5 Mo)"
                size_info = ""
                if "(" in r_status and "Mo)" in r_status:
                     size_info = r_status.split('(')[1].split(')')[0] # extract "12.5 Mo"
                     callback(new_pct, f"Missions: {done_count}/{total} (An {y_lbl}: {size_info})")
                else:
                     callback(new_pct, f"Missions: {done_count}/{total} (An {y_lbl} {status_short})")
                
            if "Mission OK" in res.get('status', ''):
                 logging.info(f"[Mission] {res['annee']} -> {res['status']}")
            else:
                 logging.warning(f"[Mission] {res['annee']} -> {res['status']}")

    return logs

def run_full_process(lat: float, lon: float, radius_m: int, folder_path_input: Optional[str],
                     progress_callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
    """Orchestrates the full historic imagery extraction process."""
    logging.info(f"=== Start Chronologie: {lat}, {lon} ===")

    folder_path = ensure_folder(folder_path_input)
    logging.info(f"Dossier cible: {folder_path}")

    final_report: List[Dict[str, str]] = []

    # ÉTAPE 1 : MISSIONS ANCIENNES (0% -> 50%)
    logging.info("--- Phase 1 : Missions < 1960 ---")
    mission_report = process_missions(lat, lon, folder_path, radius_m, progress_callback, 0)
    final_report.extend(mission_report)

    # ÉTAPE 2 : MOSAIQUES MODERNES (50% -> 100%)
    logging.info("--- Phase 2 : Mosaïques > 1950 ---")
    if progress_callback:
        progress_callback(50.0, "Démarrage Mosaïques...")

    delta_lat = float(radius_m) / 111111.0
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 0.0001:
        cos_lat = 0.0001
    delta_lon = delta_lat / cos_lat

    wms_bbox = f"{lat-delta_lat},{lon-delta_lon},{lat+delta_lat},{lon+delta_lon}"
    
    # Create bbox dict for georeferencing
    bbox_dict = {
        'min_lat': lat - delta_lat,
        'max_lat': lat + delta_lat,
        'min_lon': lon - delta_lon,
        'max_lon': lon + delta_lon
    }

    total_mos = len(IGN_MOSAICS)
    step_mos = 50.0 / total_mos

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures: Dict[Future, str] = {}
        for label, layer in IGN_MOSAICS:
            fname = os.path.join(folder_path, f"{label}.png")
            futures[executor.submit(download_wms, layer, fname, wms_bbox, bbox_dict)] = label

        done_count = 0
        for f in as_completed(futures):
            done_count += 1
            lbl = futures[f]
            try:
                res = f.result()
                current_pct = 50.0 + (done_count * step_mos)
                if progress_callback:
                    progress_callback(current_pct, f"Mosaïque {lbl}...")

                if res == "OK":
                    final_report.append({"annee": lbl, "status": "Mosaïque OK"})
            except Exception as e:
                logging.error(f"Error processing future for {lbl}: {e}")

    if progress_callback:
        progress_callback(100.0, "Finalisation...")

    def get_year(item: Dict[str, str]) -> int:
        try:
            return int(item.get('annee', '0')[:4])
        except (ValueError, TypeError, IndexError):
            return 0

    final_report.sort(key=get_year)

    logging.info(f"Chronologie terminée. {len(final_report)} fichiers générés.")
    return {"folder": folder_path, "summary": final_report}

# ==========================================
# 3. UI LOADER (TEMPLATING)
# ==========================================
def get_ui_content() -> str:
    """Returns the HTML fragment for the Orthohisto module."""
    # Safety wrapper could be added here similar to geotoolbox
    return core.load_template("orthohisto.html")
