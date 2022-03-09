<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyDrawingTol="1" simplifyLocal="1" version="3.4.11-Madeira" labelsEnabled="0" readOnly="0" maxScale="0" hasScaleBasedVisibilityFlag="0" minScale="1e+08" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol type="line" alpha="1" name="0" force_rhr="0" clip_to_extent="1">
        <layer locked="0" enabled="1" class="ArrowLine" pass="0">
          <prop k="arrow_start_width" v="1"/>
          <prop k="arrow_start_width_unit" v="MM"/>
          <prop k="arrow_start_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="arrow_type" v="0"/>
          <prop k="arrow_width" v="1"/>
          <prop k="arrow_width_unit" v="MM"/>
          <prop k="arrow_width_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_length" v="3.9"/>
          <prop k="head_length_unit" v="MM"/>
          <prop k="head_length_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_thickness" v="2.9"/>
          <prop k="head_thickness_unit" v="MM"/>
          <prop k="head_thickness_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="head_type" v="0"/>
          <prop k="is_curved" v="0"/>
          <prop k="is_repeated" v="0"/>
          <prop k="offset" v="0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="ring_filter" v="0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol type="fill" alpha="1" name="@0@0" force_rhr="0" clip_to_extent="1">
            <layer locked="0" enabled="1" class="SimpleFill" pass="0">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="31,120,180,255"/>
              <prop k="joinstyle" v="round"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="no"/>
              <prop k="outline_width" v="0.46"/>
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
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory labelPlacementMethod="XHeight" diagramOrientation="Up" minimumSize="0" penAlpha="255" height="15" minScaleDenominator="0" backgroundColor="#ffffff" width="15" scaleDependency="Area" rotationOffset="270" enabled="0" backgroundAlpha="255" opacity="1" sizeScale="3x:0,0,0,0,0,0" lineSizeType="MM" penColor="#000000" lineSizeScale="3x:0,0,0,0,0,0" sizeType="MM" barWidth="5" scaleBasedVisibility="0" maxScaleDenominator="1e+08" penWidth="0">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute color="#000000" label="" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" showAll="1" zIndex="0" dist="0" priority="0" placement="2" linePlacementFlags="2">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="LINKNO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="DSLINKNO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="DSNODEID">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="WSNO">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" field="LINKNO" name=""/>
    <alias index="1" field="DSLINKNO" name=""/>
    <alias index="2" field="DSNODEID" name=""/>
    <alias index="3" field="WSNO" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="LINKNO" expression=""/>
    <default applyOnUpdate="0" field="DSLINKNO" expression=""/>
    <default applyOnUpdate="0" field="DSNODEID" expression=""/>
    <default applyOnUpdate="0" field="WSNO" expression=""/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" notnull_strength="0" field="LINKNO" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="DSLINKNO" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="DSNODEID" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="WSNO" constraints="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="LINKNO"/>
    <constraint exp="" desc="" field="DSLINKNO"/>
    <constraint exp="" desc="" field="DSNODEID"/>
    <constraint exp="" desc="" field="WSNO"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column type="field" width="-1" name="LINKNO" hidden="0"/>
      <column type="field" width="-1" name="DSLINKNO" hidden="0"/>
      <column type="field" width="-1" name="WSNO" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
      <column type="field" width="-1" name="DSNODEID" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1">.</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>.</editforminitfilepath>
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
    <field name="DSLINKNO" editable="1"/>
    <field name="DSNODEID" editable="1"/>
    <field name="LINKNO" editable="1"/>
    <field name="WSNO" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="DSLINKNO"/>
    <field labelOnTop="0" name="DSNODEID"/>
    <field labelOnTop="0" name="LINKNO"/>
    <field labelOnTop="0" name="WSNO"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>DSNODEID</previewExpression>
  <mapTip>ID</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
