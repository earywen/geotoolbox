"""
XML/JSON Parsers

Parsing functions for WFS responses and other data formats.

Migrated from: modules/geotoolbox_core/parsers.py
"""

import xml.etree.ElementTree as ET
import re
import logging

def smart_fix_coords_france(lat, lon):
    """Fix coordinate order for France (handles WFS axis order issues)."""
    try:
        val1 = float(lat)
        val2 = float(lon)
    except (ValueError, TypeError):
        return None, None
    if abs(val1) > 180 or abs(val2) > 180: return None, None
    if (val1 < 20 and val2 > 35): return val2, val1
    return val1, val2

def parse_gml_coord_string(text, is_poslist=False, dimension_hint=2):
    """Parse GML coordinate strings into point lists."""
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
    except Exception:
        pass
    return points

def parse_geometry_hybrid(element):
    """Parse various GML geometry formats into GeoJSON."""
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

        # --- SUPPORT LIGNES (LineString / Curve) ---
        lines_tags = element.findall(".//LineString") + element.findall(".//Curve") + element.findall(".//LineStringSegment")
        if lines_tags:
            all_line_points = []
            geojson_lines = []
            for line in lines_tags:
                l_pts = []
                c_tag = line.find(".//coordinates")
                if c_tag is not None and c_tag.text:
                    l_pts = parse_gml_coord_string(c_tag.text, is_poslist=False)
                else:
                    p_tag = line.find(".//posList")
                    if p_tag is not None and p_tag.text:
                         dim = 2
                         if 'srsDimension="3"' in str(ET.tostring(p_tag)) or len(p_tag.text.split()) % 3 == 0: dim = 3
                         l_pts = parse_gml_coord_string(p_tag.text, is_poslist=True, dimension_hint=dim)

                if l_pts:
                    geojson_lines.append(l_pts)
                    all_line_points.extend(l_pts)

            if geojson_lines and all_line_points:
                avg_lon = sum(p[0] for p in all_line_points) / len(all_line_points)
                avg_lat = sum(p[1] for p in all_line_points) / len(all_line_points)
                if len(geojson_lines) == 1:
                    return {"type": "LineString", "coordinates": geojson_lines[0]}, avg_lat, avg_lon
                else:
                    return {"type": "MultiLineString", "coordinates": geojson_lines}, avg_lat, avg_lon

        # --- SUPPORT POLYGONS ---
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
    except Exception:
        return None, 0, 0

def parse_gml_response(xml_text):
    """Parse complete GML WFS response into feature list."""
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
                tag_raw = child.tag
                if '}' in tag_raw:
                    tag_raw = tag_raw.split('}', 1)[1]

                tag_clean = tag_raw.lower().strip()

                if "geometry" not in tag_clean and "boundedby" not in tag_clean:
                    if child.text: props[tag_clean] = child.text.strip()
            if geojson_geom:
                props['geometry'] = geojson_geom
                props['LATITUDE_APPROX'] = lat_center
                props['LONGITUDE_APPROX'] = lon_center
                if "code_bss" in props: props["bss_id"] = props["code_bss"]
                if "code_ssp" in props: props["id"] = props["code_ssp"]

                # --- FORMATAGE SPÉCIFIQUE PARCELLES ---
                if "section" in props and "numero" in props:
                    lbl = f"Section {props['section']} n°{props['numero']}"
                    if "contenance" in props:
                        lbl += f" ({props['contenance']} m²)"
                    props["label_parcelle"] = lbl

                rows.append(props)
    except Exception as e: logging.error(f"Erreur XML: {e}")
    return rows


# Alias for backward compatibility
def parse_wfs_response(response_text, format_type="json"):
    """Parse WFS response (wrapper for parse_gml_response)."""
    if format_type == "json":
        import json
        try:
            data = json.loads(response_text)
            return data.get('features', [])
        except:
            return []
    return parse_gml_response(response_text)
