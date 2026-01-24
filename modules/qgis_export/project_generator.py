"""
QGIS Project Generator.

Creates .qgz project files compatible with QGIS 3.34+ with basemaps and proper projection.
"""

import os
import logging
import zipfile
from datetime import datetime
from typing import List, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


def _generate_layer_id(layer_name: str) -> str:
    """Generate a unique layer ID."""
    uid = str(uuid.uuid4()).replace('-', '')[:12]
    return f"{layer_name.replace(' ', '_')}_{uid}"


def _get_mercator_bounds(min_lat, min_lon, max_lat, max_lon):
    """Convert LatLon bbox to Web Mercator (EPSG:3857) bounds roughly."""
    import math
    
    def lat_to_y(lat):
        if lat > 89.5: lat = 89.5
        if lat < -89.5: lat = -89.5
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137

    def lon_to_x(lon):
        return math.radians(lon) * 6378137

    return (
        lon_to_x(min_lon),
        lat_to_y(min_lat),
        lon_to_x(max_lon),
        lat_to_y(max_lat)
    )




def _get_mercator_bounds(min_lat, min_lon, max_lat, max_lon):
    """Convert LatLon bbox to Web Mercator (EPSG:3857) bounds roughly."""
    import math
    
    def lat_to_y(lat):
        if lat > 89.5: lat = 89.5
        if lat < -89.5: lat = -89.5
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137

    def lon_to_x(lon):
        return math.radians(lon) * 6378137

    return (
        lon_to_x(min_lon),
        lat_to_y(min_lat),
        lon_to_x(max_lon),
        lat_to_y(max_lat)
    )


def _get_vector_layer_xml(layer_path: str, layer_name: str, layer_id: str) -> str:
    """Create vector layer XML (Generic Extent)."""
    colors = {
        "BSS": "31,120,180,255",
        "SSP": "227,26,28,255", 
        "SIS": "255,127,0,255",
        "ICPE": "106,61,154,255",
    }
    color = colors.get(layer_name, "51,160,44,255")
    
    return f'''<maplayer simplifyLocal="1" autoRefreshTime="0" readOnly="0" type="vector" refreshOnNotifyMessage="" legendPlaceholderImage="" symbologyReferenceScale="-1" styleCategories="AllStyleCategories" labelsEnabled="0" geometry="Unknown" autoRefreshMode="Disabled" wkbType="Unknown" hasScaleBasedVisibilityFlag="0" refreshOnNotifyEnabled="0" simplifyAlgorithm="0" simplifyDrawingHints="0" maxScale="0" minScale="100000000" simplifyDrawingTol="1" simplifyMaxScale="1">
      <id>{layer_id}</id>
      <datasource>{layer_path}</datasource>
      <layername>{layer_name}</layername>
      <srs>
        <spatialrefsys nativeFormat="Wkt">
          <wkt>GEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]</wkt>
          <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
          <srsid>3452</srsid>
          <srid>4326</srid>
          <authid>EPSG:4326</authid>
          <description>WGS 84</description>
          <projectionacronym>longlat</projectionacronym>
          <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
          <geographicflag>true</geographicflag>
        </spatialrefsys>
      </srs>
      <provider encoding="UTF-8">ogr</provider>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
        <symbols>
          <symbol type="marker" alpha="1" clip_to_extent="1" name="0" force_rhr="0" is_animated="0" frame_rate="10">
            <layer class="SimpleMarker" enabled="1" locked="0" pass="0" id="0">
              <Option type="Map">
                <Option type="QString" value="0" name="angle"/>
                <Option type="QString" value="square" name="cap_style"/>
                <Option type="QString" value="{color}" name="color"/>
                <Option type="QString" value="1" name="horizontal_anchor_point"/>
                <Option type="QString" value="bevel" name="joinstyle"/>
                <Option type="QString" value="circle" name="name"/>
                <Option type="QString" value="0,0" name="offset"/>
                <Option type="QString" value="MM" name="offset_unit"/>
                <Option type="QString" value="35,35,35,255" name="outline_color"/>
                <Option type="QString" value="solid" name="outline_style"/>
                <Option type="QString" value="0.4" name="outline_width"/>
                <Option type="QString" value="MM" name="outline_width_unit"/>
                <Option type="QString" value="diameter" name="scale_method"/>
                <Option type="QString" value="3" name="size"/>
                <Option type="QString" value="MM" name="size_unit"/>
                <Option type="QString" value="1" name="vertical_anchor_point"/>
              </Option>
            </layer>
          </symbol>
          <!-- Additional generic symbols can be added here if needed, but keeping it simple -->
        </symbols>
      </renderer-v2>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
    </maplayer>'''



def _get_raster_layer_xml(layer_path: str, layer_name: str, layer_id: str) -> str:
    """Create raster layer XML (Generic Extent)."""
    return f'''<maplayer autoRefreshTime="0" type="raster" refreshOnNotifyMessage="" legendPlaceholderImage="" styleCategories="AllStyleCategories" autoRefreshMode="Disabled" hasScaleBasedVisibilityFlag="0" refreshOnNotifyEnabled="0" maxScale="0" minScale="1e+08">
      <id>{layer_id}</id>
      <datasource>{layer_path}</datasource>
      <layername>{layer_name}</layername>
      <provider>gdal</provider>
      <pipe>
        <provider>
          <resampling zoomedInResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour"/>
        </provider>
        <rasterrenderer opacity="1" nodataColor="" alphaBand="-1" type="multibandcolor">
          <rasterTransparency/>
          <redBand>1</redBand>
          <greenBand>2</greenBand>
          <blueBand>3</blueBand>
        </rasterrenderer>
      </pipe>
    </maplayer>'''


def _get_xyz_layer_xml(url: str, layer_name: str, layer_id: str, zmax: int = 19) -> str:
    """Create XYZ tile layer XML (Full World Extent)."""
    return f'''<maplayer autoRefreshTime="0" type="raster" refreshOnNotifyMessage="" legendPlaceholderImage="" styleCategories="AllStyleCategories" autoRefreshMode="Disabled" hasScaleBasedVisibilityFlag="0" refreshOnNotifyEnabled="0" maxScale="0" minScale="1e+08">
      <extent>
        <xmin>-20037508.342789244</xmin>
        <ymin>-20037508.342789255</ymin>
        <xmax>20037508.342789244</xmax>
        <ymax>20037508.342789244</ymax>
      </extent>
      <id>{layer_id}</id>
      <datasource>crs=EPSG:3857&amp;format&amp;type=xyz&amp;url={url}&amp;zmax={zmax}&amp;zmin=0</datasource>
      <layername>{layer_name}</layername>
      <srs>
        <spatialrefsys nativeFormat="Wkt">
          <wkt>PROJCRS["WGS 84 / Pseudo-Mercator",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["Popular Visualisation Pseudo-Mercator",METHOD["Popular Visualisation Pseudo Mercator",ID["EPSG",1024]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Web mapping and visualisation."],AREA["World between 85.06 S and 85.06 N."],BBOX[-85.06,-180,85.06,180]],ID["EPSG",3857]]</wkt>
          <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs</proj4>
          <srsid>3857</srsid>
          <srid>3857</srid>
          <authid>EPSG:3857</authid>
          <description>WGS 84 / Pseudo-Mercator</description>
          <projectionacronym>merc</projectionacronym>
          <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
          <geographicflag>false</geographicflag>
        </spatialrefsys>
      </srs>
      <provider>wms</provider>
      <pipe-data-defined-properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option name="properties"/>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </pipe-data-defined-properties>
      <pipe>
        <provider>
          <resampling zoomedInResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour"/>
        </provider>
        <rasterrenderer opacity="1" nodataColor="" alphaBand="-1" type="singlebandcolordata" band="1">
          <rasterTransparency/>
        </rasterrenderer>
        <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
        <huesaturation colorizeRed="255" saturation="0" colorizeBlue="128" grayscaleMode="0" colorizeStrength="100" colorizeOn="0" colorizeGreen="128" invertColors="0"/>
        <rasterresampler maxOversampling="2"/>
        <resamplingStage>resamplingFilter</resamplingStage>
      </pipe>
      <blendMode>0</blendMode>
    </maplayer>'''


def _get_layer_tree_item(layer_name: str, layer_id: str, checked: bool = True, provider: str = "ogr") -> str:
    """Create layer tree item XML."""
    check = "Qt::Checked" if checked else "Qt::Unchecked"
    return f'''<layer-tree-layer legend_split_behavior="0" id="{layer_id}" legend_exp="" patch_size="-1,-1" name="{layer_name}" checked="{check}" providerKey="{provider}" source="" expanded="0">
        <customproperties>
          <Option/>
        </customproperties>
      </layer-tree-layer>'''


def generate_qgis_project(
    project_path: str,
    vector_layers: List[str] = None,
    raster_layers: List[str] = None,
    project_name: str = "GeoToolbox Export",
    bbox: Dict = None
) -> bool:
    """Generate a QGIS 3.34+ compatible project file (.qgz)."""
    vector_layers = vector_layers or []
    raster_layers = raster_layers or []
    
    try:
        # Build layer XMLs
        map_layers_xml = []
        data_tree_xml = []
        basemap_tree_xml = []
        basemap_layers_xml = []
        
        # Vector layers
        for vpath in vector_layers:
            layer_name = os.path.splitext(os.path.basename(vpath))[0]
            layer_id = _generate_layer_id(layer_name)
            
            # Normalize path to POSIX for QGIS XML
            rel_path = os.path.relpath(vpath, os.path.dirname(project_path))
            rel_path = rel_path.replace('\\', '/')
            
            map_layers_xml.append(_get_vector_layer_xml(rel_path, layer_name, layer_id))
            data_tree_xml.append(_get_layer_tree_item(layer_name, layer_id, True, "ogr"))
            
        # Raster layers
        for rpath in raster_layers:
            layer_name = os.path.splitext(os.path.basename(rpath))[0]
            layer_id = _generate_layer_id(layer_name)
            
            rel_path = os.path.relpath(rpath, os.path.dirname(project_path))
            rel_path = rel_path.replace('\\', '/')
            
            map_layers_xml.append(_get_raster_layer_xml(rel_path, layer_name, layer_id))
            data_tree_xml.append(_get_layer_tree_item(layer_name, layer_id, True, "gdal"))
        
        # Basemaps
        basemaps = [
            ("OpenStreetMap", "https://tile.openstreetmap.org/{z}/{x}/{y}.png", 19, True),
            ("Google Satellite", "https://mt1.google.com/vt/lyrs=s&amp;x={x}&amp;y={y}&amp;z={z}", 20, False),
        ]
        
        for name, url, zmax, checked in basemaps:
            layer_id = _generate_layer_id(name.replace(" ", "_"))
            basemap_layers_xml.append(_get_xyz_layer_xml(url, name, layer_id, zmax))
            basemap_tree_xml.append(_get_layer_tree_item(name, layer_id, checked, "wms"))
            
        # Calculate Extent (Default to World if None)
        if bbox:
            minx, miny, maxx, maxy = _get_mercator_bounds(
                bbox.get('min_lat', 40), bbox.get('min_lon', -5),
                bbox.get('max_lat', 51), bbox.get('max_lon', 10)
            )
            # Add padding
            w = maxx - minx
            h = maxy - miny
            minx -= w * 0.1
            maxx += w * 0.1
            miny -= h * 0.1
            maxy += h * 0.1
        else:
            # France Extent approx (Web Mercator)
            minx, miny, maxx, maxy = -600000, 5000000, 1000000, 6600000

        # Build full project XML (Using EPSG:3857 for compatibility)
        project_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="{project_name}" version="3.34.0-Prizren" saveDateTime="{datetime.now().isoformat()}" saveUser="GeoToolbox" saveUserFull="GeoToolbox">
  <title>{project_name}</title>
  <transaction mode="Disabled"/>
  <projectCrs>
    <spatialrefsys nativeFormat="Wkt">
      <wkt>PROJCRS["WGS 84 / Pseudo-Mercator",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["Popular Visualisation Pseudo-Mercator",METHOD["Popular Visualisation Pseudo Mercator",ID["EPSG",1024]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Web mapping and visualisation."],AREA["World between 85.06 S and 85.06 N."],BBOX[-85.06,-180,85.06,180]],ID["EPSG",3857]]</wkt>
      <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs</proj4>
      <srsid>3857</srsid>
      <srid>3857</srid>
      <authid>EPSG:3857</authid>
      <description>WGS 84 / Pseudo-Mercator</description>
      <projectionacronym>merc</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>false</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <layer-tree-group>
    <customproperties/>
    <layer-tree-group name="Données" checked="Qt::Checked" expanded="1">
      <customproperties/>
      {"".join(data_tree_xml)}
    </layer-tree-group>
    <layer-tree-group name="Fonds de carte" checked="Qt::Checked" expanded="0">
      <customproperties/>
      {"".join(basemap_tree_xml)}
    </layer-tree-group>
  </layer-tree-group>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>meters</units>
    <extent>
      <xmin>{minx}</xmin>
      <ymin>{miny}</ymin>
      <xmax>{maxx}</xmax>
      <ymax>{maxy}</ymax>
    </extent>
    <destinationsrs>
      <spatialrefsys nativeFormat="Wkt">
        <wkt>PROJCRS["WGS 84 / Pseudo-Mercator",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["Popular Visualisation Pseudo-Mercator",METHOD["Popular Visualisation Pseudo Mercator",ID["EPSG",1024]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Web mapping and visualisation."],AREA["World between 85.06 S and 85.06 N."],BBOX[-85.06,-180,85.06,180]],ID["EPSG",3857]]</wkt>
        <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs</proj4>
        <srsid>3857</srsid>
        <srid>3857</srid>
        <authid>EPSG:3857</authid>
        <description>WGS 84 / Pseudo-Mercator</description>
        <projectionacronym>merc</projectionacronym>
        <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
        <geographicflag>false</geographicflag>
      </spatialrefsys>
    </destinationsrs>
  </mapcanvas>
  <legend updateDrawingOrder="true">
    <legendgroup checked="Qt::Checked" name="Données" open="true"/>
    <legendgroup checked="Qt::Checked" name="Fonds de carte" open="false"/>
  </legend>
  <maplayers>
    {"".join(map_layers_xml)}
    {"".join(basemap_layers_xml)}
  </maplayers>
</qgis>'''
        
        # Ensure .qgz extension
        if project_path.endswith('.qgs'):
            project_path = project_path[:-4] + '.qgz'
        elif not project_path.endswith('.qgz'):
            project_path += '.qgz'
        
        qgs_filename = os.path.basename(project_path).replace('.qgz', '.qgs')
        
        with zipfile.ZipFile(project_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(qgs_filename, project_xml)
        
        total_layers = len(vector_layers) + len(raster_layers) + len(basemaps)
        logger.info(f"[QGIS Export] Created project: {project_path} ({total_layers} layers)")
        return True
        
    except Exception as e:
        logger.error(f"[QGIS Export] Failed to create project: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_qgis_project(
    project_path: str,
    new_raster_layers: List[str] = None,
    new_vector_layers: List[str] = None,
    bbox: Dict = None
) -> bool:
    """Update an existing QGIS project."""
    return generate_qgis_project(
        project_path,
        vector_layers=new_vector_layers or [],
        raster_layers=new_raster_layers or [],
        bbox=bbox
    )
