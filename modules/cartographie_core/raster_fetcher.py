"""
Raster Data Fetcher

Handles WMS requests and PVA downloads for aerial imagery.

Migrated from: modules/orthohisto.py
"""

import os
import math
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable, Tuple

from modules import core

# IGN Mosaic layers (géoréférencées)
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

# Minimum file size for non-empty images
MIN_IMAGE_SIZE = 50000  # 50KB


def ensure_folder(path: Optional[str]) -> str:
    """Creates directory if it doesn't exist. Defaults to user dir if path is None/Empty."""
    if not path or not path.strip():
        base = core.get_user_dir()
        path = os.path.join(base, f"Chronologie_{datetime.now().strftime('%Y%m%d_%H%M')}")
    
    os.makedirs(path, exist_ok=True)
    return path


def download_wms(layer_name: str, filename: str, bbox: str, bbox_dict: Optional[Dict[str, float]] = None) -> str:
    """Downloads a WMS tile for the given layer and bbox. Generates world file if bbox_dict provided.
    Returns 'OK', 'Vide' (empty/white), or 'Erreur'."""
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
            # Skip empty/white images - don't even save them
            if len(r.content) < MIN_IMAGE_SIZE:
                logging.info(f"[Mosaïque] {layer_name} -> Ignoré (image vide/blanche)")
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
                logging.warning(f"[PVA] 404 Non trouvé: {url}")
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
                        global_pct = base_pct + (progress * pct_range)
                        
                        # Throttle updates
                        if downloaded % (8192 * 20) == 0: 
                             progress_callback(global_pct, f"{label} ({int(progress*100)}%)")
            
            return downloaded
    except Exception as e:
        logging.error(f"[PVA] Erreur DL {os.path.basename(filepath)}: {e}")
        return -1


def _fallback_basic_georef(target: str, footprint: Dict[str, Any], year: int) -> None:
    """Fallback basic georeferencing without OpenCV processing."""
    try:
        from PIL import Image
        from modules.qgis_export.worldfile_writer import create_world_file, create_prj_file, EPSG_WEB_MERCATOR
        
        with Image.open(target) as img:
            width, height = img.size
        
        bbox_dict = {
            'min_lat': footprint['min_lat'],
            'max_lat': footprint['max_lat'],
            'min_lon': footprint['min_lon'],
            'max_lon': footprint['max_lon']
        }
        
        create_world_file(target, bbox_dict, width, height, target_crs=EPSG_WEB_MERCATOR)
        create_prj_file(target, epsg=EPSG_WEB_MERCATOR)
        logging.info(f"[PVA] {year}: World file créé EPSG:3857 ({width}x{height}px)")
        
    except Exception as e:
        logging.warning(f"[PVA] {year}: Erreur création world file: {e}")


def download_pva_tif(year: int, info: Dict[str, Any], folder_path: str, dl_base: str) -> Dict[str, str]:
    """Helper to download a single PVA TIF with real year in filename.
    
    Enhanced processing includes:
    1. Download the raw PVA TIF
    2. Auto-crop black scanner borders
    3. Apply rotation based on IGN orientation
    4. Create world file with adjusted footprint
    
    Uses EPSG:3857 (Web Mercator) for consistency with mosaics."""
    try:
        base_name = f"{year}_PVA.tif"
        target = os.path.join(folder_path, base_name)
        
        url_tif = f"{dl_base}/{info['ds_id']}/{info['img_id']}.tif"
        
        bytes_dl = download_file_stream(url_tif, target, progress_callback=None)
        
        if bytes_dl >= 0:
            size_mb = bytes_dl / (1024 * 1024)
            georef_status = ""
            processing_status = ""
            
            footprint = info.get('footprint')
            orientation = info.get('orientation')
            
            if footprint:
                # Try advanced processing with OpenCV
                try:
                    from .raster_processor import create_georeferenced_pva
                    
                    result = create_georeferenced_pva(
                        input_path=target,
                        footprint=footprint,
                        orientation=orientation,
                        auto_crop=True,
                        apply_rotation=True
                    )
                    
                    if result.get("success"):
                        georef_status = " (géoréf.+)"
                        if result.get("rotation_applied"):
                            processing_status = f" rot:{result['rotation_applied']:.0f}°"
                        logging.info(f"[PVA] {year}: Traitement avancé OK{processing_status}")
                    else:
                        raise Exception(result.get("error", "Unknown error"))
                        
                except ImportError as e:
                    logging.info(f"[PVA] {year}: OpenCV non disponible, géoréf. basique")
                    _fallback_basic_georef(target, footprint, year)
                    georef_status = " (géoréf.)"
                    
                except Exception as e:
                    logging.warning(f"[PVA] {year}: Traitement avancé échoué ({e}), fallback basique")
                    _fallback_basic_georef(target, footprint, year)
                    georef_status = " (géoréf.)"
            
            return {"annee": str(year), "status": f"PVA OK{georef_status} ({size_mb:.1f} Mo)"}
        else:
            return {"annee": str(year), "status": "Echec TIF"}
            
    except Exception as e:
        return {"annee": str(year), "status": f"Erreur: {str(e)}"}


def process_all_pva(lat: float, lon: float, folder_path: str, radius_m: int,
                    callback: Optional[Callable[[float, str], None]] = None,
                    current_prog: float = 0, progress_range: float = 90.0) -> List[Dict[str, str]]:
    """Fetches ALL historic PVA missions via WFS (no year limit) using Parallel Execution."""

    if callback:
        callback(current_prog, "Recherche de toutes les photos aériennes (PVA)...")
    logging.info(f"Recherche WFS PVA autour de {lat}, {lon} ({radius_m}m)")

    delta_lat = float(radius_m) / 111111.0
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

            geo = f.get('geometry', {})
            geo_type = geo.get('type', '')
            coords = geo.get('coordinates', [])
            
            dist = 999.0
            footprint = None
            orientation = props.get('orientation')
            
            if geo_type == 'Polygon' and coords:
                outer_ring = coords[0] if coords else []
                if outer_ring:
                    lons = [c[0] for c in outer_ring]
                    lats = [c[1] for c in outer_ring]
                    center_lon = sum(lons) / len(lons)
                    center_lat = sum(lats) / len(lats)
                    dist = math.sqrt((center_lon - lon)**2 + (center_lat - lat)**2)
                    
                    footprint = {
                        'min_lon': min(lons),
                        'max_lon': max(lons),
                        'min_lat': min(lats),
                        'max_lat': max(lats),
                        'polygon': outer_ring
                    }
                    logging.debug(f"[PVA] {year}: Polygon footprint found")
            
            elif geo_type == 'Point' and coords:
                p_lon, p_lat = coords[0], coords[1] if len(coords) > 1 else coords
                dist = math.sqrt((p_lon - lon)**2 + (p_lat - lat)**2)

            ds_id = props.get('dataset_identifier')
            img_id = props.get('image_identifier')
            if ds_id and img_id:
                if year not in candidates or candidates[year]['dist'] > dist:
                    candidates[year] = {
                        'dist': dist, 'year': year, 'date': d,
                        'ds_id': ds_id, 'img_id': img_id,
                        'footprint': footprint,
                        'orientation': orientation
                    }

        logging.info(f"WFS: {len(candidates)} années uniques trouvées (toutes périodes)")

    except Exception as e:
        logging.error(f"Erreur WFS PVA: {str(e)}")
        return [{"annee": "Erreur", "status": f"WFS: {str(e)}"}]

    logs: List[Dict[str, str]] = []
    total = len(candidates)
    if total == 0:
        logging.warning("Aucune PVA trouvée dans cette zone")
        return logs

    step = progress_range / total
    dl_base = core.CONFIG.get('orthohisto', {}).get('download_url')
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for year, info in candidates.items():
            f = executor.submit(download_pva_tif, year, info, folder_path, dl_base)
            futures[f] = year
            
        done_count = 0
        for f in as_completed(futures):
            done_count += 1
            res = f.result()
            logs.append(res)
            
            new_pct = current_prog + (done_count * step)
            if callback:
                y_lbl = res.get('annee', '?')
                r_status = res.get('status', '')
                status_short = "OK" if "OK" in r_status else "Échec"
                
                size_info = ""
                if "(" in r_status and "Mo)" in r_status:
                     size_info = r_status.split('(')[1].split(')')[0]
                     callback(new_pct, f"PVA: {done_count}/{total} (Année {y_lbl}: {size_info})")
                else:
                     callback(new_pct, f"PVA: {done_count}/{total} (Année {y_lbl} {status_short})")
                
            if "PVA OK" in res.get('status', ''):
                 logging.info(f"[PVA] {res['annee']} -> {res['status']}")
            else:
                 logging.warning(f"[PVA] {res['annee']} -> {res['status']}")

    return logs
