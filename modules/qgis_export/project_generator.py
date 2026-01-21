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


def _get_vector_layer_xml(layer_path: str, layer_name: str, layer_id: str) -> str:
    """Create vector layer XML."""
    colors = {
        "BSS": "31,120,180,255",
        "SSP": "227,26,28,255", 
        "SIS": "255,127,0,255",
        "ICPE": "106,61,154,255",
    }
    color = colors.get(layer_name, "51,160,44,255")
    
    return f'''<maplayer simplifyLocal="1" autoRefreshTime="0" readOnly="0" type="vector" refreshOnNotifyMessage="" legendPlaceholderImage="" symbologyReferenceScale="-1" styleCategories="AllStyleCategories" labelsEnabled="0" geometry="Point" autoRefreshMode="Disabled" wkbType="Point" hasScaleBasedVisibilityFlag="0" refreshOnNotifyEnabled="0" simplifyAlgorithm="0" simplifyDrawingHints="0" maxScale="0" minScale="100000000" simplifyDrawingTol="1" simplifyMaxScale="1">
      <extent>
        <xmin>-180</xmin>
        <ymin>-90</ymin>
        <xmax>180</xmax>
        <ymax>90</ymax>
      </extent>
      <wgs84extent>
        <xmin>-180</xmin>
        <ymin>-90</ymin>
        <xmax>180</xmax>
        <ymax>90</ymax>
      </wgs84extent>
      <id>{layer_id}</id>
      <datasource>./{layer_path}</datasource>
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
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <expressionfields/>
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
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" value="" name="name"/>
                  <Option name="properties"/>
                  <Option type="QString" value="collection" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
    </maplayer>'''


def _get_xyz_layer_xml(url: str, layer_name: str, layer_id: str, zmax: int = 19) -> str:
    """Create XYZ tile layer XML for QGIS 3.34+."""
    return f'''<maplayer autoRefreshTime="0" type="raster" refreshOnNotifyMessage="" legendPlaceholderImage="" styleCategories="AllStyleCategories" autoRefreshMode="Disabled" hasScaleBasedVisibilityFlag="0" refreshOnNotifyEnabled="0" maxScale="0" minScale="1e+08">
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
    project_name: str = "GeoToolbox Export"
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
            rel_path = os.path.relpath(vpath, os.path.dirname(project_path))
            
            map_layers_xml.append(_get_vector_layer_xml(rel_path, layer_name, layer_id))
            data_tree_xml.append(_get_layer_tree_item(layer_name, layer_id, True, "ogr"))
        
        # Basemaps
        basemaps = [
            ("OpenStreetMap", "https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png", 19, True),
            ("Google Satellite", "https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D", 20, False),
        ]
        
        for name, url, zmax, checked in basemaps:
            layer_id = _generate_layer_id(name.replace(" ", "_"))
            basemap_layers_xml.append(_get_xyz_layer_xml(url, name, layer_id, zmax))
            basemap_tree_xml.append(_get_layer_tree_item(name, layer_id, checked, "wms"))
        
        # Build full project XML
        project_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="{project_name}" version="3.34.0-Prizren" saveDateTime="{datetime.now().isoformat()}" saveUser="GeoToolbox" saveUserFull="GeoToolbox">
  <homePath path=""/>
  <title>{project_name}</title>
  <transaction mode="Disabled"/>
  <projectFlags set="TrustStoredLayerStatistics"/>
  <projectCrs>
    <spatialrefsys nativeFormat="Wkt">
      <wkt>PROJCRS["RGF93 v1 / CC49",BASEGEOGCRS["RGF93 v1",DATUM["Reseau Geodesique Francais 1993 v1",ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4171]],CONVERSION["France CC zone 9",METHOD["Lambert Conic Conformal (2SP)",ID["EPSG",9802]],PARAMETER["Latitude of false origin",49,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8821]],PARAMETER["Longitude of false origin",3,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8822]],PARAMETER["Latitude of 1st standard parallel",48.25,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Latitude of 2nd standard parallel",49.75,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8824]],PARAMETER["Easting at false origin",1700000,LENGTHUNIT["metre",1],ID["EPSG",8826]],PARAMETER["Northing at false origin",8200000,LENGTHUNIT["metre",1],ID["EPSG",8827]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Cadastre, engineering survey, topographic mapping (large and medium scale)."],AREA["France - mainland onshore between 48 N and 50 N."],BBOX[48,-4.87,50.18,8.23]],ID["EPSG",3949]]</wkt>
      <proj4>+proj=lcc +lat_0=49 +lon_0=3 +lat_1=48.25 +lat_2=49.75 +x_0=1700000 +y_0=8200000 +ellps=GRS80 +units=m +no_defs</proj4>
      <srsid>3949</srsid>
      <srid>3949</srid>
      <authid>EPSG:3949</authid>
      <description>RGF93 v1 / CC49</description>
      <projectionacronym>lcc</projectionacronym>
      <ellipsoidacronym>EPSG:7019</ellipsoidacronym>
      <geographicflag>false</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <layer-tree-group>
    <customproperties>
      <Option/>
    </customproperties>
    <layer-tree-group name="Données" checked="Qt::Checked" expanded="1">
      <customproperties>
        <Option/>
      </customproperties>
      {"".join(data_tree_xml)}
    </layer-tree-group>
    <layer-tree-group name="Fonds de carte" checked="Qt::Checked" expanded="0">
      <customproperties>
        <Option/>
      </customproperties>
      {"".join(basemap_tree_xml)}
    </layer-tree-group>
    <custom-order enabled="0"/>
  </layer-tree-group>
  <snapping-settings enabled="0" type="1" mode="2" unit="1" tolerance="12" self-snapping="0" intersection-snapping="0" maxScale="0" minScale="0" scaleDependencyMode="0">
    <individual-layer-settings/>
  </snapping-settings>
  <relations/>
  <polymorphicRelations/>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>meters</units>
    <extent>
      <xmin>1650000</xmin>
      <ymin>8150000</ymin>
      <xmax>1750000</xmax>
      <ymax>8250000</ymax>
    </extent>
    <rotation>0</rotation>
    <destinationsrs>
      <spatialrefsys nativeFormat="Wkt">
        <wkt>PROJCRS["RGF93 v1 / CC49",BASEGEOGCRS["RGF93 v1",DATUM["Reseau Geodesique Francais 1993 v1",ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4171]],CONVERSION["France CC zone 9",METHOD["Lambert Conic Conformal (2SP)",ID["EPSG",9802]],PARAMETER["Latitude of false origin",49,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8821]],PARAMETER["Longitude of false origin",3,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8822]],PARAMETER["Latitude of 1st standard parallel",48.25,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Latitude of 2nd standard parallel",49.75,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8824]],PARAMETER["Easting at false origin",1700000,LENGTHUNIT["metre",1],ID["EPSG",8826]],PARAMETER["Northing at false origin",8200000,LENGTHUNIT["metre",1],ID["EPSG",8827]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Cadastre, engineering survey, topographic mapping (large and medium scale)."],AREA["France - mainland onshore between 48 N and 50 N."],BBOX[48,-4.87,50.18,8.23]],ID["EPSG",3949]]</wkt>
        <proj4>+proj=lcc +lat_0=49 +lon_0=3 +lat_1=48.25 +lat_2=49.75 +x_0=1700000 +y_0=8200000 +ellps=GRS80 +units=m +no_defs</proj4>
        <srsid>3949</srsid>
        <srid>3949</srid>
        <authid>EPSG:3949</authid>
        <description>RGF93 v1 / CC49</description>
        <projectionacronym>lcc</projectionacronym>
        <ellipsoidacronym>EPSG:7019</ellipsoidacronym>
        <geographicflag>false</geographicflag>
      </spatialrefsys>
    </destinationsrs>
    <rendermaptile>0</rendermaptile>
  </mapcanvas>
  <legend updateDrawingOrder="true">
    <legendgroup checked="Qt::Checked" name="Données" open="true"/>
    <legendgroup checked="Qt::Checked" name="Fonds de carte" open="false"/>
  </legend>
  <projectModels/>
  <maplayers>
    {"".join(map_layers_xml)}
    {"".join(basemap_layers_xml)}
  </maplayers>
  <layerorder/>
  <properties>
    <Digitizing>
      <AvoidIntersectionsMode type="int">0</AvoidIntersectionsMode>
    </Digitizing>
    <Gui>
      <CanvasColorBluePart type="int">255</CanvasColorBluePart>
      <CanvasColorGreenPart type="int">255</CanvasColorGreenPart>
      <CanvasColorRedPart type="int">255</CanvasColorRedPart>
      <SelectionColorAlphaPart type="int">255</SelectionColorAlphaPart>
      <SelectionColorBluePart type="int">0</SelectionColorBluePart>
      <SelectionColorGreenPart type="int">255</SelectionColorGreenPart>
      <SelectionColorRedPart type="int">255</SelectionColorRedPart>
    </Gui>
    <Measure>
      <Ellipsoid type="QString">EPSG:7019</Ellipsoid>
    </Measure>
    <SpatialRefSys>
      <ProjectionsEnabled type="int">1</ProjectionsEnabled>
    </SpatialRefSys>
    <WMSServiceTitle type="QString">{project_name}</WMSServiceTitle>
  </properties>
  <visibility-presets/>
  <transformContext/>
  <projectMetadata>
    <identifier></identifier>
    <parentidentifier></parentidentifier>
    <language>fr</language>
    <type></type>
    <title>{project_name}</title>
    <abstract>Projet généré automatiquement par GéoToolbox</abstract>
    <author>GéoToolbox</author>
    <creation>{datetime.now().isoformat()}</creation>
  </projectMetadata>
  <Annotations/>
  <Layouts/>
  <Bookmarks/>
  <ProjectViewSettings UseProjectScales="0" rotation="0">
    <Scales/>
  </ProjectViewSettings>
  <ProjectTimeSettings timeStepUnit="h" cumulativeTemporalRange="0" frameRate="1" timeStep="1"/>
  <ProjectDisplaySettings>
    <BearingFormat id="bearing">
      <Option type="Map">
        <Option type="QChar" value="" name="decimal_separator"/>
        <Option type="int" value="6" name="decimals"/>
        <Option type="int" value="0" name="direction_format"/>
        <Option type="int" value="0" name="rounding_type"/>
        <Option type="bool" value="false" name="show_plus"/>
        <Option type="bool" value="true" name="show_thousand_separator"/>
        <Option type="bool" value="false" name="show_trailing_zeros"/>
        <Option type="QChar" value="" name="thousand_separator"/>
      </Option>
    </BearingFormat>
    <GeographicCoordinateFormat id="geographiccoordinate">
      <Option type="Map">
        <Option type="QChar" value="" name="decimal_separator"/>
        <Option type="int" value="6" name="decimals"/>
        <Option type="int" value="0" name="direction_format"/>
        <Option type="int" value="0" name="rounding_type"/>
        <Option type="bool" value="false" name="show_plus"/>
        <Option type="bool" value="true" name="show_thousand_separator"/>
        <Option type="bool" value="false" name="show_trailing_zeros"/>
        <Option type="QChar" value="" name="thousand_separator"/>
      </Option>
    </GeographicCoordinateFormat>
  </ProjectDisplaySettings>
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
    new_vector_layers: List[str] = None
) -> bool:
    """Update an existing QGIS project."""
    return generate_qgis_project(
        project_path,
        vector_layers=new_vector_layers or [],
        raster_layers=new_raster_layers or []
    )
