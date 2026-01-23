"""
Geometric Calculations

Mathematical functions for geometric analysis: slope, elevation, 
distance calculations, and position analysis (upstream/downstream).

Migrated from: modules/geotoolbox_core/maths.py
"""

import math
import time
import logging
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from modules import core


@lru_cache(maxsize=512)
def get_elevation_ign_only(lat, lon):
    """
    Récupère l'altitude via l'API IGN Géoplateforme avec gestion des limites.
    Retourne un COUPLE : (Altitude_float, Nom_source_str)
    
    Performance: Uses @lru_cache to memoize results for repeated coordinate lookups.
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
    
    Performance: Uses parallel API calls for 4x speedup (4 calls in ~0.3s instead of ~1.2s).
    """
    logging.info("Calcul du vecteur pente local (pas de 150m)...")

    D = 150
    d_lat = D / 111111.0
    d_lon = D / (111111.0 * math.cos(math.radians(c_lat)))

    # Parallel elevation API calls for 4x speedup
    coords = [
        (c_lat + d_lat, c_lon),  # North
        (c_lat - d_lat, c_lon),  # South
        (c_lat, c_lon + d_lon),  # East
        (c_lat, c_lon - d_lon),  # West
    ]
    
    def fetch_elevation(coord_tuple):
        return get_elevation_ign_only(coord_tuple[0], coord_tuple[1])
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_elevation, coords))
    
    z_n, z_s, z_e, z_w = [r[0] for r in results]

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
