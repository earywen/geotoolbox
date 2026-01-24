"""
QGIS Style Generator (.qml)
Generates customized .qml files for vector layers.
"""

import logging

logger = logging.getLogger(__name__)

def hex_to_rgba(hex_color: str, opacity: float = 1.0) -> str:
    """Convert hex color (#RRGGBB) to 'r,g,b,a' string (0-255)."""
    hex_clean = hex_color.lstrip('#')
    if len(hex_clean) != 6:
        return "0,0,0,255"
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    a = int(opacity * 255)
    return f"{r},{g},{b},{a}"


def _get_labeling_xml(field: str, size: float = 8.0, buffer_size: float = 1.0) -> str:
    """Generate XML for simple labeling with buffer."""
    if not field:
        return "<labeling type=\"simple\"/>"
        
    return f"""<labeling type="simple">
    <settings calloutType="simple">
      <text-style fontLetterSpacing="0" textColor="0,0,0,255" fontSizeUnit="Point" namedStyle="Regular" fontFamily="Arial" fontSize="{size}" fontWordSpacing="0" textOpacity="1" blendMode="0" multilineHeight="1" previewBkgrdColor="255,255,255,255" fieldName="{field}" fontStrikeout="0" fontItalic="0" fontWeight="50" fontKerning="1" isExpression="0" fontUnderline="0" useSubstitutions="0" allowHtml="0" textOrientation="horizontal" caps="0">
        <text-buffer bufferSize="{buffer_size}" bufferJoinStyle="128" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="1" bufferOpacity="1" bufferColor="255,255,255,255" bufferBlendMode="0" bufferNoFill="1" bufferSizeUnits="MM"/>
        <text-mask maskSize="0" maskEnabled="0" maskOpacity="1" maskSizeUnits="MM" maskType="0" maskedSymbolLayers="" maskJoinStyle="128" maskSizeMapUnitScale="3x:0,0,0,0,0,0"/>
        <background shapeFillColor="255,255,255,255" shapeBorderWidth="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeBorderColor="128,128,128,255" shapeType="0" shapeSVGFile="" shapeOffsetX="0" shapeOffsetY="0" shapeSizeX="0" shapeSizeY="0" shapeRotationType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeBlendMode="0" shapeDraw="0" shapeRotation="0" shapeSizeType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetUnit="MM" shapeSizeUnit="MM" shapeJoinStyle="64" shapeBorderWidthUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiUnit="MM" shapeRadiiX="0" shapeRadiiY="0"/>
        <shadow shadowOffsetGlobal="1" shadowRadiusAlphaOnly="0" shadowOffsetAngle="135" shadowUnder="0" shadowRadius="1.5" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowOpacity="0.7" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255" shadowRadiusUnit="MM" shadowDraw="0" shadowBlendMode="6" shadowOffsetUnit="MM" shadowOffsetDist="1"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format wrapChar="" placeDirectionSymbol="0" plussign="0" leftDirectionSymbol="&lt;" rightDirectionSymbol="&gt;" multilineAlign="0" formatNumbers="0" addDirectionSymbol="0" reverseDirectionSymbol="0" decimals="3" useMaxLineLengthForAutoWrap="1" autoWrapLength="0"/>
      <placement repeatDistance="0" placement="0" maxCurvedCharAngleIn="25" maxCurvedCharAngleOut="-25" dist="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" geometryGeneratorType="PointGeometry" centroidInside="0" centroidWhole="0" offsetType="0" placementFlags="10" distMapUnitScale="3x:0,0,0,0,0,0" geometryGenerator="" priority="5" distUnits="MM" layerType="PointGeometry" xOffset="0" rotationAngle="0" repeatDistanceUnits="MM" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" preserveRotation="1" geometryGeneratorEnabled="0" fitInPolygonOnly="0" yOffset="0"/>
      <rendering scaleMax="0" scaleMin="0" fontMinPixelSize="3" maxNumLabels="2000" fontMaxPixelSize="10000" scaleVisibility="0" minFeatureSize="0" upsidedownLabels="0" mergeLines="0" limitNumLabels="0" labelPerPart="0" obstacleType="1" obstacle="1" displayAll="0" zIndex="0" drawLabels="1" fontLimitPixelSize="0" obstacleFactor="1"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option name="properties"/>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" value="pole_of_inaccessibility" name="anchorPoint"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" value="" name="name"/>
            <Option name="properties"/>
            <Option type="QString" value="collection" name="type"/>
          </Option>
          <Option type="bool" value="false" name="drawToAllParts"/>
          <Option type="QString" value="0" name="enabled"/>
          <Option type="QString" value="point_on_exterior" name="labelAnchorPoint"/>
          <Option type="QString" value="&lt;symbol type=&quot;line&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot; name=&quot;symbol&quot; force_rhr=&quot;0&quot; is_animated=&quot;0&quot; frame_rate=&quot;10&quot;&gt;&lt;layer class=&quot;SimpleLine&quot; enabled=&quot;1&quot; locked=&quot;0&quot; pass=&quot;0&quot; id=&quot;0&quot;&gt;&lt;Option type=&quot;Map&quot;&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;align_dash_pattern&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;square&quot; name=&quot;capstyle&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;5;2&quot; name=&quot;customdash&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;customdash_map_unit_scale&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;customdash_unit&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;dash_pattern_offset&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;dash_pattern_offset_unit&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;draw_inside_polygon&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;bevel&quot; name=&quot;joinstyle&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;60,60,60,255&quot; name=&quot;line_color&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;solid&quot; name=&quot;line_style&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0.3&quot; name=&quot;line_width&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;line_width_unit&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;offset&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;offset_map_unit_scale&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;offset_unit&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;ring_filter&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_end&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_end_map_unit_scale&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_end_unit&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;trim_distance_start&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;trim_distance_start_map_unit_scale&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;MM&quot; name=&quot;trim_distance_start_unit&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;tweak_dash_pattern_on_corners&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;0&quot; name=&quot;use_custom_dash&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot; name=&quot;width_map_unit_scale&quot;/&gt;&lt;/Option&gt;&lt;data_defined_properties&gt;&lt;Option type=&quot;Map&quot;&gt;&lt;Option type=&quot;QString&quot; value=&quot;&quot; name=&quot;name&quot;/&gt;&lt;Option name=&quot;properties&quot;/&gt;&lt;Option type=&quot;QString&quot; value=&quot;collection&quot; name=&quot;type&quot;/&gt;&lt;/Option&gt;&lt;/data_defined_properties&gt;&lt;/layer&gt;&lt;/symbol&gt;" name="lineSymbol"/>
          <Option type="double" value="0" name="minLength"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale"/>
          <Option type="QString" value="MM" name="minLengthUnit"/>
          <Option type="double" value="0" name="offsetFromAnchor"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromAnchorUnit"/>
          <Option type="double" value="0" name="offsetFromLabel"/>
          <Option type="QString" value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale"/>
          <Option type="QString" value="MM" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>"""

def _get_point_qml(color: str, shape: str = 'circle', size: float = 3.0, 
                   outline_color: str = 'black', outline_width: float = 0.4,
                   label_field: str = None, label_size: float = 10, buffer_size: float = 1.0) -> str:
    color_rgba = hex_to_rgba(color)
    outline_rgba = hex_to_rgba(outline_color)
    labeling = _get_labeling_xml(label_field, label_size, buffer_size)
    
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0-Prizren" styleCategories="AllStyleCategories" minScale="100000000" maxScale="0" hasScaleBasedVisibilityFlag="0" readOnly="0">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol type="marker" alpha="1" clip_to_extent="1" name="0" force_rhr="0" is_animated="0" frame_rate="10">
        <layer class="SimpleMarker" enabled="1" locked="0" pass="0" id="0">
          <Option type="Map">
            <Option type="QString" value="0" name="angle"/>
            <Option type="QString" value="square" name="cap_style"/>
            <Option type="QString" value="{color_rgba}" name="color"/>
            <Option type="QString" value="1" name="horizontal_anchor_point"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="{shape}" name="name"/>
            <Option type="QString" value="0,0" name="offset"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="{outline_rgba}" name="outline_color"/>
            <Option type="QString" value="solid" name="outline_style"/>
            <Option type="QString" value="{outline_width}" name="outline_width"/>
            <Option type="QString" value="MM" name="outline_width_unit"/>
            <Option type="QString" value="diameter" name="scale_method"/>
            <Option type="QString" value="{size}" name="size"/>
            <Option type="QString" value="MM" name="size_unit"/>
            <Option type="QString" value="1" name="vertical_anchor_point"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  {labeling}
</qgis>"""

def _get_line_qml(color: str, width: float = 0.66, style: str = 'solid',
                  label_field: str = None, label_size: float = 10, buffer_size: float = 1.0) -> str:
    color_rgba = hex_to_rgba(color)
    labeling = _get_labeling_xml(label_field, label_size, buffer_size)
    
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0-Prizren" styleCategories="AllStyleCategories" minScale="100000000" maxScale="0" hasScaleBasedVisibilityFlag="0" readOnly="0">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol type="line" alpha="1" clip_to_extent="1" name="0" force_rhr="0" is_animated="0" frame_rate="10">
        <layer class="SimpleLine" enabled="1" locked="0" pass="0" id="0">
          <Option type="Map">
            <Option type="QString" value="0" name="align_dash_pattern"/>
            <Option type="QString" value="square" name="capstyle"/>
            <Option type="QString" value="5;2" name="customdash"/>
            <Option type="QString" value="MM" name="customdash_unit"/>
            <Option type="QString" value="0" name="dash_pattern_offset"/>
            <Option type="QString" value="MM" name="dash_pattern_offset_unit"/>
            <Option type="QString" value="0" name="draw_inside_polygon"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="{color_rgba}" name="line_color"/>
            <Option type="QString" value="{style}" name="line_style"/>
            <Option type="QString" value="{width}" name="line_width"/>
            <Option type="QString" value="MM" name="line_width_unit"/>
            <Option type="QString" value="0" name="offset"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="0" name="ring_filter"/>
            <Option type="QString" value="0" name="trim_distance_end"/>
            <Option type="QString" value="MM" name="trim_distance_end_unit"/>
            <Option type="QString" value="0" name="trim_distance_start"/>
            <Option type="QString" value="MM" name="trim_distance_start_unit"/>
            <Option type="QString" value="0" name="tweak_dash_pattern_on_corners"/>
            <Option type="QString" value="0" name="use_custom_dash"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="width_map_unit_scale"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  {labeling}
</qgis>"""

def _get_polygon_qml(color: str, outline_color: str = 'black', 
                     outline_width: float = 0.26, opacity: float = 1.0,
                     fill_style: str = 'solid',
                     label_field: str = None, label_size: float = 10, buffer_size: float = 1.0) -> str:
    color_rgba = hex_to_rgba(color, opacity)
    outline_rgba = hex_to_rgba(outline_color)
    if fill_style == 'no': fill_style = 'no'
    labeling = _get_labeling_xml(label_field, label_size, buffer_size)
    
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0-Prizren" styleCategories="AllStyleCategories" minScale="100000000" maxScale="0" hasScaleBasedVisibilityFlag="0" readOnly="0">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol type="fill" alpha="1" clip_to_extent="1" name="0" force_rhr="0" is_animated="0" frame_rate="10">
        <layer class="SimpleFill" enabled="1" locked="0" pass="0" id="0">
          <Option type="Map">
            <Option type="QString" value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale"/>
            <Option type="QString" value="{color_rgba}" name="color"/>
            <Option type="QString" value="bevel" name="joinstyle"/>
            <Option type="QString" value="0,0" name="offset"/>
            <Option type="QString" value="3x:0,0,0,0,0,0" name="offset_map_unit_scale"/>
            <Option type="QString" value="MM" name="offset_unit"/>
            <Option type="QString" value="{outline_rgba}" name="outline_color"/>
            <Option type="QString" value="solid" name="outline_style"/>
            <Option type="QString" value="{outline_width}" name="outline_width"/>
            <Option type="QString" value="MM" name="outline_width_unit"/>
            <Option type="QString" value="{fill_style}" name="style"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  {labeling}
</qgis>"""

def generate_qml_point(output_path: str, color: str, shape: str = 'circle', size: float = 3.0, outline_color: str = 'black',
                       label_field: str = None, label_size: float = 10, buffer_size: float = 1.0) -> bool:
    try:
        xml = _get_point_qml(color, shape, size, outline_color, outline_width=0.4, label_field=label_field, label_size=label_size, buffer_size=buffer_size)
        with open(output_path, 'w', encoding='utf-8') as f: f.write(xml)
        return True
    except Exception as e:
        logger.error(f"Gen QML Point Error: {e}")
        return False

def generate_qml_line(output_path: str, color: str, width: float = 0.66,
                      label_field: str = None, label_size: float = 10, buffer_size: float = 1.0) -> bool:
    try:
        xml = _get_line_qml(color, width, label_field=label_field, label_size=label_size, buffer_size=buffer_size)
        with open(output_path, 'w', encoding='utf-8') as f: f.write(xml)
        return True
    except Exception as e:
        logger.error(f"Gen QML Line Error: {e}")
        return False

def generate_qml_polygon(output_path: str, color: str, outline_color: str = 'black', 
                         outline_width: float = 0.26, opacity: float = 1.0, fill_style='solid',
                         label_field: str = None, label_size: float = 10, buffer_size: float = 1.0) -> bool:
    try:
        xml = _get_polygon_qml(color, outline_color, outline_width, opacity, fill_style, 
                               label_field=label_field, label_size=label_size, buffer_size=buffer_size)
        with open(output_path, 'w', encoding='utf-8') as f: f.write(xml)
        return True
    except Exception as e:
        logger.error(f"Gen QML Polygon Error: {e}")
        return False

