<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" labelsEnabled="0" simplifyAlgorithm="0" simplifyMaxScale="1" readOnly="0" maxScale="0" minScale="1e+08" simplifyDrawingHints="1" simplifyDrawingTol="1" version="3.4.5-Madeira" simplifyLocal="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" type="RuleRenderer" symbollevels="0" enableorderby="0">
    <rules key="{a91f1344-fc60-4b87-8637-ce265fab9cf3}">
      <rule filter="&quot;LakeId&quot; IS NULL AND &quot;Subbasin&quot; > 0" symbol="0" key="{67c77a71-e0ec-49d0-9684-1f64c24f9b13}"/>
      <rule filter="&quot;LakeId&quot; IS NOT NULL" symbol="1" label="lake" key="{cf51ac01-3597-4219-975d-809b6090c781}"/>
      <rule filter=" &quot;LakeId&quot;  IS NULL AND  &quot;Subbasin&quot;  IS NULL" symbol="2" key="{182d8450-1473-4c6b-9b8d-4df53d770572}"/>
    </rules>
    <symbols>
      <symbol force_rhr="0" type="fill" name="0" clip_to_extent="1" alpha="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="109,248,204,0"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="no"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" type="fill" name="1" clip_to_extent="1" alpha="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="27,252,255,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol force_rhr="0" type="fill" name="2" clip_to_extent="1" alpha="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="145,82,45,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="no"/>
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
  <labeling type="simple">
    <settings>
      <text-style fontUnderline="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontStrikeout="0" fieldName="CASE WHEN &quot;Subbasin&quot; = 0 OR &quot;LakeId&quot; THEN '' ELSE &quot;Subbasin&quot; END" blendMode="0" useSubstitutions="0" textColor="0,0,0,255" fontSizeUnit="Point" isExpression="1" fontItalic="0" fontSize="8.25" previewBkgrdColor="#ffffff" fontFamily="MS Shell Dlg 2" fontWeight="50" fontWordSpacing="0" textOpacity="1" namedStyle="Regular" fontLetterSpacing="0" fontCapitals="0" multilineHeight="1">
        <text-buffer bufferDraw="0" bufferSizeUnits="MM" bufferJoinStyle="128" bufferBlendMode="0" bufferNoFill="0" bufferColor="255,255,255,255" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSize="1" bufferOpacity="1"/>
        <background shapeBorderWidthUnit="MM" shapeRotationType="0" shapeOffsetX="0" shapeSizeUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeType="0" shapeSizeType="0" shapeOffsetY="0" shapeSizeY="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeRadiiX="0" shapeBorderWidth="0" shapeJoinStyle="64" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeBorderColor="128,128,128,255" shapeSVGFile="" shapeRadiiUnit="MM" shapeDraw="0" shapeFillColor="255,255,255,255" shapeBlendMode="0" shapeOffsetUnit="MM" shapeSizeX="0"/>
        <shadow shadowOffsetDist="1" shadowColor="0,0,0,255" shadowDraw="0" shadowOpacity="0.7" shadowUnder="0" shadowOffsetGlobal="1" shadowRadius="1.5" shadowRadiusAlphaOnly="0" shadowOffsetUnit="MM" shadowRadiusUnit="MM" shadowOffsetAngle="135" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowBlendMode="6" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0"/>
        <substitutions/>
      </text-style>
      <text-format autoWrapLength="0" multilineAlign="4294967295" reverseDirectionSymbol="0" wrapChar="" addDirectionSymbol="0" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" formatNumbers="0" decimals="3" plussign="0" placeDirectionSymbol="0"/>
      <placement labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetType="0" offsetUnits="MapUnit" distUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" preserveRotation="1" fitInPolygonOnly="1" maxCurvedCharAngleIn="25" rotationAngle="0" distMapUnitScale="3x:0,0,0,0,0,0" priority="5" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" centroidInside="0" quadOffset="4" centroidWhole="0" placement="1" xOffset="0" yOffset="0" dist="0" repeatDistance="0" repeatDistanceUnits="MM" maxCurvedCharAngleOut="-25" placementFlags="10"/>
      <rendering scaleMin="1" obstacleFactor="1" obstacle="1" fontMinPixelSize="3" obstacleType="0" scaleMax="10000000" mergeLines="0" upsidedownLabels="0" labelPerPart="0" fontMaxPixelSize="10000" drawLabels="1" limitNumLabels="0" displayAll="0" maxNumLabels="2000" zIndex="0" scaleVisibility="0" minFeatureSize="0" fontLimitPixelSize="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option name="properties"/>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <customproperties>
    <property key="dualview/previewExpressions">
      <value>PolygonId</value>
      <value>"PolygonId"</value>
    </property>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="true" key="labeling/enabled"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory maxScaleDenominator="1e+08" diagramOrientation="Up" minScaleDenominator="0" minimumSize="0" lineSizeType="MM" opacity="1" scaleBasedVisibility="0" sizeType="MM" enabled="0" penAlpha="255" height="15" barWidth="5" labelPlacementMethod="XHeight" scaleDependency="Area" lineSizeScale="3x:0,0,0,0,0,0" rotationOffset="270" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" width="15" penColor="#000000" penWidth="0">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute color="#000000" label="" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings showAll="1" placement="0" dist="0" linePlacementFlags="2" obstacle="0" priority="0" zIndex="0">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="PolygonId">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="DownId">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Area">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Subbasin">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LakeId">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="PolygonId"/>
    <alias index="1" name="" field="DownId"/>
    <alias index="2" name="" field="Area"/>
    <alias index="3" name="" field="Subbasin"/>
    <alias index="4" name="" field="LakeId"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" expression="" field="PolygonId"/>
    <default applyOnUpdate="0" expression="" field="DownId"/>
    <default applyOnUpdate="0" expression="" field="Area"/>
    <default applyOnUpdate="0" expression="" field="Subbasin"/>
    <default applyOnUpdate="0" expression="" field="LakeId"/>
  </defaults>
  <constraints>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" field="PolygonId" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" field="DownId" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" field="Area" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" field="Subbasin" exp_strength="0"/>
    <constraint constraints="0" notnull_strength="0" unique_strength="0" field="LakeId" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="PolygonId" exp=""/>
    <constraint desc="" field="DownId" exp=""/>
    <constraint desc="" field="Area" exp=""/>
    <constraint desc="" field="Subbasin" exp=""/>
    <constraint desc="" field="LakeId" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="&quot;PolygonId&quot;" sortOrder="0">
    <columns>
      <column width="-1" type="field" name="PolygonId" hidden="0"/>
      <column width="-1" type="field" name="DownId" hidden="0"/>
      <column width="-1" type="field" name="Area" hidden="0"/>
      <column width="-1" type="field" name="Subbasin" hidden="0"/>
      <column width="-1" type="actions" hidden="1"/>
      <column width="-1" type="field" name="LakeId" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1">C:/PROGRA~1/QGIS3~1.4/bin</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>C:/PROGRA~1/QGIS3~1.4/bin</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="Area"/>
    <field editable="1" name="DownId"/>
    <field editable="1" name="LakeId"/>
    <field editable="1" name="PolygonId"/>
    <field editable="1" name="Subbasin"/>
  </editable>
  <labelOnTop>
    <field name="Area" labelOnTop="0"/>
    <field name="DownId" labelOnTop="0"/>
    <field name="LakeId" labelOnTop="0"/>
    <field name="PolygonId" labelOnTop="0"/>
    <field name="Subbasin" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>PolygonId</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
