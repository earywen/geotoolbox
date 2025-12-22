import os
import sys
import time
import webview
import xml.etree.ElementTree as ET
import re
import math
import requests 
from datetime import datetime
import pandas as pd
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from modules import core 

# ==========================================
# 1. META-DONNÉES
# ==========================================
TOOL_INFO = {
    "id": "geotoolbox",
    "name": "GéoToolbox",
    "icon": "🌍",
    "description": "Outils de cartographie et scraping BSS/SSP"
}

# ==========================================
# 2. CONFIGURATION DES COUCHES
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
    }
}

# ==========================================
# 3. LOGIQUE GÉOMÉTRIQUE & PARSING
# ==========================================
def smart_fix_coords_france(lat, lon):
    try:
        val1 = float(lat)
        val2 = float(lon)
    except: return None, None 
    if abs(val1) > 180 or abs(val2) > 180: return None, None
    if (val1 < 20 and val2 > 35): return val2, val1 
    return val1, val2

def parse_gml_coord_string(text, is_poslist=False, dimension_hint=2):
    if not text: return []
    points = []
    try:
        if is_poslist:
            tokens = text.replace(',', ' ').split()
            step = dimension_hint
            if len(tokens) % step != 0: step = 2
            for i in range(0, len(tokens), step):
                if i+1 < len(tokens):
                    lat, lon = smart_fix_coords_france(tokens[i+1], tokens[i])
                    if lat is not None: points.append([lon, lat])
        else:
            tuples = text.strip().split() 
            for t in tuples:
                coords = t.split(',')
                if len(coords) >= 2:
                    lat, lon = smart_fix_coords_france(coords[1], coords[0])
                    if lat is not None: points.append([lon, lat])
    except: pass
    return points

def parse_geometry_hybrid(element):
    try:
        point_tag = element.find(".//Point") or element.find(".//Point")
        if point_tag is not None:
            coords = point_tag.find(".//coordinates")
            if coords is not None and coords.text:
                pts = parse_gml_coord_string(coords.text, is_poslist=False)
                if pts: return {"type": "Point", "coordinates": pts[0]}, pts[0][1], pts[0][0]
            pos = point_tag.find(".//pos")
            if pos is not None and pos.text:
                pts = parse_gml_coord_string(pos.text, is_poslist=True, dimension_hint=2)
                if pts: return {"type": "Point", "coordinates": pts[0]}, pts[0][1], pts[0][0]

        polys_tags = element.findall(".//Polygon") + element.findall(".//PolygonPatch")
        all_polygons_geojson = [] 
        all_points_flat = []

        for poly in polys_tags:
            exterior = poly.find(".//exterior") or poly.find(".//outerBoundaryIs")
            if exterior is None: continue
            ring_coords = []
            c_tag = exterior.find(".//coordinates")
            if c_tag is not None and c_tag.text:
                ring_coords = parse_gml_coord_string(c_tag.text, is_poslist=False)
            if not ring_coords:
                p_tag = exterior.find(".//posList")
                if p_tag is not None and p_tag.text:
                    dim = 2
                    if 'srsDimension="3"' in str(ET.tostring(p_tag)) or len(p_tag.text.split()) % 3 == 0: dim = 3
                    ring_coords = parse_gml_coord_string(p_tag.text, is_poslist=True, dimension_hint=dim)
            if not ring_coords: continue
            if ring_coords[0] != ring_coords[-1]: ring_coords.append(ring_coords[0])
            poly_structure = [ring_coords]
            all_points_flat.extend(ring_coords)

            interiors = poly.findall(".//interior") or poly.findall(".//innerBoundaryIs")
            for interior in interiors:
                hole_coords = []
                c_tag_in = interior.find(".//coordinates")
                if c_tag_in is not None and c_tag_in.text:
                    hole_coords = parse_gml_coord_string(c_tag_in.text, is_poslist=False)
                if hole_coords:
                    if hole_coords[0] != hole_coords[-1]: hole_coords.append(hole_coords[0])
                    poly_structure.append(hole_coords)
            all_polygons_geojson.append(poly_structure)

        if not all_polygons_geojson: return None, 0, 0
        avg_lon = sum(p[0] for p in all_points_flat) / len(all_points_flat)
        avg_lat = sum(p[1] for p in all_points_flat) / len(all_points_flat)
        return {"type": "MultiPolygon", "coordinates": all_polygons_geojson}, avg_lat, avg_lon
    except: return None, 0, 0

def parse_gml_response(xml_text):
    rows = []
    try:
        xml_content = re.sub(r'(</?)[a-zA-Z0-9]+:', r'\1', xml_text)
        root = ET.fromstring(xml_content)
        features = root.findall(".//featureMember") + root.findall(".//member")
        
        for feature in features:
            if len(list(feature)) == 0: continue 
            obj = list(feature)[0]
            props = {}
            geojson_geom, lat_center, lon_center = parse_geometry_hybrid(obj)
            for child in obj:
                tag_clean = child.tag.lower().strip()
                if "geometry" not in tag_clean and "boundedby" not in tag_clean:
                    if child.text: props[tag_clean] = child.text.strip()
            if geojson_geom:
                props['geometry'] = geojson_geom
                props['LATITUDE_APPROX'] = lat_center
                props['LONGITUDE_APPROX'] = lon_center
                if "code_bss" in props: props["bss_id"] = props["code_bss"]
                if "code_ssp" in props: props["id"] = props["code_ssp"]
                rows.append(props)
    except Exception as e: logging.error(f"Erreur XML: {e}")
    return rows

# ==========================================
# 4. LOGIQUE D'ACQUISITION (FETCH & SCRAPE)
# ==========================================

def scrape_ssp_activity(session, url):
    if not url or "http" not in url: return "-"
    try:
        r = session.get(url, timeout=5)
        if r.status_code != 200: return "Err HTTP"
        html = r.text.replace('\n', ' ').replace('\r', ' ')
        html = re.sub(r'\s+', ' ', html)
        
        m_prim = re.search(r"Activit(?:é|e)\s*principale.*?<td[^>]*>.*?<span>(.*?)</span>", html, re.IGNORECASE)
        val_prim = ""
        if m_prim:
            val_prim = re.sub(r'<[^>]+>', '', m_prim.group(1)).strip()
        if val_prim and "Non renseignée" not in val_prim and "Indéterminé" not in val_prim:
            return val_prim
            
        m_sec = re.search(r"Activit(?:é|e)\(s\)\s*secondaire\(s\).*?<tbody>.*?<td>(.*?)</td>", html, re.IGNORECASE)
        if m_sec:
            val_sec = re.sub(r'<[^>]+>', '', m_sec.group(1)).strip()
            if val_sec and "Non renseignée" not in val_sec:
                return f"{val_sec} (Secondaire)"

        m_dd = re.search(r"(?:Activit(?:é|e)(?:s)?\s*(?:principale|exercée)?).*?<dd[^>]*>(.*?)</dd>", html, re.IGNORECASE)
        if m_dd:
            val_dd = re.sub(r'<[^>]+>', '', m_dd.group(1)).strip()
            if val_dd: return val_dd

        return val_prim if val_prim else "Non détectée"
    except Exception: return "Err Scrap"

def fetch_features(layer_key, bbox, mode='preview'):
    config = LAYERS_CONFIG.get(layer_key)
    if not config: return []
    base_url = core.CONFIG.get('geotoolbox', {}).get(config['url_key'])
    if not base_url: return []

    min_lon, min_lat = max(bbox['min_lon'], -180), max(bbox['min_lat'], -90)
    max_lon, max_lat = min(bbox['max_lon'], 180), min(bbox['max_lat'], 90)
    params = {"service": "WFS", "version": "1.0.0", "request": "GetFeature", "typeName": config["layer_name"], "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}", "srsName": "EPSG:4326"}
    
    rows = []
    session = core.get_session()

    try:
        response = session.get(base_url, params=params, timeout=30)
        if response.status_code == 200: 
            rows = parse_gml_response(response.text)
            logging.info(f"[{layer_key}] {len(rows)} objets trouvés")
        else: logging.warning(f"[{layer_key}] Erreur HTTP {response.status_code}")
    except Exception as e: logging.error(f"Err Fetch {layer_key}: {e}")

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
                    m = re.search(r"Niveau d'eau mesuré par rapport au sol.*?([\d]+(?:[\.,]\d+)?)\s*m", html_flat, re.IGNORECASE)
                    row['niveau_eau_scrappe'] = f"{m.group(1)} m" if m else "Non indiqué"
            except: row['niveau_eau_scrappe'] = "-"
            return row
        with ThreadPoolExecutor(max_workers=20) as executor: list(executor.map(scrape_bss, rows))
    
    elif layer_key == "SSP" and mode == 'export' and rows:
        logging.info(f"Start Scraping Activités pour {len(rows)} sites SSP...")
        def scrape_ssp(row):
            url = row.get('fiche_risque') or row.get('url_fiche') or row.get('lien_fiche')
            row['activite_principale'] = scrape_ssp_activity(session, url)
            return row
        with ThreadPoolExecutor(max_workers=20) as executor: list(executor.map(scrape_ssp, rows))

    return rows

# ==========================================
# 5. LOGIQUE EXPORT & CALCUL ALTIMÉTRIE
# ==========================================

def get_elevation_ign_only(lat, lon):
    """
    Récupère l'altitude via l'API IGN Géoplateforme avec gestion des limites.
    Retourne un COUPLE : (Altitude_float, Nom_source_str)
    """
    session = core.get_session()
    ign_url = "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json"
    
    ign_resources = ['ign_rge_alti_wld'] 

    for res_name in ign_resources:
        try:
            params = {
                'lon': str(lon), 'lat': str(lat),
                'resource': res_name,
                'delimiter': '|', 'indent': 'false', 'measures': 'false', 'zonly': 'false'
            }
            time.sleep(0.25)
            r = session.get(ign_url, params=params, timeout=5)
            
            if r.status_code == 429:
                logging.warning("IGN Rate Limit (429) -> Pause...")
                time.sleep(1.5)
                r = session.get(ign_url, params=params, timeout=5)

            if r.status_code == 200:
                data = r.json()
                if 'elevations' in data and len(data['elevations']) > 0:
                    val = data['elevations'][0]['z']
                    return float(val), f"IGN ({res_name})" 
            else:
                pass 
                
        except Exception:
            pass 

    return None, None 

def get_local_slope_vector(c_lat, c_lon):
    """
    Calcule la direction de la pente locale.
    """
    logging.info("Calcul du vecteur pente local (pas de 150m)...")
    
    D = 150 
    d_lat = D / 111111.0
    d_lon = D / (111111.0 * math.cos(math.radians(c_lat)))
    
    z_n, _ = get_elevation_ign_only(c_lat + d_lat, c_lon)
    z_s, _ = get_elevation_ign_only(c_lat - d_lat, c_lon)
    z_e, _ = get_elevation_ign_only(c_lat, c_lon + d_lon)
    z_w, _ = get_elevation_ign_only(c_lat, c_lon - d_lon)
    
    if any(z is None for z in [z_n, z_s, z_e, z_w]):
        logging.warning("Impossible de calculer la pente (Z manquant)")
        return None, None

    dz_dx = (z_e - z_w) / (2 * D)
    dz_dy = (z_n - z_s) / (2 * D)
    
    vec_x = - (z_e - z_w)
    vec_y = - (z_n - z_s)
    
    slope_angle = (math.degrees(math.atan2(vec_x, vec_y)) + 360) % 360
    slope_pct = math.sqrt(dz_dx**2 + dz_dy**2) * 100
    
    dirs = ["Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ouest", "Ouest", "Nord-Ouest"]
    dir_txt = dirs[round(slope_angle / 45) % 8]
    
    logging.info(f"Pente locale : {slope_pct:.1f}% vers {dir_txt} ({slope_angle:.0f}°)")
    logging.info(f"Détail Z : N={z_n} S={z_s} E={z_e} W={z_w}")
    
    return slope_angle, slope_pct

def calculate_geometrics(rows, bbox, slope_azimut, z_center):
    """
    Calcul géométrique pour une liste de points avec SÉPARATION DES COLONNES.
    """
    if not rows or not bbox: return rows
    
    c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
    c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
    
    def process_geom(row):
        try:
            p_lat = float(row.get('LATITUDE_APPROX', 0))
            p_lon = float(row.get('LONGITUDE_APPROX', 0))
            ident = row.get('code_metier') or row.get('id') or "N/A"
            
            if p_lat == 0 and p_lon == 0:
                row['geo_dist_dir'] = "Non localisé"
                row['hydro_context'] = "Non localisé"
                return row

            # 1. Distance & Azimut
            R = 6371000
            phi1, phi2 = math.radians(c_lat), math.radians(p_lat)
            dphi, dlambda = math.radians(p_lat - c_lat), math.radians(p_lon - c_lon)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            dist = int(R * c)
            
            y = math.sin(dlambda) * math.cos(phi2)
            x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
            site_bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
            
            dirs = ["au Nord", "au Nord-Est", "à l'Est", "au Sud-Est", "au Sud", "au Sud-Ouest", "à l'Ouest", "au Nord-Ouest"]
            direction = dirs[round(site_bearing / 45) % 8]
            
            # --- COLONNE 1 : GÉOMÉTRIE ---
            row['geo_dist_dir'] = f"{dist} m {direction}"
            
            # 2. Interprétation Pente
            hydro_status = "Latéral"
            
            if slope_azimut is not None:
                diff = abs(site_bearing - slope_azimut)
                if diff > 180: diff = 360 - diff
                
                # Cône élargi à 75°
                if diff <= 75: hydro_status = "Aval"
                elif diff >= 105: hydro_status = "Amont"
                else: hydro_status = "Latéral"
            else:
                hydro_status = "Indéterminé"

            # 3. Interprétation Z Topo (Juge de Paix)
            z_suffix = ""
            if z_center is not None and dist < 3000:
                z_site, _ = get_elevation_ign_only(p_lat, p_lon)
                if z_site is not None:
                    diff_z = z_site - z_center
                    if diff_z > 2: z_suffix = f" [Z+{int(diff_z)}m]"
                    elif diff_z < -2: z_suffix = f" [Z{int(diff_z)}m]"
                    
                    if hydro_status == "Latéral" or hydro_status == "Indéterminé":
                        if diff_z < -3.0: hydro_status = "Aval (Topo)"
                        if diff_z > 3.0: hydro_status = "Amont (Topo)"
            
            # --- COLONNE 2 : HYDRO CONTEXT ---
            full_hydro = f"{hydro_status} sens pente{z_suffix}"
            logging.info(f"[{ident}] {full_hydro}")
            row['hydro_context'] = full_hydro
            
        except Exception:
            row['geo_dist_dir'] = "-"
            row['hydro_context'] = "-"
        return row

    logging.info("Calcul positions (2 threads)...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        rows = list(executor.map(process_geom, rows))
    
    return rows

def run_preview_logic(bbox, layers_list):
    results = []
    window = webview.active_window()
    logging.info(f"Recherche Preview: {layers_list}")
    
    for index, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        if not config: continue
        pct = int((index / len(layers_list)) * 100)
        
        msg = f"Chargement {config['label']}..."
        if window: window.evaluate_js(f"updateLoader({pct}, {json.dumps(msg)})")

        rows = fetch_features(layer_key, bbox, mode='preview')
        preview_items = []
        name_k = config["name_field"].lower()
        for r in rows:
            if r.get('LATITUDE_APPROX', 0) > 35:
                raw_nom = r.get(name_k)
                if not raw_nom or str(raw_nom).strip() == "" or raw_nom == "None":
                    raw_nom = r.get('bss_id') or r.get('code_bss') or r.get('id') or "Sans nom"
                preview_items.append({"nom": str(raw_nom), "color": config["color"], "geometry": r.get('geometry'), "details": r.get('niveau_eau_scrappe')})
        results.append({"layer": config['label'], "count": len(rows), "items": preview_items})

    if window:
        window.evaluate_js("updateLoader(100, 'Affichage...')")
        time.sleep(0.5)
        window.evaluate_js("hideLoader()")
    return results

def run_export_logic(bbox, layers_list, folder_name, base_path_ui):
    # 1. Récupération de la fenêtre pour communiquer avec l'UI
    window = webview.active_window()

    if base_path_ui and os.path.isdir(base_path_ui): base_path = base_path_ui
    elif getattr(sys, 'frozen', False): base_path = os.path.dirname(sys.executable)
    else: base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    folder = folder_name.strip() if folder_name else f"Export_{datetime.now().strftime('%H%M%S')}"
    path = os.path.join(base_path, folder)
    os.makedirs(path, exist_ok=True)
    
    summary = []

    # --- ETAPE 1 : ANALYSE GLOBALE (0-10%) ---
    logging.info("--- DÉBUT ANALYSE GLOBALE ---")
    if window: window.evaluate_js("updateLoader(5, 'Analyse du relief (Pente locale)...')")
    
    c_lat = (float(bbox['min_lat']) + float(bbox['max_lat'])) / 2.0
    c_lon = (float(bbox['min_lon']) + float(bbox['max_lon'])) / 2.0
    
    slope_azimut, slope_val = get_local_slope_vector(c_lat, c_lon)
    
    if window: window.evaluate_js("updateLoader(10, 'Récupération Altitude de référence...')")
    z_center, src_center = get_elevation_ign_only(c_lat, c_lon)
    
    if z_center: logging.info(f"Centre Z={z_center}m ({src_center})")
    logging.info("--- FIN ANALYSE GLOBALE -> TRAITEMENT COUCHES ---")

    # --- ETAPE 2 : BOUCLE SUR LES COUCHES (10-100%) ---
    total_layers = len(layers_list)
    
    for i, layer_key in enumerate(layers_list):
        config = LAYERS_CONFIG.get(layer_key)
        
        # Calcul du % d'avancement : On part de 10%, on répartit les 90% restants
        progress_start = 10 + int((i / total_layers) * 90)
        
        # UI : Début traitement couche
        msg = f"Traitement {config['label']}..."
        if window: window.evaluate_js(f"updateLoader({progress_start}, {json.dumps(msg)})")
        
        rows = fetch_features(layer_key, bbox, mode='export')
        
        # UI : Calculs géométriques (milieu de l'étape)
        if rows:
            msg_calc = f"Calculs géométriques {config['label']} ({len(rows)} objets)..."
            if window: window.evaluate_js(f"updateLoader({progress_start + 5}, {json.dumps(msg_calc)})")
            
        rows = calculate_geometrics(rows, bbox, slope_azimut, z_center)
        
        # UI : Génération Excel
        if window: window.evaluate_js(f"updateLoader({progress_start + 8}, {json.dumps('Génération Excel...')})")
        
        fname = f"{layer_key}.xlsx"
        full_path = os.path.join(path, fname)
        
        if rows:
            df = pd.DataFrame(rows)
            
            rename_map = {
                "code_metier": "Référence",
                "code_ssp": "Référence",
                "nom_etablissement": "Etablissement / Adresse",
                "etat_activite": "Etat d'occupation du site",
                "etat": "Etat d'occupation du site",
                "activite_principale": "Activité",
                "fiche_risque": "Fiche GéoRisques",
                "adresse": "Adresse",
                "code_postal": "Code Postal",
                "nom_commune": "Commune",
                "geo_dist_dir": "Distance / Position",
                "hydro_context": "Amont / Aval (Topo)"
            }
            df.rename(columns=rename_map, inplace=True)

            cols_to_exclude = [
                'nom_inventaire', 'code_inventaire', 'code_departement', 'nom_departement', 
                'code_region', 'nom_region', 'nature_localisation', 'x_wgs84', 'y_wgs84', 
                'code_siret', 'geometry', 'LATITUDE_APPROX', 'LONGITUDE_APPROX', 'boundedBy', 'id',
                'activite', 'type_activite', 'code_insee', 'position_relative'
            ]
            df = df.drop(columns=[c for c in cols_to_exclude if c in df.columns], errors='ignore')
            
            priority_cols = ["Référence", "Etablissement / Adresse", "Adresse", "Code Postal", "Commune", "Etat d'occupation du site", "Activité", "Distance / Position", "Amont / Aval (Topo)"]
            existing_priority = [c for c in priority_cols if c in df.columns]
            other_cols = [c for c in df.columns if c not in existing_priority]
            df = df[existing_priority + other_cols]

            try:
                writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
                df.to_excel(writer, index=False, sheet_name='Données')
                
                workbook = writer.book
                worksheet = writer.sheets['Données']
                
                header_fmt = workbook.add_format({'bold': True, 'fg_color': '#005b9e', 'font_color': 'white', 'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'})
                body_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'})
                center_fmt = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'})
                link_fmt = workbook.add_format({'color': 'blue', 'underline': 1, 'border': 1, 'valign': 'vcenter', 'align': 'center'})
                
                warning_fmt = workbook.add_format({
                    'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
                    'bg_color': '#fff9c4', 
                    'font_color': '#b45309' 
                })

                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_fmt)
                    width = 20
                    if "Etablissement" in str(value) or "Activité" in str(value) or "Adresse" in str(value): 
                        width = 40
                    if "Distance" in str(value): width = 30
                    if "Amont" in str(value): width = 30
                    worksheet.set_column(col_num, col_num, width)

                for row_num in range(len(df)):
                    for col_num in range(len(df.columns)):
                        col_name = df.columns[col_num]
                        val = df.iloc[row_num, col_num]
                        
                        if col_name == "Fiche GéoRisques" and pd.notnull(val) and str(val).startswith('http'):
                            worksheet.write_url(row_num + 1, col_num, val, link_fmt, string="Voir la fiche")
                        elif col_name in ["Référence", "Etat d'occupation du site", "Code Postal"]:
                            worksheet.write(row_num + 1, col_num, str(val) if pd.notnull(val) else "", center_fmt)
                        
                        elif col_name == "Amont / Aval (Topo)":
                             worksheet.write(row_num + 1, col_num, str(val) if pd.notnull(val) else "", warning_fmt)
                        
                        else:
                            worksheet.write(row_num + 1, col_num, str(val) if pd.notnull(val) else "", body_fmt)
                
                writer.close()

            except Exception as e:
                logging.error(f"Erreur Excel: {e}")
                df.to_excel(full_path, index=False)

        summary.append({"layer": config['label'], "count": len(rows), "filename": fname})
        
    # --- FIN : 100% ---
    if window: 
        window.evaluate_js("updateLoader(100, 'Export terminé !')")
        time.sleep(0.5) # Petite pause pour laisser l'utilisateur voir le 100%
        
    return {"folder": path, "summary": summary}

def get_ui_content():
    checkboxes_html = ""
    for k, c in LAYERS_CONFIG.items():
        checkboxes_html += f'''
        <div class="checkbox-wrapper">
            <input type="checkbox" id="chk_{k}" value="{k}" checked>
            <label for="chk_{k}" style="color:{c["color"]}">{c["label"]}</label>
        </div>
        '''
    template = core.load_template("geotoolbox.html")
    return template.replace("{{CHECKBOXES}}", checkboxes_html)