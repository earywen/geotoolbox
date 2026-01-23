"""
Vector Data Fetcher

Handles WFS requests for vector data sources (BSS, BDLisa, SSP, etc.).

Migrated from: modules/geotoolbox_core/fetcher.py
"""

import re
import logging
from concurrent.futures import ThreadPoolExecutor
from modules import core
from .models import LAYERS_CONFIG
from .parsers import parse_gml_response

# Performance: Precompiled regex patterns for faster scraping
_WHITESPACE_PATTERN = re.compile(r'\s+')
_HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
_ACTIVITY_PRIMARY_PATTERN = re.compile(
    r"Activit(?:é|e)\s*principale.*?<td[^>]*>.*?<span>(.*?)</span>",
    re.IGNORECASE
)
_ACTIVITY_SECONDARY_PATTERN = re.compile(
    r"Activit(?:é|e)\(s\)\s*secondaire\(s\).*?<tbody>.*?<td>(.*?)</td>",
    re.IGNORECASE
)
_ACTIVITY_DD_PATTERN = re.compile(
    r"(?:Activit(?:é|e)(?:s)?\s*(?:principale|exercée)?).*?<dd[^>]*>(.*?)</dd>",
    re.IGNORECASE
)
_BSS_NIVEAU_EAU_PATTERN = re.compile(
    r"Niveau d'eau mesuré par rapport au sol.*?([\d]+(?:[\.,]\d+)?)\s*m",
    re.IGNORECASE
)


def scrape_ssp_activity(session, url):
    """Scrape activity information from GeoRisques SSP page."""
    if not url or "http" not in url: return "-"
    try:
        r = session.get(url, timeout=5)
        if r.status_code != 200: return "Err HTTP"
        html = r.text.replace('\n', ' ').replace('\r', ' ')
        html = _WHITESPACE_PATTERN.sub(' ', html)

        m_prim = _ACTIVITY_PRIMARY_PATTERN.search(html)
        val_prim = ""
        if m_prim:
            val_prim = _HTML_TAG_PATTERN.sub('', m_prim.group(1)).strip()
        if val_prim and "Non renseignée" not in val_prim and "Indéterminé" not in val_prim:
            return val_prim

        m_sec = _ACTIVITY_SECONDARY_PATTERN.search(html)
        if m_sec:
            val_sec = _HTML_TAG_PATTERN.sub('', m_sec.group(1)).strip()
            if val_sec and "Non renseignée" not in val_sec:
                return f"{val_sec} (Secondaire)"

        m_dd = _ACTIVITY_DD_PATTERN.search(html)
        if m_dd:
            val_dd = _HTML_TAG_PATTERN.sub('', m_dd.group(1)).strip()
            if val_dd: return val_dd

        return val_prim if val_prim else "Non détectée"
    except Exception: return "Err Scrap"


def fetch_features(layer_key, bbox, mode='preview'):
    """
    Fetch features from WFS for a given layer and bounding box.
    
    Args:
        layer_key: Layer identifier (e.g., 'BSS', 'SAGES')
        bbox: Bounding box with min_lat, max_lat, min_lon, max_lon
        mode: 'preview' or 'export'
        
    Returns:
        List of feature dictionaries
    """
    config = LAYERS_CONFIG.get(layer_key)
    if not config: return []
    base_url = core.CONFIG.get('geotoolbox', {}).get(config['url_key'])
    if not base_url: return []

    min_lon, min_lat = max(bbox['min_lon'], -180), max(bbox['min_lat'], -90)
    max_lon, max_lat = min(bbox['max_lon'], 180), min(bbox['max_lat'], 90)

    # Par défaut WFS 1.0.0 (Lon,Lat)
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": config["layer_name"],
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "srsName": "EPSG:4326"
    }

    # SPÉCIFIQUE IGN : WFS 2.0.0 + Axis Order Lat,Lon pour EPSG:4326
    if config.get('url_key') == 'ign_wfs_url':
        params['version'] = "2.0.0"
        params['bbox'] = f"{min_lat},{min_lon},{max_lat},{max_lon}"

    rows = []
    session = core.get_session()

    try:
        response = session.get(base_url, params=params, timeout=30)
        if response.status_code == 200:
            rows = parse_gml_response(response.text)
            logging.info(f"[{layer_key}] {len(rows)} objets trouvés")
        else: logging.warning(f"[{layer_key}] Erreur HTTP {response.status_code}")
    except Exception as e: logging.error(f"Err Fetch {layer_key}: {e}")

    # BSS scraping for water level
    if layer_key == "BSS" and rows:
        def scrape_bss(row):
            bss_id = row.get("bss_id")
            if not bss_id:
                row['niveau_eau_scrappe'] = "-"
                return row
            clean_id = bss_id.split('/')[0] if '/' in bss_id else bss_id
            url_base = core.CONFIG.get('geotoolbox', {}).get('infoterre_url')
            try:
                r = session.get(f"{url_base}{clean_id}", timeout=4)
                if r.status_code != 200: row['niveau_eau_scrappe'] = "Err HTTP"
                else:
                    html_flat = r.text.replace('\n', ' ').replace('\r', ' ')
                    m = _BSS_NIVEAU_EAU_PATTERN.search(html_flat)
                    row['niveau_eau_scrappe'] = f"{m.group(1)} m" if m else "Non indiqué"
            except Exception:
                row['niveau_eau_scrappe'] = "-"
            return row
        with ThreadPoolExecutor(max_workers=20) as executor: list(executor.map(scrape_bss, rows))

    # SSP scraping for activity (export mode only)
    elif layer_key == "SSP" and mode == 'export' and rows:
        logging.info(f"Start Scraping Activités pour {len(rows)} sites SSP...")
        def scrape_ssp(row):
            url = row.get('fiche_risque') or row.get('url_fiche') or row.get('lien_fiche')
            row['activite_principale'] = scrape_ssp_activity(session, url)
            return row
        with ThreadPoolExecutor(max_workers=20) as executor: list(executor.map(scrape_ssp, rows))

    return rows
