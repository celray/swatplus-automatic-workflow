<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" minScale="1e+08" labelsEnabled="1" styleCategories="AllStyleCategories" simplifyAlgorithm="0" simplifyMaxScale="1" readOnly="0" maxScale="0" version="3.4.11-Madeira" simplifyDrawingHints="1" simplifyDrawingTol="1" simplifyLocal="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" forceraster="0" type="RuleRenderer" enableorderby="0">
    <rules key="{a91f1344-fc60-4b87-8637-ce265fab9cf3}">
      <rule filter="&quot;LakeId&quot; IS NULL" symbol="0" key="{67c77a71-e0ec-49d0-9684-1f64c24f9b13}"/>
      <rule filter="&quot;LakeId&quot; IS NOT NULL" label="lake" symbol="1" key="{cf51ac01-3597-4219-975d-809b6090c781}"/>
    </rules>
    <symbols>
      <symbol name="0" clip_to_extent="1" force_rhr="0" alpha="1" type="fill">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="109,248,204,0" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0,0,0,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="no" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" clip_to_extent="1" force_rhr="0" alpha="1" type="fill">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="27,252,255,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style blendMode="0" namedStyle="Regular" fontSizeUnit="Point" fontCapitals="0" textColor="0,0,0,255" fontLetterSpacing="0" textOpacity="1" fontWordSpacing="0" useSubstitutions="0" fontItalic="0" fontFamily="MS Shell Dlg 2" fontStrikeout="0" multilineHeight="1" fontSize="8.25" fontUnderline="0" fieldName="CASE WHEN &quot;Subbasin&quot; = 0 OR &quot;LakeId&quot; THEN '' ELSE &quot;Subbasin&quot; END" previewBkgrdColor="#ffffff" fontWeight="50" fontSizeMapUnitScale="3x:0,0,0,0,0,0" isExpression="1">
        <text-buffer bufferSizeUnits="MM" bufferJoinStyle="128" bufferDraw="0" bufferColor="255,255,255,255" bufferOpacity="1" bufferNoFill="0" bufferBlendMode="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSize="1"/>
        <background shapeBlendMode="0" shapeRotationType="0" shapeRadiiY="0" shapeBorderColor="128,128,128,255" shapeSVGFile="" shapeFillColor="255,255,255,255" shapeBorderWidthUnit="MM" shapeSizeUnit="MM" shapeOffsetX="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetUnit="MM" shapeSizeType="0" shapeRadiiX="0" shapeBorderWidth="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeDraw="0" shapeSizeX="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeY="0" shapeType="0" shapeRadiiUnit="MM" shapeOffsetY="0" shapeRotation="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64"/>
        <shadow shadowUnder="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusAlphaOnly="0" shadowOffsetGlobal="1" shadowOpacity="0.7" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowOffsetAngle="135" shadowRadius="1.5" shadowBlendMode="6" shadowRadiusUnit="MM" shadowOffsetUnit="MM" shadowDraw="0" shadowOffsetDist="1" shadowColor="0,0,0,255"/>
        <substitutions/>
      </text-style>
      <text-format plussign="0" wrapChar="" formatNumbers="0" autoWrapLength="0" placeDirectionSymbol="0" useMaxLineLengthForAutoWrap="1" leftDirectionSymbol="&lt;" reverseDirectionSymbol="0" multilineAlign="4294967295" rightDirectionSymbol=">" addDirectionSymbol="0" decimals="3"/>
      <placement distUnits="MM" placementFlags="10" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleOut="-25" priority="5" yOffset="0" repeatDistance="0" distMapUnitScale="3x:0,0,0,0,0,0" preserveRotation="1" offsetUnits="MapUnit" quadOffset="4" repeatDistanceUnits="MM" dist="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" fitInPolygonOnly="1" centroidWhole="0" rotationAngle="0" centroidInside="0" xOffset="0" offsetType="0" placement="1" maxCurvedCharAngleIn="25"/>
      <rendering fontMaxPixelSize="10000" scaleVisibility="0" zIndex="0" scaleMax="10000000" limitNumLabels="0" obstacleType="0" fontMinPixelSize="3" displayAll="0" maxNumLabels="2000" obstacleFactor="1" scaleMin="1" upsidedownLabels="0" obstacle="1" fontLimitPixelSize="0" labelPerPart="0" mergeLines="0" minFeatureSize="0" drawLabels="1"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties"/>
          <Option name="type" type="QString" value="collection"/>
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
    <DiagramCategory sizeScale="3x:0,0,0,0,0,0" penAlpha="255" width="15" scaleDependency="Area" minScaleDenominator="0" lineSizeType="MM" scaleBasedVisibility="0" diagramOrientation="Up" labelPlacementMethod="XHeight" minimumSize="0" height="15" barWidth="5" opacity="1" rotationOffset="270" lineSizeScale="3x:0,0,0,0,0,0" maxScaleDenominator="1e+08" backgroundAlpha="255" backgroundColor="#ffffff" penWidth="0" sizeType="MM" enabled="0" penColor="#000000">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute color="#000000" field="" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="0" zIndex="0" dist="0" priority="0" showAll="1" linePlacementFlags="2" obstacle="0">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
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
    <field name="RES">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="PolygonId" index="0"/>
    <alias name="" field="DownId" index="1"/>
    <alias name="" field="Area" index="2"/>
    <alias name="" field="Subbasin" index="3"/>
    <alias name="" field="LakeId" index="4"/>
    <alias name="" field="RES" index="5"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="PolygonId" expression="" applyOnUpdate="0"/>
    <default field="DownId" expression="" applyOnUpdate="0"/>
    <default field="Area" expression="" applyOnUpdate="0"/>
    <default field="Subbasin" expression="" applyOnUpdate="0"/>
    <default field="LakeId" expression="" applyOnUpdate="0"/>
    <default field="RES" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="PolygonId" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="DownId" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="Area" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="Subbasin" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="LakeId" exp_strength="0"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" field="RES" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="PolygonId" desc=""/>
    <constraint exp="" field="DownId" desc=""/>
    <constraint exp="" field="Area" desc=""/>
    <constraint exp="" field="Subbasin" desc=""/>
    <constraint exp="" field="LakeId" desc=""/>
    <constraint exp="" field="RES" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="&quot;PolygonId&quot;" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" width="-1" name="PolygonId" type="field"/>
      <column hidden="0" width="-1" name="DownId" type="field"/>
      <column hidden="0" width="-1" name="Area" type="field"/>
      <column hidden="0" width="-1" name="Subbasin" type="field"/>
      <column hidden="1" width="-1" type="actions"/>
      <column hidden="0" width="-1" name="LakeId" type="field"/>
      <column hidden="0" width="-1" name="RES" type="field"/>
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
    <field name="Area" editable="1"/>
    <field name="DownId" editable="1"/>
    <field name="LakeId" editable="1"/>
    <field name="PolygonId" editable="1"/>
    <field name="RES" editable="1"/>
    <field name="Subbasin" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="Area"/>
    <field labelOnTop="0" name="DownId"/>
    <field labelOnTop="0" name="LakeId"/>
    <field labelOnTop="0" name="PolygonId"/>
    <field labelOnTop="0" name="RES"/>
    <field labelOnTop="0" name="Subbasin"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>PolygonId</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
