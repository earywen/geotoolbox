"""
Vector Data Fetcher

Handles WFS requests for vector data sources (BSS, BDLisa, SSP, etc.).

Migrated from: modules/geotoolbox_core/fetcher.py
"""

import re
import logging
from typing import List, Dict, Any, Optional
from modules import core
from .models import LAYERS_CONFIG, GeoFeature
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

logger = logging.getLogger(__name__)

def fetch_features(layer_key: str, bbox: Dict[str, float], mode: str = 'preview') -> List[GeoFeature]:
    """
    Fetch features from WFS for a given layer and bounding box.
    
    Orchestrates:
    1. Cache Lookup (Local DiskCache)
    2. WFS Fetching (OWSLib or Legacy Requests)
    3. Parsing (GML -> GeoFeature objects)
    4. Async Scraping (for BSS/SSP enrichment)
    5. Cache Storage
    
    Args:
        layer_key (str): Layer identifier (e.g., 'BSS', 'SAGES').
        bbox (dict): Bounding box with min_lat, max_lat, min_lon, max_lon.
        mode (str): 'preview' or 'export'.
        
    Returns:
        List[GeoFeature]: List of feature objects.
    """
    # --- CACHE ---
    from modules.cache_manager import get_cache
    cache = get_cache()
    
    # Cache Key for WFS
    cache_key_wfs = f"WFS_{layer_key}_{bbox['min_lon']:.4f}_{bbox['min_lat']:.4f}_{bbox['max_lon']:.4f}_{bbox['max_lat']:.4f}_{mode}"
    
    cached_rows = cache.get(cache_key_wfs)
    if cached_rows is not None:
         logger.info(f"[{layer_key}] Cache HIT ({len(cached_rows)} items)")
         rows = cached_rows
    else:
        # --- FETCH (Hybrid) ---
        config = LAYERS_CONFIG.get(layer_key)
        if not config: return []
        base_url = core.CONFIG.get('geotoolbox', {}).get(config['url_key'])
        if not base_url: return []

        # Prepare BBOX (always passed as tuple to OWSLib)
        bbox_tuple = (
            bbox['min_lon'], bbox['min_lat'],
            bbox['max_lon'], bbox['max_lat']
        )

        wfs_version = config.get("wfs_version", "1.0.0")
        layer_name = config["layer_name"]
        use_legacy = False # Force OWSLib for everyone since we fixed HTTPS
        rows = []

        if use_legacy:
            # --- LEGACY MANUAL FETCH (Requests) ---
            logger.info(f"[{layer_key}] Fetching in LEGACY mode (Carmen/INPN)")
            params = {
                "service": "WFS",
                "version": wfs_version,
                "request": "GetFeature",
                "typeName": layer_name,
                "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}",
                "srsName": "EPSG:4326"
            }
            session = core.get_session()
            try:
                response = session.get(base_url, params=params, timeout=5)
                if response.status_code == 200:
                    rows = parse_gml_response(response.text)
                    logger.info(f"[{layer_key}] {len(rows)} objets trouvés (Legacy)")
                else: 
                    logger.warning(f"[{layer_key}] Erreur HTTP {response.status_code}")
            except Exception as e: 
                logger.error(f"Err Fetch {layer_key}: {e}")

        else:
            # --- MODERN FETCH (OWSLib) ---
            try:
                from owslib.wfs import WebFeatureService
                
                wfs = WebFeatureService(url=base_url, version=wfs_version, timeout=90)
                kwargs = {
                    'typename': [layer_name],
                    'bbox': bbox_tuple
                }
                if wfs_version != '1.1.0':
                     kwargs['srsname'] = 'EPSG:4326'

                if wfs_version == '1.1.0':
                     kwargs['outputFormat'] = 'text/xml; subtype=gml/3.1.1' 
                
                logger.info(f"[{layer_key}] Fetching OWSLib v{wfs_version} BBOX={bbox_tuple}")
                response = wfs.getfeature(**kwargs)
                
                raw_gml = response.read()
                gml_text = raw_gml.decode('utf-8', errors='replace')
                
                if "ExceptionReport" in gml_text and "ExceptionText" in gml_text:
                     logger.error(f"[{layer_key}] WFS Service Exception: {gml_text[:200]}")
                else:
                    rows = parse_gml_response(gml_text)
                    logger.info(f"[{layer_key}] {len(rows)} objets trouvés (OWSLib)")
        
            except ImportError:
                logger.error("OWSLib not installed.")
            except Exception as e:
                logger.error(f"Err Fetch {layer_key}: {e}")

        # Save WFS Results to Cache (24h)
        if rows:
             cache.set(cache_key_wfs, rows, expire=86400)


    # --- ASYNC SCRAPING HELPERS ---
    async def fetch_url(session, url: str, timeout: int = 10):
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200: return None, response.status
                text = await response.text()
                return text, 200
        except Exception as e:
            return None, str(e)

    async def scrape_bss_row(session, feature: dict, url_base: str):
        """Scrape BSS water level for a specific feature."""
        if isinstance(feature, GeoFeature):
            props = feature.properties
        else:
             props = feature

        bss_id = props.get('bss_id') or props.get('id')
        if not bss_id:
            props['niveau_eau_scrappe'] = "-"
            return
        
        clean_id = bss_id.split('/')[0] if '/' in bss_id else bss_id
        
        # Check Cache
        cache_key = f"SCRAPE_BSS_{clean_id}"
        cached_val = cache.get(cache_key)
        cached_val = cache.get(cache_key)
        if cached_val:
             props['niveau_eau_scrappe'] = cached_val
             return

        url = f"{url_base}{clean_id}"
        text, status = await fetch_url(session, url, timeout=5)
        
        if status != 200:
             props['niveau_eau_scrappe'] = "Err HTTP" if isinstance(status, int) else "-"
        else:
             html_flat = text.replace('\n', ' ').replace('\r', ' ')
             m = _BSS_NIVEAU_EAU_PATTERN.search(html_flat)
             val = f"{m.group(1)} m" if m else "Non indiqué"
             props['niveau_eau_scrappe'] = val
             cache.set(cache_key, val, expire=604800)

    async def scrape_ssp_row(session, feature: Any):
        """Scrape SSP activity for a specific feature."""
        if isinstance(feature, GeoFeature):
             props = feature.properties
        else:
             props = feature

        url = props.get('fiche_risque') or props.get('url_fiche') or props.get('lien_fiche')
        if not url or "http" not in url: 
            props['activite_principale'] = "-"
            return

        # Check Cache
        cache_key = f"SCRAPE_SSP_{url}"
        cached_val = cache.get(cache_key)
        if cached_val:
             props['activite_principale'] = cached_val
             return

        text, status = await fetch_url(session, url, timeout=8)
        
        if status != 200:
             props['activite_principale'] = "Err HTTP"
             return

        html_flat = text.replace('\n', ' ').replace('\r', ' ')
        html_flat = _WHITESPACE_PATTERN.sub(' ', html_flat)
        m_prim = _ACTIVITY_PRIMARY_PATTERN.search(html_flat)
        val = "Non détectée"
        if m_prim:
             val = _HTML_TAG_PATTERN.sub('', m_prim.group(1)).strip()
        props['activite_principale'] = val
        cache.set(cache_key, val, expire=604800)

    async def process_batch(features: List[dict], layer_t: str):
        """Process batch async scraping for BSS or SSP layers."""
        url_base = core.CONFIG.get('geotoolbox', {}).get('infoterre_url')
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = []
            for feature in features:
                if layer_t == 'BSS':
                    tasks.append(scrape_bss_row(session, feature, url_base))
                elif layer_t == 'SSP':
                    tasks.append(scrape_ssp_row(session, feature))
            await asyncio.gather(*tasks)

    # Dispatch to Async
    if rows and layer_key == "BSS" and mode == 'export':
        try:
             import asyncio
             import aiohttp
             asyncio.run(process_batch(rows, "BSS"))
        except ImportError:
             logger.error("Missing aiohttp, skipping sync BSS scrape")
        except Exception as e:
             import traceback
             logger.error(f"Async BSS Error: {e}")
             traceback.print_exc()

    elif rows and layer_key == "SSP" and mode == 'export':
        logger.info(f"Start Scraping Activités pour {len(rows)} sites SSP (Async)...")
        try:
             import asyncio
             import aiohttp
             asyncio.run(process_batch(rows, "SSP"))
        except Exception as e:
             logger.error(f"Async SSP Error: {e}")

    return rows
