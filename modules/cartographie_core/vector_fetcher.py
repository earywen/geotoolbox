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
    """Scrape activity information from GeoRisques SSP page using BeautifulSoup."""
    if not url or "http" not in url: return "-"
    
    try:
        from bs4 import BeautifulSoup
        r = session.get(url, timeout=5)
        if r.status_code != 200: return "Err HTTP"
        
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Method 1: Look for "Activité principale" in labels or dt
        # The structure is often a table-like definition list or simple table
        
        # Try finding the specific span or td
        # Pattern often: <td>Activité principale</td><td><span>...</span></td>
        
        container = soup.find(string=re.compile("Activité principale", re.IGNORECASE))
        if container:
            # Navigate up to parent and find the next sibling or value
            # Structure varies, typically it's in a neighboring cell
            # Case 1: <td>Title</td><td>Value</td>
            parent_td = container.find_parent('td')
            if parent_td:
                next_td = parent_td.find_next_sibling('td')
                if next_td:
                    val = next_td.get_text(strip=True)
                    if val: return val

            # Case 2: <dt>Title</dt><dd>Value</dd>
            parent_dt = container.find_parent('dt')
            if parent_dt:
                next_dd = parent_dt.find_next_sibling('dd')
                if next_dd:
                    val = next_dd.get_text(strip=True)
                    if val: return val
                    
        # Fallback to regex if BS4 fails to find structure but text exists
        # (Keeping legacy regex as fallback is safe)
        html = r.text.replace('\n', ' ').replace('\r', ' ')
        html = _WHITESPACE_PATTERN.sub(' ', html)
        
        m_prim = _ACTIVITY_PRIMARY_PATTERN.search(html)
        if m_prim:
             val = _HTML_TAG_PATTERN.sub('', m_prim.group(1)).strip()
             if val and "Non renseignée" not in val: return val

        return "Non détectée"
        
    except ImportError:
        # Fallback if BS4 not installed (graceful degradation)
        logging.warning("BeautifulSoup not found, falling back to regex")
        # Legacy Regex Code
        try:
            r = session.get(url, timeout=5)
            html = r.text.replace('\n', ' ').replace('\r', ' ')
            html = _WHITESPACE_PATTERN.sub(' ', html)
            m_prim = _ACTIVITY_PRIMARY_PATTERN.search(html)
            if m_prim:
                return _HTML_TAG_PATTERN.sub('', m_prim.group(1)).strip()
            return "Non détectée"
        except:
             return "Err Scrap"
             
    except Exception as e:
        return f"Err: {str(e)[:10]}"


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

    # Determine Version (Default 1.0.0)
    wfs_version = config.get("wfs_version", "1.0.0")
    
    # Generic Params
    params = {
        "service": "WFS",
        "version": wfs_version,
        "request": "GetFeature",
        "typeName": config["layer_name"],
        "srsName": "EPSG:4326" 
    }

    # BBOX Handling depends on Version and Service
    # WFS 1.0.0 -> Lon,Lat
    # WFS 1.1.0 -> Usually Lat,Lon if URN used, but Server dependent.
    # Our test showed INPN WFS 1.1.0 accepts Lon,Lat for "EPSG:4326"
    # IGN uses 2.0.0 Lat,Lon
    
    if config.get('url_key') == 'ign_wfs_url':
         # FORCE IGN Specific configuration
         params['version'] = "2.0.0"
         params['bbox'] = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    else:
         # Default Lon,Lat (Works for INPN 1.1.0 and Georisques 1.0.0/1.1.0)
         params['bbox'] = f"{min_lon},{min_lat},{max_lon},{max_lat}"


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
            
        max_workers = core.CONFIG.get('max_workers', 10)
        with ThreadPoolExecutor(max_workers=max_workers) as executor: list(executor.map(scrape_bss, rows))

    # SSP scraping for activity (export mode only)
    elif layer_key == "SSP" and mode == 'export' and rows:
        logging.info(f"Start Scraping Activités pour {len(rows)} sites SSP (Threads: {core.CONFIG.get('max_workers', 10)})...")
        def scrape_ssp(row):
            url = row.get('fiche_risque') or row.get('url_fiche') or row.get('lien_fiche')
            row['activite_principale'] = scrape_ssp_activity(session, url)
            return row
            
        max_workers = core.CONFIG.get('max_workers', 10)
        with ThreadPoolExecutor(max_workers=max_workers) as executor: list(executor.map(scrape_ssp, rows))

    return rows
