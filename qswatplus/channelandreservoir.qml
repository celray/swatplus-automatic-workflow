<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="1e+08" simplifyDrawingTol="1" readOnly="0" styleCategories="AllStyleCategories" simplifyDrawingHints="0" labelsEnabled="0" maxScale="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" version="3.4.7-Madeira" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" type="RuleRenderer" enableorderby="0" symbollevels="0">
    <rules key="{50ab9495-26fd-4273-9c00-a04b2e8a8b6c}">
      <rule label="Channel" key="{d08297ae-7ac2-40dd-b266-b666c1d99d5c}" filter=" &quot;Reservoir&quot; = 0 AND  &quot;Pond&quot;  = 0" symbol="0"/>
      <rule label="Reservoir" key="{49129db6-8dbb-4e40-ad9d-1d806820c5f4}" filter=" &quot;Reservoir&quot; > 0 AND  &quot;Pond&quot; = 0" symbol="1"/>
      <rule label="Pond" key="{9ea290bc-2764-4fbe-bbdc-0d991d819325}" description="Pond" filter=" &quot;Reservoir&quot; = 0 AND  &quot;Pond&quot; > 0" symbol="2"/>
    </rules>
    <symbols>
      <symbol name="0" clip_to_extent="1" force_rhr="0" alpha="1" type="line">
        <layer class="SimpleLine" enabled="1" pass="0" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="5;2"/>
          <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="MM"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="27,179,255,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="0.26"/>
          <prop k="line_width_unit" v="MM"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="ring_filter" v="0"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="1" clip_to_extent="1" force_rhr="0" alpha="1" type="line">
        <layer class="SimpleLine" enabled="1" pass="0" locked="0">
          <prop k="capstyle" v="square"/>
          <prop k="customdash" v="5;2"/>
          <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="MM"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="line_color" v="0,85,255,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="2"/>
          <prop k="line_width_unit" v="MM"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="ring_filter" v="0"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol name="2" clip_to_extent="1" force_rhr="0" alpha="1" type="line">
        <layer class="SimpleLine" enabled="1" pass="0" locked="0">
          <prop k="capstyle" v="square"/>
          <prop k="customdash" v="5;2"/>
          <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="MM"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="line_color" v="21,217,234,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="MM"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="ring_filter" v="0"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
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
  <customproperties>
    <property key="dualview/previewExpressions" value="COALESCE(&quot;ID&quot;, '&lt;NULL>')"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory enabled="0" maxScaleDenominator="1e+08" barWidth="5" sizeScale="3x:0,0,0,0,0,0" minScaleDenominator="0" diagramOrientation="Up" sizeType="MM" lineSizeType="MM" opacity="1" width="15" scaleBasedVisibility="0" rotationOffset="270" height="15" penColor="#000000" scaleDependency="Area" minimumSize="0" lineSizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" labelPlacementMethod="XHeight" penWidth="0" backgroundColor="#ffffff" penAlpha="255">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="2" zIndex="0" linePlacementFlags="2" priority="0" dist="0" obstacle="0" showAll="1">
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
    <field name="LINKNO">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Channel">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="ChannelR">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Subbasin">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="AreaC">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Len2">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Slo2">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Wid2">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Dep2">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="MinEl">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="MaxEl">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Reservoir">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Pond">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LakeIn">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="LakeOut">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" index="0" field="LINKNO"/>
    <alias name="" index="1" field="Channel"/>
    <alias name="" index="2" field="ChannelR"/>
    <alias name="" index="3" field="Subbasin"/>
    <alias name="" index="4" field="AreaC"/>
    <alias name="" index="5" field="Len2"/>
    <alias name="" index="6" field="Slo2"/>
    <alias name="" index="7" field="Wid2"/>
    <alias name="" index="8" field="Dep2"/>
    <alias name="" index="9" field="MinEl"/>
    <alias name="" index="10" field="MaxEl"/>
    <alias name="" index="11" field="Reservoir"/>
    <alias name="" index="12" field="Pond"/>
    <alias name="" index="13" field="LakeIn"/>
    <alias name="" index="14" field="LakeOut"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="LINKNO" expression="" applyOnUpdate="0"/>
    <default field="Channel" expression="" applyOnUpdate="0"/>
    <default field="ChannelR" expression="" applyOnUpdate="0"/>
    <default field="Subbasin" expression="" applyOnUpdate="0"/>
    <default field="AreaC" expression="" applyOnUpdate="0"/>
    <default field="Len2" expression="" applyOnUpdate="0"/>
    <default field="Slo2" expression="" applyOnUpdate="0"/>
    <default field="Wid2" expression="" applyOnUpdate="0"/>
    <default field="Dep2" expression="" applyOnUpdate="0"/>
    <default field="MinEl" expression="" applyOnUpdate="0"/>
    <default field="MaxEl" expression="" applyOnUpdate="0"/>
    <default field="Reservoir" expression="" applyOnUpdate="0"/>
    <default field="Pond" expression="" applyOnUpdate="0"/>
    <default field="LakeIn" expression="" applyOnUpdate="0"/>
    <default field="LakeOut" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="LINKNO"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Channel"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="ChannelR"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Subbasin"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="AreaC"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Len2"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Slo2"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Wid2"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Dep2"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="MinEl"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="MaxEl"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Reservoir"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="Pond"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="LakeIn"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" notnull_strength="0" field="LakeOut"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="LINKNO" desc=""/>
    <constraint exp="" field="Channel" desc=""/>
    <constraint exp="" field="ChannelR" desc=""/>
    <constraint exp="" field="Subbasin" desc=""/>
    <constraint exp="" field="AreaC" desc=""/>
    <constraint exp="" field="Len2" desc=""/>
    <constraint exp="" field="Slo2" desc=""/>
    <constraint exp="" field="Wid2" desc=""/>
    <constraint exp="" field="Dep2" desc=""/>
    <constraint exp="" field="MinEl" desc=""/>
    <constraint exp="" field="MaxEl" desc=""/>
    <constraint exp="" field="Reservoir" desc=""/>
    <constraint exp="" field="Pond" desc=""/>
    <constraint exp="" field="LakeIn" desc=""/>
    <constraint exp="" field="LakeOut" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="1" sortExpression="&quot;Pond&quot;" actionWidgetStyle="dropDown">
    <columns>
      <column name="Channel" hidden="0" type="field" width="-1"/>
      <column name="ChannelR" hidden="0" type="field" width="-1"/>
      <column name="Subbasin" hidden="0" type="field" width="-1"/>
      <column name="AreaC" hidden="0" type="field" width="-1"/>
      <column name="Len2" hidden="0" type="field" width="-1"/>
      <column name="Slo2" hidden="0" type="field" width="-1"/>
      <column name="Wid2" hidden="0" type="field" width="-1"/>
      <column name="Dep2" hidden="0" type="field" width="-1"/>
      <column name="MinEl" hidden="0" type="field" width="-1"/>
      <column name="MaxEl" hidden="0" type="field" width="-1"/>
      <column name="Reservoir" hidden="0" type="field" width="-1"/>
      <column hidden="1" type="actions" width="-1"/>
      <column name="LINKNO" hidden="0" type="field" width="-1"/>
      <column name="Pond" hidden="0" type="field" width="-1"/>
      <column name="LakeIn" hidden="0" type="field" width="-1"/>
      <column name="LakeOut" hidden="0" type="field" width="-1"/>
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
    <field name="AreaC" editable="1"/>
    <field name="Channel" editable="1"/>
    <field name="ChannelR" editable="1"/>
    <field name="Dep2" editable="1"/>
    <field name="LINKNO" editable="1"/>
    <field name="LakeIn" editable="1"/>
    <field name="LakeOut" editable="1"/>
    <field name="Len2" editable="1"/>
    <field name="MaxEl" editable="1"/>
    <field name="MinEl" editable="1"/>
    <field name="Pond" editable="1"/>
    <field name="Reservoir" editable="1"/>
    <field name="Slo2" editable="1"/>
    <field name="Subbasin" editable="1"/>
    <field name="Wid2" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="AreaC" labelOnTop="0"/>
    <field name="Channel" labelOnTop="0"/>
    <field name="ChannelR" labelOnTop="0"/>
    <field name="Dep2" labelOnTop="0"/>
    <field name="LINKNO" labelOnTop="0"/>
    <field name="LakeIn" labelOnTop="0"/>
    <field name="LakeOut" labelOnTop="0"/>
    <field name="Len2" labelOnTop="0"/>
    <field name="MaxEl" labelOnTop="0"/>
    <field name="MinEl" labelOnTop="0"/>
    <field name="Pond" labelOnTop="0"/>
    <field name="Reservoir" labelOnTop="0"/>
    <field name="Slo2" labelOnTop="0"/>
    <field name="Subbasin" labelOnTop="0"/>
    <field name="Wid2" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>COALESCE("ID", '&lt;NULL>')</previewExpression>
  <mapTip>ID</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
