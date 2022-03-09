
'''
date        : 31/03/2020
description : this is a template for qgs file

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

template = '''<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="{project_name}" version="3.24.10">
  <homePath path=""/>
  <title>{project_name}</title>
  <autotransaction active="0"/>
  <evaluateDefaultValues active="0"/>
  <trust active="0"/>
  <projectCrs>
    <spatialrefsys>
      <wkt>{prjcrs}</wkt>
      <proj4>{proj4}</proj4>
      <srsid>{srsid}</srsid>
      <srid>{srid}</srid>
      <authid>EPSG:{srid}</authid>
      <description>{srs_description}</description>
      <projectionacronym>{projectionacronym}</projectionacronym>
      <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
      <geographicflag>{geographicflag}</geographicflag>
    </spatialrefsys>
  </projectCrs>
  <layer-tree-group>
    <customproperties/>
    <layer-tree-group checked="Qt::Checked" expanded="1" name="Animations">
      <customproperties/>
    </layer-tree-group>
    <layer-tree-group checked="Qt::Checked" expanded="1" name="Results">
      <customproperties/>
    </layer-tree-group>
    <layer-tree-group checked="Qt::Checked" expanded="1" name="Watershed">
      <customproperties/>
      <layer-tree-layer id="Subbasins__subs1__3017a81e_0174_439c_b815_cf54de0e0667" source="./Watershed/Shapes/subs1.shp" checked="Qt::Checked" expanded="0" providerKey="ogr" name="Subbasins (subs1)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Pt_sources_and_reservoirs__reservoirs2__ada5d781_850f_43ac_825b_b807e28299e4" source="./Watershed/Shapes/reservoirs1.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Pt sources and reservoirs (reservoirs2)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Snapped_inlets_outlets__{outlet_name}_snap__2a54eb19_3da0_420d_b964_e4cd8efd371f" source="./Watershed/Shapes/{outlet_name}_snap.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Snapped inlets/outlets ({outlet_name}_snap)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Drawn_inlets_outlets__{outlet_name}__c41cb90c_f1d6_4ffe_8a64_99bcb575d961" source="./Watershed/Shapes/{outlet_name}.shp" checked="Qt::Unchecked" expanded="1" providerKey="ogr" name="Drawn inlets/outlets ({outlet_name})">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Inlets_outlets__{outlet_name}__0c49465a_2a2b_4ecb_ae4f_fbb60c4c1bcb" source="./Watershed/Shapes/{outlet_name}.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Inlets/outlets ({outlet_name})">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Streams__{dem_name}stream__6a837462_9d7d_48f0_a6c1_1710f553d03b" source="./Watershed/Shapes/{dem_name}stream.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Streams ({dem_name}stream)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Channel_reaches__rivs1__514d2d76_3dcd_4834_8bd4_42392284ab2f" source="./Watershed/Shapes/rivs1.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Channel reaches (rivs1)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Channels__{dem_name}channel__a7e3608c_b71d_44f6_8194_67e56bb7c543" source="./Watershed/Shapes/{dem_name}channel.shp" checked="Qt::Unchecked" expanded="1" providerKey="ogr" name="Channels ({dem_name}channel)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Full_LSUs__lsus1__8f4e9cfb_3ca6_4a70_83b9_fe977379bcf4" source="./Watershed/Shapes/lsus1.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Full LSUs (lsus1)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Actual_HRUs__hrus2__7adc36e1_3c7f_40db_8b2c_bb4f79fa3338" source="./Watershed/Shapes/hrus2.shp" checked="Qt::Checked" expanded="1" providerKey="ogr" name="Actual HRUs (hrus2)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Full_HRUs__hrus1__4e2ba365_e7bd_4f8e_9d6c_79056945afb5" source="./Watershed/Shapes/hrus1.shp" checked="Qt::Unchecked" expanded="1" providerKey="ogr" name="Full HRUs (hrus1)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="Hillshade__{dem_name}hillshade__a6f33483_65e8_4cde_a966_948ff13f0c2a" source="./Watershed/Rasters/DEM/{dem_name}hillshade.tif" checked="Qt::Checked" expanded="0" providerKey="gdal" name="Hillshade ({dem_name}hillshade)">
        <customproperties/>
      </layer-tree-layer>
      <layer-tree-layer id="DEM__{dem_name}__f751ab49_fdac_4766_be7f_300fbfe6adf2" source="./Watershed/Rasters/DEM/{dem_file_name}" checked="Qt::Checked" expanded="1" providerKey="gdal" name="DEM ({dem_name})">
        <customproperties/>
      </layer-tree-layer>
    </layer-tree-group>
    <layer-tree-group checked="Qt::Checked" expanded="1" name="Landuse">
      <customproperties/>
      <layer-tree-layer id="Landuses__{landuse_name}__f7ec5ca9_3dce_4d3e_8def_9e31ecc6c163" source="./Watershed/Rasters/Landuse/{landuse_file_name}" checked="Qt::Checked" expanded="1" providerKey="gdal" name="Landuses ({landuse_name})">
        <customproperties/>
      </layer-tree-layer>
    </layer-tree-group>
    <layer-tree-group checked="Qt::Checked" expanded="1" name="Soil">
      <customproperties/>
      <layer-tree-layer id="Soils__{soil_name}_tif__2cd25288_d1b5_4e76_83af_39034c9f7ffd" source="./Watershed/Rasters/Soil/{soil_file_name}" checked="Qt::Checked" expanded="1" providerKey="gdal" name="Soils ({soil_name})">
        <customproperties/>
      </layer-tree-layer>
    </layer-tree-group>
    <layer-tree-group checked="Qt::Checked" expanded="1" name="Slope">
      <customproperties/>
      <layer-tree-layer id="Slope_bands__{dem_name}slp_bands__daa1ee9a_d352_4de4_a12e_21aa0143f677" source="./Watershed/Rasters/DEM/{dem_name}slp_bands.tif" checked="Qt::Checked" expanded="1" providerKey="gdal" name="Slope bands ({dem_name}slp_bands)">
        <customproperties/>
      </layer-tree-layer>
    </layer-tree-group>
    <custom-order enabled="0">
      <item>DEM__{dem_name}__f751ab49_fdac_4766_be7f_300fbfe6adf2</item>
      <item>Hillshade__{dem_name}hillshade__a6f33483_65e8_4cde_a966_948ff13f0c2a</item>
      <item>Inlets_outlets__{outlet_name}__0c49465a_2a2b_4ecb_ae4f_fbb60c4c1bcb</item>
      <item>Drawn_inlets_outlets__{outlet_name}__c41cb90c_f1d6_4ffe_8a64_99bcb575d961</item>
      <item>Landuses__{landuse_name}__f7ec5ca9_3dce_4d3e_8def_9e31ecc6c163</item>
      <item>Soils__{soil_name}_tif__2cd25288_d1b5_4e76_83af_39034c9f7ffd</item>
      <item>Snapped_inlets_outlets__{outlet_name}_snap__2a54eb19_3da0_420d_b964_e4cd8efd371f</item>
      <item>Streams__{dem_name}stream__6a837462_9d7d_48f0_a6c1_1710f553d03b</item>
      <item>Channels__{dem_name}channel__a7e3608c_b71d_44f6_8194_67e56bb7c543</item>
      <item>Full_LSUs__lsus1__8f4e9cfb_3ca6_4a70_83b9_fe977379bcf4</item>
      <item>Full_HRUs__hrus1__4e2ba365_e7bd_4f8e_9d6c_79056945afb5</item>
      <item>Slope_bands__{dem_name}slp_bands__daa1ee9a_d352_4de4_a12e_21aa0143f677</item>
      <item>Pt_sources_and_reservoirs__reservoirs2__ada5d781_850f_43ac_825b_b807e28299e4</item>
      <item>Channel_reaches__rivs1__514d2d76_3dcd_4834_8bd4_42392284ab2f</item>
      <item>Actual_HRUs__hrus2__7adc36e1_3c7f_40db_8b2c_bb4f79fa3338</item>
      <item>Subbasins__subs1__3017a81e_0174_439c_b815_cf54de0e0667</item>
    </custom-order>
  </layer-tree-group>
  <snapping-settings enabled="0" intersection-snapping="0" unit="1" mode="2" tolerance="12" type="1">
    <individual-layer-settings>
      <layer-setting id="Snapped_inlets_outlets__{outlet_name}_snap__2a54eb19_3da0_420d_b964_e4cd8efd371f" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Full_LSUs__lsus1__8f4e9cfb_3ca6_4a70_83b9_fe977379bcf4" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Drawn_inlets_outlets__{outlet_name}__c41cb90c_f1d6_4ffe_8a64_99bcb575d961" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Actual_HRUs__hrus2__7adc36e1_3c7f_40db_8b2c_bb4f79fa3338" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Subbasins__subs1__3017a81e_0174_439c_b815_cf54de0e0667" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Streams__{dem_name}stream__6a837462_9d7d_48f0_a6c1_1710f553d03b" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Channels__{dem_name}channel__a7e3608c_b71d_44f6_8194_67e56bb7c543" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Full_HRUs__hrus1__4e2ba365_e7bd_4f8e_9d6c_79056945afb5" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Pt_sources_and_reservoirs__reservoirs2__ada5d781_850f_43ac_825b_b807e28299e4" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Inlets_outlets__{outlet_name}__0c49465a_2a2b_4ecb_ae4f_fbb60c4c1bcb" enabled="0" tolerance="12" type="1" units="1"/>
      <layer-setting id="Channel_reaches__rivs1__514d2d76_3dcd_4834_8bd4_42392284ab2f" enabled="0" tolerance="12" type="1" units="1"/>
    </individual-layer-settings>
  </snapping-settings>
  <relations/>
  <mapcanvas name="theMapCanvas" annotationsVisible="1">
    <units>meters</units>
    <extent>
      <xmin>325042.12329483608482406</xmin>
      <ymin>1286510.87989890901371837</ymin>
      <xmax>338444.10459518124116585</xmax>
      <ymax>1293740.12989890901371837</ymax>
    </extent>
    <rotation>0</rotation>
    <destinationsrs>
      <spatialrefsys>
         <wkt>{prjcrs}</wkt>
        <proj4>{proj4}</proj4>
        <srsid>{srsid}</srsid>
        <srid>{srid}</srid>
        <authid>EPSG:{srid}</authid>
        <description>{srs_description}</description>
        <projectionacronym>{projectionacronym}</projectionacronym>
        <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
        <geographicflag>{geographicflag}</geographicflag>
      </spatialrefsys>
    </destinationsrs>
    <rendermaptile>0</rendermaptile>
    <expressionContextScope/>
  </mapcanvas>
  <projectModels/>
  <legend updateDrawingOrder="true">
    <legendgroup checked="Qt::Checked" open="true" name="Animations"/>
    <legendgroup checked="Qt::Checked" open="true" name="Results"/>
    <legendgroup checked="Qt::Checked" open="true" name="Watershed">
      <legendlayer checked="Qt::Checked" open="false" showFeatureCount="0" drawingOrder="-1" name="Subbasins (subs1)">
        <filegroup open="false" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Subbasins__subs1__3017a81e_0174_439c_b815_cf54de0e0667"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Pt sources and reservoirs (reservoirs2)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Pt_sources_and_reservoirs__reservoirs2__ada5d781_850f_43ac_825b_b807e28299e4"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Snapped inlets/outlets ({outlet_name}_snap)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Snapped_inlets_outlets__{outlet_name}_snap__2a54eb19_3da0_420d_b964_e4cd8efd371f"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Unchecked" open="true" showFeatureCount="0" drawingOrder="-1" name="Drawn inlets/outlets ({outlet_name})">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="0" isInOverview="0" layerid="Drawn_inlets_outlets__{outlet_name}__c41cb90c_f1d6_4ffe_8a64_99bcb575d961"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Inlets/outlets ({outlet_name})">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Inlets_outlets__{outlet_name}__0c49465a_2a2b_4ecb_ae4f_fbb60c4c1bcb"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Streams ({dem_name}stream)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Streams__{dem_name}stream__6a837462_9d7d_48f0_a6c1_1710f553d03b"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Channel reaches (rivs1)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Channel_reaches__rivs1__514d2d76_3dcd_4834_8bd4_42392284ab2f"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Unchecked" open="true" showFeatureCount="0" drawingOrder="-1" name="Channels ({dem_name}channel)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="0" isInOverview="0" layerid="Channels__{dem_name}channel__a7e3608c_b71d_44f6_8194_67e56bb7c543"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Full LSUs (lsus1)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Full_LSUs__lsus1__8f4e9cfb_3ca6_4a70_83b9_fe977379bcf4"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Actual HRUs (hrus2)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Actual_HRUs__hrus2__7adc36e1_3c7f_40db_8b2c_bb4f79fa3338"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Unchecked" open="true" showFeatureCount="0" drawingOrder="-1" name="Full HRUs (hrus1)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="0" isInOverview="0" layerid="Full_HRUs__hrus1__4e2ba365_e7bd_4f8e_9d6c_79056945afb5"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="false" showFeatureCount="0" drawingOrder="-1" name="Hillshade ({dem_name}hillshade)">
        <filegroup open="false" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Hillshade__{dem_name}hillshade__a6f33483_65e8_4cde_a966_948ff13f0c2a"/>
        </filegroup>
      </legendlayer>
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="DEM ({dem_name})">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="DEM__{dem_name}__f751ab49_fdac_4766_be7f_300fbfe6adf2"/>
        </filegroup>
      </legendlayer>
    </legendgroup>
    <legendgroup checked="Qt::Checked" open="true" name="Landuse">
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Landuses ({landuse_name})">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Landuses__{landuse_name}__f7ec5ca9_3dce_4d3e_8def_9e31ecc6c163"/>
        </filegroup>
      </legendlayer>
    </legendgroup>
    <legendgroup checked="Qt::Checked" open="true" name="Soil">
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Soils ({soil_name})">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Soils__{soil_name}_tif__2cd25288_d1b5_4e76_83af_39034c9f7ffd"/>
        </filegroup>
      </legendlayer>
    </legendgroup>
    <legendgroup checked="Qt::Checked" open="true" name="Slope">
      <legendlayer checked="Qt::Checked" open="true" showFeatureCount="0" drawingOrder="-1" name="Slope bands ({dem_name}slp_bands)">
        <filegroup open="true" hidden="false">
          <legendlayerfile visible="1" isInOverview="0" layerid="Slope_bands__{dem_name}slp_bands__daa1ee9a_d352_4de4_a12e_21aa0143f677"/>
        </filegroup>
      </legendlayer>
    </legendgroup>
  </legend>
  <mapViewDocks/>
  <mapViewDocks3D/>
  <projectlayers>
    <maplayer geometry="Polygon" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="1" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="1" simplifyLocal="1" wkbType="MultiPolygon" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328825.8826469536870718</xmin>
        <ymin>1287329.26022111857309937</ymin>
        <xmax>336355.8826469536870718</xmax>
        <ymax>1292189.26022111857309937</ymax>
      </extent>
      <id>Actual_HRUs__hrus2__7adc36e1_3c7f_40db_8b2c_bb4f79fa3338</id>
      <datasource>./Watershed/Shapes/hrus2.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Actual HRUs (hrus2)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="singleSymbol">
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="fill" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleFill">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="220,255,212,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.06"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="solid"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
        <rotation/>
        <sizescale/>
      </renderer-v2>
      <customproperties/>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Channel">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Landscape">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Landuse">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Soil">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="SlopeBand">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Area">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="%Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="%Landscape">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="HRUS">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="LINKNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="Subbasin" index="0" name=""/>
        <alias field="Channel" index="1" name=""/>
        <alias field="Landscape" index="2" name=""/>
        <alias field="Landuse" index="3" name=""/>
        <alias field="Soil" index="4" name=""/>
        <alias field="SlopeBand" index="5" name=""/>
        <alias field="Area" index="6" name=""/>
        <alias field="%Subbasin" index="7" name=""/>
        <alias field="%Landscape" index="8" name=""/>
        <alias field="HRUS" index="9" name=""/>
        <alias field="LINKNO" index="10" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="Subbasin" applyOnUpdate="0" expression=""/>
        <default field="Channel" applyOnUpdate="0" expression=""/>
        <default field="Landscape" applyOnUpdate="0" expression=""/>
        <default field="Landuse" applyOnUpdate="0" expression=""/>
        <default field="Soil" applyOnUpdate="0" expression=""/>
        <default field="SlopeBand" applyOnUpdate="0" expression=""/>
        <default field="Area" applyOnUpdate="0" expression=""/>
        <default field="%Subbasin" applyOnUpdate="0" expression=""/>
        <default field="%Landscape" applyOnUpdate="0" expression=""/>
        <default field="HRUS" applyOnUpdate="0" expression=""/>
        <default field="LINKNO" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Channel" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Landscape" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Landuse" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Soil" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="SlopeBand" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Area" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="%Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="%Landscape" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="HRUS" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="LINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="Subbasin" exp="" desc=""/>
        <constraint field="Channel" exp="" desc=""/>
        <constraint field="Landscape" exp="" desc=""/>
        <constraint field="Landuse" exp="" desc=""/>
        <constraint field="Soil" exp="" desc=""/>
        <constraint field="SlopeBand" exp="" desc=""/>
        <constraint field="Area" exp="" desc=""/>
        <constraint field="%Subbasin" exp="" desc=""/>
        <constraint field="%Landscape" exp="" desc=""/>
        <constraint field="HRUS" exp="" desc=""/>
        <constraint field="LINKNO" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions>
        <defaultAction value--open-curly--00000000-0000-0000-0000-000000000000--close-curly--" key="Canvas"/>
      </attributeactions>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns/>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../Documents</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
      <editforminitcode><![CDATA[]]></editforminitcode>
      <featformsuppress>0</featformsuppress>
      <editorlayout>generatedlayout</editorlayout>
      <editable/>
      <labelOnTop/>
      <widgets/>
      <previewExpression>"SUBBASIN"</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer geometry="Line" maxScale="0" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="0" simplifyLocal="1" wkbType="MultiLineString" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328870.8826469536870718</xmin>
        <ymin>1287794.26022111857309937</ymin>
        <xmax>335980.8826469536870718</xmax>
        <ymax>1291904.26022111857309937</ymax>
      </extent>
      <id>Channel_reaches__rivs1__514d2d76_3dcd_4834_8bd4_42392284ab2f</id>
      <datasource>./Watershed/Shapes/rivs1.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Channel reaches (rivs1)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
        <rules key--open-curly--50ab9495-26fd-4273-9c00-a04b2e8a8b6c--close-curly--">
          <rule key--open-curly--d08297ae-7ac2-40dd-b266-b666c1d99d5c--close-curly--" label="Channel" symbol="0" filter=" &quot;Reservoir&quot; = 0 AND  &quot;Pond&quot;  = 0"/>
          <rule key--open-curly--49129db6-8dbb-4e40-ad9d-1d806820c5f4--close-curly--" label="Reservoir" symbol="1" filter=" &quot;Reservoir&quot; > 0 AND  &quot;Pond&quot; = 0"/>
          <rule key--open-curly--9ea290bc-2764-4fbe-bbdc-0d991d819325--close-curly--" label="Pond" description="Pond" symbol="2" filter=" &quot;Reservoir&quot; = 0 AND  &quot;Pond&quot; > 0"/>
        </rules>
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="line" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleLine">
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="line" name="1">
            <layer pass="0" locked="0" enabled="1" class="SimpleLine">
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="line" name="2">
            <layer pass="0" locked="0" enabled="1" class="SimpleLine">
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <customproperties>
        <property value="COALESCE(&quot;ID&quot;, '&lt;NULL>')" key="dualview/previewExpressions"/>
        <property value="0" key="embeddedWidgets/count"/>
        <property key="variableNames"/>
        <property key="variableValues"/>
      </customproperties>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="0" scaleDependency="Area" width="15">
          <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="2" zIndex="0" showAll="1" placement="2" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
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
        <alias field="LINKNO" index="0" name=""/>
        <alias field="Channel" index="1" name=""/>
        <alias field="ChannelR" index="2" name=""/>
        <alias field="Subbasin" index="3" name=""/>
        <alias field="AreaC" index="4" name=""/>
        <alias field="Len2" index="5" name=""/>
        <alias field="Slo2" index="6" name=""/>
        <alias field="Wid2" index="7" name=""/>
        <alias field="Dep2" index="8" name=""/>
        <alias field="MinEl" index="9" name=""/>
        <alias field="MaxEl" index="10" name=""/>
        <alias field="Reservoir" index="11" name=""/>
        <alias field="Pond" index="12" name=""/>
        <alias field="LakeIn" index="13" name=""/>
        <alias field="LakeOut" index="14" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="LINKNO" applyOnUpdate="0" expression=""/>
        <default field="Channel" applyOnUpdate="0" expression=""/>
        <default field="ChannelR" applyOnUpdate="0" expression=""/>
        <default field="Subbasin" applyOnUpdate="0" expression=""/>
        <default field="AreaC" applyOnUpdate="0" expression=""/>
        <default field="Len2" applyOnUpdate="0" expression=""/>
        <default field="Slo2" applyOnUpdate="0" expression=""/>
        <default field="Wid2" applyOnUpdate="0" expression=""/>
        <default field="Dep2" applyOnUpdate="0" expression=""/>
        <default field="MinEl" applyOnUpdate="0" expression=""/>
        <default field="MaxEl" applyOnUpdate="0" expression=""/>
        <default field="Reservoir" applyOnUpdate="0" expression=""/>
        <default field="Pond" applyOnUpdate="0" expression=""/>
        <default field="LakeIn" applyOnUpdate="0" expression=""/>
        <default field="LakeOut" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="LINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Channel" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="ChannelR" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="AreaC" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Len2" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Slo2" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Wid2" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Dep2" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="MinEl" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="MaxEl" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Reservoir" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Pond" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="LakeIn" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="LakeOut" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="LINKNO" exp="" desc=""/>
        <constraint field="Channel" exp="" desc=""/>
        <constraint field="ChannelR" exp="" desc=""/>
        <constraint field="Subbasin" exp="" desc=""/>
        <constraint field="AreaC" exp="" desc=""/>
        <constraint field="Len2" exp="" desc=""/>
        <constraint field="Slo2" exp="" desc=""/>
        <constraint field="Wid2" exp="" desc=""/>
        <constraint field="Dep2" exp="" desc=""/>
        <constraint field="MinEl" exp="" desc=""/>
        <constraint field="MaxEl" exp="" desc=""/>
        <constraint field="Reservoir" exp="" desc=""/>
        <constraint field="Pond" exp="" desc=""/>
        <constraint field="LakeIn" exp="" desc=""/>
        <constraint field="LakeOut" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions>
        <defaultAction value--open-curly--00000000-0000-0000-0000-000000000000--close-curly--" key="Canvas"/>
      </attributeactions>
      <attributetableconfig sortExpression="&quot;Pond&quot;" sortOrder="1" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="Channel"/>
          <column width="-1" hidden="0" type="field" name="ChannelR"/>
          <column width="-1" hidden="0" type="field" name="Subbasin"/>
          <column width="-1" hidden="0" type="field" name="AreaC"/>
          <column width="-1" hidden="0" type="field" name="Len2"/>
          <column width="-1" hidden="0" type="field" name="Slo2"/>
          <column width="-1" hidden="0" type="field" name="Wid2"/>
          <column width="-1" hidden="0" type="field" name="Dep2"/>
          <column width="-1" hidden="0" type="field" name="MinEl"/>
          <column width="-1" hidden="0" type="field" name="MaxEl"/>
          <column width="-1" hidden="0" type="field" name="Reservoir"/>
          <column width="-1" hidden="1" type="actions"/>
          <column width="-1" hidden="0" type="field" name="LINKNO"/>
          <column width="-1" hidden="0" type="field" name="Pond"/>
          <column width="-1" hidden="0" type="field" name="LakeIn"/>
          <column width="-1" hidden="0" type="field" name="LakeOut"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../../../PROGRA~1/QGIS3~1.4/bin</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath>../../../../../PROGRA~1/QGIS3~1.4/bin</editforminitfilepath>
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
        <field editable="1" name="AreaC"/>
        <field editable="1" name="Channel"/>
        <field editable="1" name="ChannelR"/>
        <field editable="1" name="Dep2"/>
        <field editable="1" name="LINKNO"/>
        <field editable="1" name="LakeIn"/>
        <field editable="1" name="LakeOut"/>
        <field editable="1" name="Len2"/>
        <field editable="1" name="MaxEl"/>
        <field editable="1" name="MinEl"/>
        <field editable="1" name="Pond"/>
        <field editable="1" name="Reservoir"/>
        <field editable="1" name="Slo2"/>
        <field editable="1" name="Subbasin"/>
        <field editable="1" name="Wid2"/>
      </editable>
      <labelOnTop>
        <field labelOnTop="0" name="AreaC"/>
        <field labelOnTop="0" name="Channel"/>
        <field labelOnTop="0" name="ChannelR"/>
        <field labelOnTop="0" name="Dep2"/>
        <field labelOnTop="0" name="LINKNO"/>
        <field labelOnTop="0" name="LakeIn"/>
        <field labelOnTop="0" name="LakeOut"/>
        <field labelOnTop="0" name="Len2"/>
        <field labelOnTop="0" name="MaxEl"/>
        <field labelOnTop="0" name="MinEl"/>
        <field labelOnTop="0" name="Pond"/>
        <field labelOnTop="0" name="Reservoir"/>
        <field labelOnTop="0" name="Slo2"/>
        <field labelOnTop="0" name="Subbasin"/>
        <field labelOnTop="0" name="Wid2"/>
      </labelOnTop>
      <widgets/>
      <previewExpression>COALESCE("ID", '&lt;NULL>')</previewExpression>
      <mapTip>ID</mapTip>
    </maplayer>
    <maplayer geometry="Line" maxScale="0" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="1" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="1" simplifyLocal="1" wkbType="MultiLineString" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328870.8826469536870718</xmin>
        <ymin>1287794.26022111857309937</ymin>
        <xmax>335980.8826469536870718</xmax>
        <ymax>1291904.26022111857309937</ymax>
      </extent>
      <id>Channels__{dem_name}channel__a7e3608c_b71d_44f6_8194_67e56bb7c543</id>
      <datasource>./Watershed/Shapes/{dem_name}channel.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Channels ({dem_name}channel)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="singleSymbol">
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="line" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleLine">
              <prop k="capstyle" v="square"/>
              <prop k="customdash" v="5;2"/>
              <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="customdash_unit" v="MM"/>
              <prop k="draw_inside_polygon" v="0"/>
              <prop k="joinstyle" v="bevel"/>
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
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
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="inf" scaleDependency="Area" width="15">
          <fontProperties style="" description="Ubuntu,8,-1,5,1,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="10" zIndex="0" showAll="1" placement="2" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="LINKNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DSLINKNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="USLINKNO1">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="USLINKNO2">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DSNODEID">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Order">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Length">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Magnitude">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DS_Cont_Ar">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Drop">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Slope">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Straight_L">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="US_Cont_Ar">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="WSNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DOUT_END">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DOUT_START">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DOUT_MID">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="BasinNo">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="LINKNO" index="0" name=""/>
        <alias field="DSLINKNO" index="1" name=""/>
        <alias field="USLINKNO1" index="2" name=""/>
        <alias field="USLINKNO2" index="3" name=""/>
        <alias field="DSNODEID" index="4" name=""/>
        <alias field="Order" index="5" name=""/>
        <alias field="Length" index="6" name=""/>
        <alias field="Magnitude" index="7" name=""/>
        <alias field="DS_Cont_Ar" index="8" name=""/>
        <alias field="Drop" index="9" name=""/>
        <alias field="Slope" index="10" name=""/>
        <alias field="Straight_L" index="11" name=""/>
        <alias field="US_Cont_Ar" index="12" name=""/>
        <alias field="WSNO" index="13" name=""/>
        <alias field="DOUT_END" index="14" name=""/>
        <alias field="DOUT_START" index="15" name=""/>
        <alias field="DOUT_MID" index="16" name=""/>
        <alias field="BasinNo" index="17" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="LINKNO" applyOnUpdate="0" expression=""/>
        <default field="DSLINKNO" applyOnUpdate="0" expression=""/>
        <default field="USLINKNO1" applyOnUpdate="0" expression=""/>
        <default field="USLINKNO2" applyOnUpdate="0" expression=""/>
        <default field="DSNODEID" applyOnUpdate="0" expression=""/>
        <default field="Order" applyOnUpdate="0" expression=""/>
        <default field="Length" applyOnUpdate="0" expression=""/>
        <default field="Magnitude" applyOnUpdate="0" expression=""/>
        <default field="DS_Cont_Ar" applyOnUpdate="0" expression=""/>
        <default field="Drop" applyOnUpdate="0" expression=""/>
        <default field="Slope" applyOnUpdate="0" expression=""/>
        <default field="Straight_L" applyOnUpdate="0" expression=""/>
        <default field="US_Cont_Ar" applyOnUpdate="0" expression=""/>
        <default field="WSNO" applyOnUpdate="0" expression=""/>
        <default field="DOUT_END" applyOnUpdate="0" expression=""/>
        <default field="DOUT_START" applyOnUpdate="0" expression=""/>
        <default field="DOUT_MID" applyOnUpdate="0" expression=""/>
        <default field="BasinNo" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="LINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DSLINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="USLINKNO1" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="USLINKNO2" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DSNODEID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Order" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Length" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Magnitude" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DS_Cont_Ar" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Drop" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Slope" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Straight_L" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="US_Cont_Ar" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="WSNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DOUT_END" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DOUT_START" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DOUT_MID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="BasinNo" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="LINKNO" exp="" desc=""/>
        <constraint field="DSLINKNO" exp="" desc=""/>
        <constraint field="USLINKNO1" exp="" desc=""/>
        <constraint field="USLINKNO2" exp="" desc=""/>
        <constraint field="DSNODEID" exp="" desc=""/>
        <constraint field="Order" exp="" desc=""/>
        <constraint field="Length" exp="" desc=""/>
        <constraint field="Magnitude" exp="" desc=""/>
        <constraint field="DS_Cont_Ar" exp="" desc=""/>
        <constraint field="Drop" exp="" desc=""/>
        <constraint field="Slope" exp="" desc=""/>
        <constraint field="Straight_L" exp="" desc=""/>
        <constraint field="US_Cont_Ar" exp="" desc=""/>
        <constraint field="WSNO" exp="" desc=""/>
        <constraint field="DOUT_END" exp="" desc=""/>
        <constraint field="DOUT_START" exp="" desc=""/>
        <constraint field="DOUT_MID" exp="" desc=""/>
        <constraint field="BasinNo" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions/>
      <attributetableconfig sortExpression="" sortOrder="1" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="LINKNO"/>
          <column width="-1" hidden="0" type="field" name="DSLINKNO"/>
          <column width="-1" hidden="0" type="field" name="USLINKNO1"/>
          <column width="-1" hidden="0" type="field" name="USLINKNO2"/>
          <column width="-1" hidden="0" type="field" name="DSNODEID"/>
          <column width="-1" hidden="0" type="field" name="Order"/>
          <column width="-1" hidden="0" type="field" name="Length"/>
          <column width="-1" hidden="0" type="field" name="Magnitude"/>
          <column width="-1" hidden="0" type="field" name="DS_Cont_Ar"/>
          <column width="-1" hidden="0" type="field" name="Drop"/>
          <column width="-1" hidden="0" type="field" name="Slope"/>
          <column width="-1" hidden="0" type="field" name="Straight_L"/>
          <column width="-1" hidden="0" type="field" name="US_Cont_Ar"/>
          <column width="-1" hidden="0" type="field" name="WSNO"/>
          <column width="-1" hidden="0" type="field" name="DOUT_END"/>
          <column width="-1" hidden="0" type="field" name="DOUT_START"/>
          <column width="-1" hidden="0" type="field" name="DOUT_MID"/>
          <column width="-1" hidden="0" type="field" name="BasinNo"/>
          <column width="-1" hidden="1" type="actions"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1"></editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
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
      <editable/>
      <labelOnTop/>
      <widgets/>
      <previewExpression>"DSNODEID"</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" refreshOnNotifyEnabled="0" autoRefreshTime="0" minScale="1e+08" refreshOnNotifyMessage="" type="raster" autoRefreshEnabled="0" maxScale="0">
      <extent>
        <xmin>326065.8826469536870718</xmin>
        <ymin>1286069.26022111857309937</ymin>
        <xmax>338065.8826469536870718</xmax>
        <ymax>1293509.26022111857309937</ymax>
      </extent>
      <id>DEM__{dem_name}__f751ab49_fdac_4766_be7f_300fbfe6adf2</id>
      <datasource>./Watershed/Rasters/DEM/{dem_file_name}</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>DEM ({dem_name})</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type></type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider>gdal</provider>
      <noData>
        <noDataList useSrcNoData="1" bandNo="1"/>
      </noData>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <customproperties>
        <property value="Value" key="identify/format"/>
      </customproperties>
      <pipe>
        <rasterrenderer opacity="1" alphaBand="-1" band="1" classificationMin="nan" type="singlebandpseudocolor" classificationMax="nan">
          <minMaxOrigin>
            <limits>None</limits>
            <extent>WholeRaster</extent>
            <statAccuracy>Estimated</statAccuracy>
            <cumulativeCutLower>0.02</cumulativeCutLower>
            <cumulativeCutUpper>0.98</cumulativeCutUpper>
            <stdDevFactor>2</stdDevFactor>
          </minMaxOrigin>
          <rastershader>
            <colorrampshader clip="0" colorRampType="INTERPOLATED" classificationMode="1">
              <item value="{dem_min}" color="#0a640a" label="{dem_min} - {lower_third}" alpha="255"/>
              <item value="{mid_thirds}" color="#997d19" label="{lower_third} - {upper_third}" alpha="255"/>
              <item value="{dem_max}" color="#ffffff" label="{upper_third} - {dem_max}" alpha="255"/>
            </colorrampshader>
          </rastershader>
        </rasterrenderer>
        <brightnesscontrast contrast="0" brightness="0"/>
        <huesaturation colorizeStrength="100" colorizeOn="0" grayscaleMode="0" colorizeGreen="128" saturation="0" colorizeBlue="128" colorizeRed="255"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </maplayer>
    <maplayer geometry="Point" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="0" simplifyLocal="1" wkbType="Point" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328872.81934636097867042</xmin>
        <ymin>1290232.52846676157787442</ymin>
        <xmax>328872.81934636097867042</xmax>
        <ymax>1290232.52846676157787442</ymax>
      </extent>
      <id>Drawn_inlets_outlets__{outlet_name}__c41cb90c_f1d6_4ffe_8a64_99bcb575d961</id>
      <datasource>./Watershed/Shapes/{outlet_name}.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Drawn inlets/outlets ({outlet_name})</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
        <rules key--open-curly--53a471a4-aa86-43ed-9d97-be98a958b7e1--close-curly--">
          <rule key--open-curly--57a0b081-f9fc-46d9-a9f0-302b4d29c4d2--close-curly--" label="Outlet" description="Outlet" symbol="0" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 0"/>
          <rule key--open-curly--2b092b12-ae87-4524-bf91-ee93b3bfee30--close-curly--" label="Inlet" description="Inlet" symbol="1" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 0"/>
          <rule key--open-curly--cc102ca4-a33c-498d-a2fc-8e598f588d20--close-curly--" label="Reservoir" symbol="2" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 1"/>
          <rule key--open-curly--0ede00e4-44a0-41de-b5a4-41741e7a90ad--close-curly--" label="Pond" description="Pond" symbol="3" filter="&quot;INLET&quot; = 0 AND &quot;RES&quot; = 2"/>
          <rule key--open-curly--bb3546f0-1b2c-49be-a16f-9bb5728352fd--close-curly--" label="Point source" description="Point source" symbol="4" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 1"/>
        </rules>
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="filled_arrowhead"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="1">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="180"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="filled_arrowhead"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="2">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="3">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="30,55,244,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2.6"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="4">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <customproperties>
        <property value="&quot;ID&quot;" key="dualview/previewExpressions"/>
        <property value="0" key="embeddedWidgets/count"/>
        <property key="variableNames"/>
        <property key="variableValues"/>
      </customproperties>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="-4.65661e-10" scaleDependency="Area" width="15">
          <fontProperties style="" description="Ubuntu,8,-1,5,1,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="18" zIndex="0" showAll="1" placement="0" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="ID">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="INLET">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="RES">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="PTSOURCE">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="ID" index="0" name=""/>
        <alias field="INLET" index="1" name=""/>
        <alias field="RES" index="2" name=""/>
        <alias field="PTSOURCE" index="3" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="ID" applyOnUpdate="0" expression=""/>
        <default field="INLET" applyOnUpdate="0" expression=""/>
        <default field="RES" applyOnUpdate="0" expression=""/>
        <default field="PTSOURCE" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="ID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="INLET" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="RES" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="PTSOURCE" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="ID" exp="" desc=""/>
        <constraint field="INLET" exp="" desc=""/>
        <constraint field="RES" exp="" desc=""/>
        <constraint field="PTSOURCE" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions>
        <defaultAction value--open-curly--00000000-0000-0000-0000-000000000000--close-curly--" key="Canvas"/>
      </attributeactions>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="PTSOURCE"/>
          <column width="-1" hidden="0" type="field" name="RES"/>
          <column width="-1" hidden="0" type="field" name="INLET"/>
          <column width="-1" hidden="0" type="field" name="ID"/>
          <column width="-1" hidden="1" type="actions"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">QSWATPlus_Projects/SanJuan/test1</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
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
        <field editable="1" name="ID"/>
        <field editable="1" name="INLET"/>
        <field editable="1" name="PTSOURCE"/>
        <field editable="1" name="RES"/>
      </editable>
      <labelOnTop>
        <field labelOnTop="0" name="ID"/>
        <field labelOnTop="0" name="INLET"/>
        <field labelOnTop="0" name="PTSOURCE"/>
        <field labelOnTop="0" name="RES"/>
      </labelOnTop>
      <widgets/>
      <previewExpression>ID</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer geometry="Polygon" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="1" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="1" simplifyLocal="1" wkbType="MultiPolygon" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328825.8826469536870718</xmin>
        <ymin>1287329.26022111857309937</ymin>
        <xmax>336355.8826469536870718</xmax>
        <ymax>1292189.26022111857309937</ymax>
      </extent>
      <id>Full_HRUs__hrus1__4e2ba365_e7bd_4f8e_9d6c_79056945afb5</id>
      <datasource>./Watershed/Shapes/hrus1.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Full HRUs (hrus1)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="singleSymbol">
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="fill" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleFill">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="220,255,212,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.06"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="solid"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
        <rotation/>
        <sizescale/>
      </renderer-v2>
      <customproperties/>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Channel">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Landscape">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Landuse">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Soil">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="SlopeBand">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Area">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="%Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="%Landscape">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="HRUS">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="LINKNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="Subbasin" index="0" name=""/>
        <alias field="Channel" index="1" name=""/>
        <alias field="Landscape" index="2" name=""/>
        <alias field="Landuse" index="3" name=""/>
        <alias field="Soil" index="4" name=""/>
        <alias field="SlopeBand" index="5" name=""/>
        <alias field="Area" index="6" name=""/>
        <alias field="%Subbasin" index="7" name=""/>
        <alias field="%Landscape" index="8" name=""/>
        <alias field="HRUS" index="9" name=""/>
        <alias field="LINKNO" index="10" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="Subbasin" applyOnUpdate="0" expression=""/>
        <default field="Channel" applyOnUpdate="0" expression=""/>
        <default field="Landscape" applyOnUpdate="0" expression=""/>
        <default field="Landuse" applyOnUpdate="0" expression=""/>
        <default field="Soil" applyOnUpdate="0" expression=""/>
        <default field="SlopeBand" applyOnUpdate="0" expression=""/>
        <default field="Area" applyOnUpdate="0" expression=""/>
        <default field="%Subbasin" applyOnUpdate="0" expression=""/>
        <default field="%Landscape" applyOnUpdate="0" expression=""/>
        <default field="HRUS" applyOnUpdate="0" expression=""/>
        <default field="LINKNO" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Channel" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Landscape" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Landuse" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Soil" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="SlopeBand" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Area" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="%Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="%Landscape" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="HRUS" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="LINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="Subbasin" exp="" desc=""/>
        <constraint field="Channel" exp="" desc=""/>
        <constraint field="Landscape" exp="" desc=""/>
        <constraint field="Landuse" exp="" desc=""/>
        <constraint field="Soil" exp="" desc=""/>
        <constraint field="SlopeBand" exp="" desc=""/>
        <constraint field="Area" exp="" desc=""/>
        <constraint field="%Subbasin" exp="" desc=""/>
        <constraint field="%Landscape" exp="" desc=""/>
        <constraint field="HRUS" exp="" desc=""/>
        <constraint field="LINKNO" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions/>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns/>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../Documents</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
      <editforminitcode><![CDATA[]]></editforminitcode>
      <featformsuppress>0</featformsuppress>
      <editorlayout>generatedlayout</editorlayout>
      <editable/>
      <labelOnTop/>
      <widgets/>
      <previewExpression>"SUBBASIN"</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer geometry="Polygon" maxScale="0" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="1" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="1" simplifyLocal="1" wkbType="MultiPolygon" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328825.8826469536870718</xmin>
        <ymin>1287329.26022111857309937</ymin>
        <xmax>336355.8826469536870718</xmax>
        <ymax>1292189.26022111857309937</ymax>
      </extent>
      <id>Full_LSUs__lsus1__8f4e9cfb_3ca6_4a70_83b9_fe977379bcf4</id>
      <datasource>./Watershed/Shapes/lsus1.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Full LSUs (lsus1)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="singleSymbol">
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="fill" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleFill">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="0,0,255,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="248,157,178,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.3"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="no"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
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
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="inf" scaleDependency="Area" width="15">
          <fontProperties style="" description="Ubuntu,8,-1,5,1,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="10" zIndex="0" showAll="1" placement="0" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="Area">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Channel">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="LSUID">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Landscape">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="%Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="Area" index="0" name=""/>
        <alias field="Channel" index="1" name=""/>
        <alias field="LSUID" index="2" name=""/>
        <alias field="Subbasin" index="3" name=""/>
        <alias field="Landscape" index="4" name=""/>
        <alias field="%Subbasin" index="5" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="Area" applyOnUpdate="0" expression=""/>
        <default field="Channel" applyOnUpdate="0" expression=""/>
        <default field="LSUID" applyOnUpdate="0" expression=""/>
        <default field="Subbasin" applyOnUpdate="0" expression=""/>
        <default field="Landscape" applyOnUpdate="0" expression=""/>
        <default field="%Subbasin" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="Area" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Channel" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="LSUID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Landscape" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="%Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="Area" exp="" desc=""/>
        <constraint field="Channel" exp="" desc=""/>
        <constraint field="LSUID" exp="" desc=""/>
        <constraint field="Subbasin" exp="" desc=""/>
        <constraint field="Landscape" exp="" desc=""/>
        <constraint field="%Subbasin" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions/>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="AREA (ha)"/>
          <column width="-1" hidden="0" type="field" name="Channel"/>
          <column width="-1" hidden="0" type="field" name="LSUID"/>
          <column width="-1" hidden="0" type="field" name="Subbasin"/>
          <column width="-1" hidden="0" type="field" name="Landscape"/>
          <column width="-1" hidden="0" type="field" name="%SUBBASIN"/>
          <column width="-1" hidden="1" type="actions"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1"></editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
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
      <editable/>
      <labelOnTop/>
      <widgets/>
      <previewExpression>"LSUID"</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" refreshOnNotifyEnabled="0" autoRefreshTime="0" minScale="1e+08" refreshOnNotifyMessage="" type="raster" autoRefreshEnabled="0" maxScale="0">
      <extent>
        <xmin>326065.8826469536870718</xmin>
        <ymin>1286069.26022111857309937</ymin>
        <xmax>338065.8826469536870718</xmax>
        <ymax>1293509.26022111857309937</ymax>
      </extent>
      <id>Hillshade__{dem_name}hillshade__a6f33483_65e8_4cde_a966_948ff13f0c2a</id>
      <datasource>./Watershed/Rasters/DEM/{dem_name}hillshade.tif</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Hillshade ({dem_name}hillshade)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type></type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider>gdal</provider>
      <noData>
        <noDataList useSrcNoData="1" bandNo="1"/>
      </noData>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <customproperties>
        <property value="Value" key="identify/format"/>
      </customproperties>
      <pipe>
        <rasterrenderer opacity="0.4" alphaBand="-1" gradient="BlackToWhite" grayBand="1" type="singlebandgray">
          <rasterTransparency/>
          <minMaxOrigin>
            <limits>MinMax</limits>
            <extent>WholeRaster</extent>
            <statAccuracy>Estimated</statAccuracy>
            <cumulativeCutLower>0.02</cumulativeCutLower>
            <cumulativeCutUpper>0.98</cumulativeCutUpper>
            <stdDevFactor>2</stdDevFactor>
          </minMaxOrigin>
          <contrastEnhancement>
            <minValue>1</minValue>
            <maxValue>255</maxValue>
            <algorithm>StretchToMinimumMaximum</algorithm>
          </contrastEnhancement>
        </rasterrenderer>
        <brightnesscontrast contrast="0" brightness="0"/>
        <huesaturation colorizeStrength="100" colorizeOn="0" grayscaleMode="0" colorizeGreen="128" saturation="0" colorizeBlue="128" colorizeRed="255"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </maplayer>
    <maplayer geometry="Point" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="0" simplifyLocal="1" wkbType="Point" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328653</xmin>
        <ymin>1290104</ymin>
        <xmax>328653</xmax>
        <ymax>1290104</ymax>
      </extent>
      <id>Inlets_outlets__{outlet_name}__0c49465a_2a2b_4ecb_ae4f_fbb60c4c1bcb</id>
      <datasource>./Watershed/Shapes/{outlet_name}.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Inlets/outlets ({outlet_name})</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
        <rules key--open-curly--53a471a4-aa86-43ed-9d97-be98a958b7e1--close-curly--">
          <rule key--open-curly--57a0b081-f9fc-46d9-a9f0-302b4d29c4d2--close-curly--" label="Outlet" description="Outlet" symbol="0" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 0"/>
          <rule key--open-curly--2b092b12-ae87-4524-bf91-ee93b3bfee30--close-curly--" label="Inlet" description="Inlet" symbol="1" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 0"/>
          <rule key--open-curly--cc102ca4-a33c-498d-a2fc-8e598f588d20--close-curly--" label="Reservoir" symbol="2" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 1"/>
          <rule key--open-curly--0ede00e4-44a0-41de-b5a4-41741e7a90ad--close-curly--" label="Pond" description="Pond" symbol="3" filter="&quot;INLET&quot; = 0 AND &quot;RES&quot; = 2"/>
          <rule key--open-curly--bb3546f0-1b2c-49be-a16f-9bb5728352fd--close-curly--" label="Point source" description="Point source" symbol="4" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 1"/>
        </rules>
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="filled_arrowhead"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="1">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="180"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="filled_arrowhead"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="2">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="3">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="30,55,244,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2.6"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="4">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <customproperties>
        <property value="&quot;ID&quot;" key="dualview/previewExpressions"/>
        <property value="0" key="embeddedWidgets/count"/>
        <property key="variableNames"/>
        <property key="variableValues"/>
      </customproperties>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="-4.65661e-10" scaleDependency="Area" width="15">
          <fontProperties style="" description="Ubuntu,8,-1,5,1,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="18" zIndex="0" showAll="1" placement="0" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="ID">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="INLET">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="RES">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="PTSOURCE">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="ID" index="0" name=""/>
        <alias field="INLET" index="1" name=""/>
        <alias field="RES" index="2" name=""/>
        <alias field="PTSOURCE" index="3" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="ID" applyOnUpdate="0" expression=""/>
        <default field="INLET" applyOnUpdate="0" expression=""/>
        <default field="RES" applyOnUpdate="0" expression=""/>
        <default field="PTSOURCE" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="ID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="INLET" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="RES" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="PTSOURCE" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="ID" exp="" desc=""/>
        <constraint field="INLET" exp="" desc=""/>
        <constraint field="RES" exp="" desc=""/>
        <constraint field="PTSOURCE" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions>
        <defaultAction value--open-curly--00000000-0000-0000-0000-000000000000--close-curly--" key="Canvas"/>
      </attributeactions>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="PTSOURCE"/>
          <column width="-1" hidden="0" type="field" name="RES"/>
          <column width="-1" hidden="0" type="field" name="INLET"/>
          <column width="-1" hidden="0" type="field" name="ID"/>
          <column width="-1" hidden="1" type="actions"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">QSWATPlus_Projects/SanJuan/test1</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
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
        <field editable="1" name="ID"/>
        <field editable="1" name="INLET"/>
        <field editable="1" name="PTSOURCE"/>
        <field editable="1" name="RES"/>
      </editable>
      <labelOnTop>
        <field labelOnTop="0" name="ID"/>
        <field labelOnTop="0" name="INLET"/>
        <field labelOnTop="0" name="PTSOURCE"/>
        <field labelOnTop="0" name="RES"/>
      </labelOnTop>
      <widgets/>
      <previewExpression>ID</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" refreshOnNotifyEnabled="0" autoRefreshTime="0" minScale="1e+08" refreshOnNotifyMessage="" type="raster" autoRefreshEnabled="0" maxScale="0">
      <extent>
        <xmin>{extent_xmin}</xmin>
        <ymin>{extent_ymin}</ymin>
        <xmax>{extent_xmax}</xmax>
        <ymax>{extent_ymax}</ymax>
      </extent>
      <id>Landuses__{landuse_name}__f7ec5ca9_3dce_4d3e_8def_9e31ecc6c163</id>
      <datasource>./Watershed/Rasters/Landuse/{landuse_file_name}</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Landuses ({landuse_name})</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type></type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider>gdal</provider>
      <noData>
        <noDataList useSrcNoData="1" bandNo="1"/>
      </noData>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <customproperties>
        <property value="Value" key="identify/format"/>
      </customproperties>
      <pipe>
        <rasterrenderer opacity="1" alphaBand="-1" band="1" classificationMin="nan" type="singlebandpseudocolor" classificationMax="nan">
          <minMaxOrigin>
            <limits>None</limits>
            <extent>WholeRaster</extent>
            <statAccuracy>Estimated</statAccuracy>
            <cumulativeCutLower>0.02</cumulativeCutLower>
            <cumulativeCutUpper>0.98</cumulativeCutUpper>
            <stdDevFactor>2</stdDevFactor>
          </minMaxOrigin>
          <rastershader>
            <colorrampshader clip="0" colorRampType="DISCRETE" classificationMode="1">
              <item value="0" color="#a2a3c2" label="AGRL" alpha="255"/>
              <item value="2" color="#c9dce1" label="AGRL" alpha="255"/>
              <item value="3" color="#4b0105" label="PAST" alpha="255"/>
              <item value="4" color="#60f22b" label="FRST" alpha="255"/>
            </colorrampshader>
          </rastershader>
        </rasterrenderer>
        <brightnesscontrast contrast="0" brightness="0"/>
        <huesaturation colorizeStrength="100" colorizeOn="0" grayscaleMode="0" colorizeGreen="128" saturation="0" colorizeBlue="128" colorizeRed="255"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </maplayer>
    <maplayer geometry="Point" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="0" simplifyLocal="1" wkbType="Point" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328900.8826469536870718</xmin>
        <ymin>1287794.26022111857309937</ymin>
        <xmax>335980.8826469536870718</xmax>
        <ymax>1291904.26022111857309937</ymax>
      </extent>
      <id>Pt_sources_and_reservoirs__reservoirs2__ada5d781_850f_43ac_825b_b807e28299e4</id>
      <datasource>./Watershed/Shapes/reservoirs2.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Pt sources and reservoirs (reservoirs2)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
        <rules key--open-curly--53a471a4-aa86-43ed-9d97-be98a958b7e1--close-curly--">
          <rule key--open-curly--cc102ca4-a33c-498d-a2fc-8e598f588d20--close-curly--" label="Reservoir" symbol="0" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 1"/>
          <rule key--open-curly--210e8415-28da-4360-9dcb-9c89a8497b13--close-curly--" label="Point source" description="Point source" symbol="1" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 1"/>
        </rules>
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="1">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <customproperties>
        <property value="0" key="embeddedWidgets/count"/>
        <property key="variableNames"/>
        <property key="variableValues"/>
      </customproperties>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="-4.65661e-10" scaleDependency="Area" width="15">
          <fontProperties style="" description="Ubuntu,8,-1,5,1,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="18" zIndex="0" showAll="1" placement="0" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="ID">
          <editWidget type="TextEdit">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="INLET">
          <editWidget type="TextEdit">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="RES">
          <editWidget type="TextEdit">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="PTSOURCE">
          <editWidget type="TextEdit">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="ID" index="0" name=""/>
        <alias field="INLET" index="1" name=""/>
        <alias field="RES" index="2" name=""/>
        <alias field="PTSOURCE" index="3" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="ID" applyOnUpdate="0" expression=""/>
        <default field="INLET" applyOnUpdate="0" expression=""/>
        <default field="RES" applyOnUpdate="0" expression=""/>
        <default field="PTSOURCE" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="ID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="INLET" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="RES" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="PTSOURCE" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="ID" exp="" desc=""/>
        <constraint field="INLET" exp="" desc=""/>
        <constraint field="RES" exp="" desc=""/>
        <constraint field="PTSOURCE" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions>
        <defaultAction value--open-curly--00000000-0000-0000-0000-000000000000--close-curly--" key="Canvas"/>
      </attributeactions>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="ID"/>
          <column width="-1" hidden="0" type="field" name="INLET"/>
          <column width="-1" hidden="0" type="field" name="RES"/>
          <column width="-1" hidden="0" type="field" name="PTSOURCE"/>
          <column width="-1" hidden="1" type="actions"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../Documents</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
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
        <field editable="1" name="ID"/>
        <field editable="1" name="INLET"/>
        <field editable="1" name="PTSOURCE"/>
        <field editable="1" name="RES"/>
      </editable>
      <labelOnTop>
        <field labelOnTop="0" name="ID"/>
        <field labelOnTop="0" name="INLET"/>
        <field labelOnTop="0" name="PTSOURCE"/>
        <field labelOnTop="0" name="RES"/>
      </labelOnTop>
      <widgets/>
      <previewExpression>ID</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" refreshOnNotifyEnabled="0" autoRefreshTime="0" minScale="1e+08" refreshOnNotifyMessage="" type="raster" autoRefreshEnabled="0" maxScale="0">
      <extent>
        <xmin>326065.8826469536870718</xmin>
        <ymin>1286069.26022111857309937</ymin>
        <xmax>338065.8826469536870718</xmax>
        <ymax>1293509.26022111857309937</ymax>
      </extent>
      <id>Slope_bands__{dem_name}slp_bands__daa1ee9a_d352_4de4_a12e_21aa0143f677</id>
      <datasource>./Watershed/Rasters/DEM/{dem_name}slp_bands.tif</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Slope bands ({dem_name}slp_bands)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type></type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider>gdal</provider>
      <noData>
        <noDataList useSrcNoData="0" bandNo="1"/>
      </noData>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <customproperties>
        <property value="Value" key="identify/format"/>
      </customproperties>
      <pipe>
        <rasterrenderer opacity="1" alphaBand="-1" band="1" classificationMin="nan" type="singlebandpseudocolor" classificationMax="nan">
          <minMaxOrigin>
            <limits>None</limits>
            <extent>WholeRaster</extent>
            <statAccuracy>Estimated</statAccuracy>
            <cumulativeCutLower>0.02</cumulativeCutLower>
            <cumulativeCutUpper>0.98</cumulativeCutUpper>
            <stdDevFactor>2</stdDevFactor>
          </minMaxOrigin>
          <rastershader>
            <colorrampshader clip="0" colorRampType="DISCRETE" classificationMode="1">
              <item value="0" color="#fafafa" label="0-5.0" alpha="255"/>
              <item value="1" color="#050505" label="5.0-9999" alpha="255"/>
            </colorrampshader>
          </rastershader>
        </rasterrenderer>
        <brightnesscontrast contrast="0" brightness="0"/>
        <huesaturation colorizeStrength="100" colorizeOn="0" grayscaleMode="0" colorizeGreen="128" saturation="0" colorizeBlue="128" colorizeRed="255"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </maplayer>
    <maplayer geometry="Point" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="0" simplifyLocal="1" wkbType="Point" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328867</xmin>
        <ymin>1290227</ymin>
        <xmax>328867</xmax>
        <ymax>1290227</ymax>
      </extent>
      <id>Snapped_inlets_outlets__{outlet_name}_snap__2a54eb19_3da0_420d_b964_e4cd8efd371f</id>
      <datasource>./Watershed/Shapes/{outlet_name}_snap.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Snapped inlets/outlets ({outlet_name}_snap)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
        <rules key--open-curly--53a471a4-aa86-43ed-9d97-be98a958b7e1--close-curly--">
          <rule key--open-curly--57a0b081-f9fc-46d9-a9f0-302b4d29c4d2--close-curly--" label="Outlet" description="Outlet" symbol="0" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 0"/>
          <rule key--open-curly--2b092b12-ae87-4524-bf91-ee93b3bfee30--close-curly--" label="Inlet" description="Inlet" symbol="1" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 0"/>
          <rule key--open-curly--cc102ca4-a33c-498d-a2fc-8e598f588d20--close-curly--" label="Reservoir" symbol="2" filter=" &quot;INLET&quot;  = 0  AND  &quot;RES&quot; = 1"/>
          <rule key--open-curly--0ede00e4-44a0-41de-b5a4-41741e7a90ad--close-curly--" label="Pond" description="Pond" symbol="3" filter="&quot;INLET&quot; = 0 AND &quot;RES&quot; = 2"/>
          <rule key--open-curly--bb3546f0-1b2c-49be-a16f-9bb5728352fd--close-curly--" label="Point source" description="Point source" symbol="4" filter=" &quot;INLET&quot;  = 1  AND   &quot;PTSOURCE&quot;  = 1"/>
        </rules>
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="filled_arrowhead"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="1">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="180"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="filled_arrowhead"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="2">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,85,255,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="3">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="30,55,244,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2.6"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="marker" name="4">
            <layer pass="0" locked="0" enabled="1" class="SimpleMarker">
              <prop k="angle" v="0"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="0,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="area"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <customproperties>
        <property value="&quot;ID&quot;" key="dualview/previewExpressions"/>
        <property value="0" key="embeddedWidgets/count"/>
        <property key="variableNames"/>
        <property key="variableValues"/>
      </customproperties>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
        <DiagramCategory scaleBasedVisibility="0" lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" rotationOffset="270" minimumSize="0" diagramOrientation="Up" barWidth="5" maxScaleDenominator="1e+08" opacity="1" labelPlacementMethod="XHeight" backgroundAlpha="255" lineSizeScale="3x:0,0,0,0,0,0" backgroundColor="#ffffff" sizeType="MM" penColor="#000000" height="15" enabled="0" penWidth="0" penAlpha="255" minScaleDenominator="-4.65661e-10" scaleDependency="Area" width="15">
          <fontProperties style="" description="Ubuntu,8,-1,5,1,0,0,0,0,0"/>
          <attribute field="" color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerSettings dist="0" linePlacementFlags="18" zIndex="0" showAll="1" placement="0" obstacle="0" priority="0">
        <properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </properties>
      </DiagramLayerSettings>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="ID">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="INLET">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="RES">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
        <field name="PTSOURCE">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option value="0" type="QString" name="IsMultiline"/>
                <Option value="0" type="QString" name="UseHtml"/>
              </Option>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="ID" index="0" name=""/>
        <alias field="INLET" index="1" name=""/>
        <alias field="RES" index="2" name=""/>
        <alias field="PTSOURCE" index="3" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="ID" applyOnUpdate="0" expression=""/>
        <default field="INLET" applyOnUpdate="0" expression=""/>
        <default field="RES" applyOnUpdate="0" expression=""/>
        <default field="PTSOURCE" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="ID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="INLET" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="RES" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="PTSOURCE" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="ID" exp="" desc=""/>
        <constraint field="INLET" exp="" desc=""/>
        <constraint field="RES" exp="" desc=""/>
        <constraint field="PTSOURCE" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions>
        <defaultAction value--open-curly--00000000-0000-0000-0000-000000000000--close-curly--" key="Canvas"/>
      </attributeactions>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns>
          <column width="-1" hidden="0" type="field" name="PTSOURCE"/>
          <column width="-1" hidden="0" type="field" name="RES"/>
          <column width="-1" hidden="0" type="field" name="INLET"/>
          <column width="-1" hidden="0" type="field" name="ID"/>
          <column width="-1" hidden="1" type="actions"/>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../../../QSWATPlus_Projects/SanJuan/test1</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
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
        <field editable="1" name="ID"/>
        <field editable="1" name="INLET"/>
        <field editable="1" name="PTSOURCE"/>
        <field editable="1" name="RES"/>
      </editable>
      <labelOnTop>
        <field labelOnTop="0" name="ID"/>
        <field labelOnTop="0" name="INLET"/>
        <field labelOnTop="0" name="PTSOURCE"/>
        <field labelOnTop="0" name="RES"/>
      </labelOnTop>
      <widgets/>
      <previewExpression>ID</previewExpression>
      <mapTip></mapTip>
    </maplayer>
    <maplayer hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" refreshOnNotifyEnabled="0" autoRefreshTime="0" minScale="1e+08" refreshOnNotifyMessage="" type="raster" autoRefreshEnabled="0" maxScale="0">
      <extent>
        <xmin>326002.06302211945876479</xmin>
        <ymin>1286032.46381390024907887</ymin>
        <xmax>338138.04992584581486881</xmax>
        <ymax>1293574.11281835869885981</ymax>
      </extent>
      <id>Soils__{soil_name}_tif__2cd25288_d1b5_4e76_83af_39034c9f7ffd</id>
      <datasource>./Watershed/Rasters/Soil/{soil_file_name}</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Soils ({soil_name})</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type></type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider>gdal</provider>
      <noData>
        <noDataList useSrcNoData="1" bandNo="1"/>
      </noData>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <customproperties>
        <property value="Value" key="identify/format"/>
      </customproperties>
      <pipe>
        <rasterrenderer opacity="1" alphaBand="-1" band="1" classificationMin="nan" type="singlebandpseudocolor" classificationMax="nan">
          <minMaxOrigin>
            <limits>None</limits>
            <extent>WholeRaster</extent>
            <statAccuracy>Estimated</statAccuracy>
            <cumulativeCutLower>0.02</cumulativeCutLower>
            <cumulativeCutUpper>0.98</cumulativeCutUpper>
            <stdDevFactor>2</stdDevFactor>
          </minMaxOrigin>
          <rastershader>
            <colorrampshader clip="0" colorRampType="DISCRETE" classificationMode="1">
              <item value="0" color="#089d97" label="LVx" alpha="255"/>
              <item value="178" color="#abd7ed" label="VRe" alpha="255"/>
            </colorrampshader>
          </rastershader>
        </rasterrenderer>
        <brightnesscontrast contrast="0" brightness="0"/>
        <huesaturation colorizeStrength="100" colorizeOn="0" grayscaleMode="0" colorizeGreen="128" saturation="0" colorizeBlue="128" colorizeRed="255"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </maplayer>
    <maplayer geometry="Line" maxScale="0" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="0" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="1" simplifyLocal="1" wkbType="MultiLineString" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328870.8826469536870718</xmin>
        <ymin>1288124.26022111857309937</ymin>
        <xmax>335260.8826469536870718</xmax>
        <ymax>1291454.26022111857309937</ymax>
      </extent>
      <id>Streams__{dem_name}stream__6a837462_9d7d_48f0_a6c1_1710f553d03b</id>
      <datasource>./Watershed/Shapes/{dem_name}stream.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Streams ({dem_name}stream)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="singleSymbol">
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="line" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleLine">
              <prop k="capstyle" v="square"/>
              <prop k="customdash" v="5;2"/>
              <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="customdash_unit" v="MM"/>
              <prop k="draw_inside_polygon" v="0"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="line_color" v="0,85,255,255"/>
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
        <rotation/>
        <sizescale/>
      </renderer-v2>
      <customproperties/>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="LINKNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DSLINKNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="USLINKNO1">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="USLINKNO2">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DSNODEID">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Order">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Length">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Magnitude">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DS_Cont_Ar">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Drop">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Slope">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Straight_L">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="US_Cont_Ar">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="WSNO">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DOUT_END">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DOUT_START">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="DOUT_MID">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="LINKNO" index="0" name=""/>
        <alias field="DSLINKNO" index="1" name=""/>
        <alias field="USLINKNO1" index="2" name=""/>
        <alias field="USLINKNO2" index="3" name=""/>
        <alias field="DSNODEID" index="4" name=""/>
        <alias field="Order" index="5" name=""/>
        <alias field="Length" index="6" name=""/>
        <alias field="Magnitude" index="7" name=""/>
        <alias field="DS_Cont_Ar" index="8" name=""/>
        <alias field="Drop" index="9" name=""/>
        <alias field="Slope" index="10" name=""/>
        <alias field="Straight_L" index="11" name=""/>
        <alias field="US_Cont_Ar" index="12" name=""/>
        <alias field="WSNO" index="13" name=""/>
        <alias field="DOUT_END" index="14" name=""/>
        <alias field="DOUT_START" index="15" name=""/>
        <alias field="DOUT_MID" index="16" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="LINKNO" applyOnUpdate="0" expression=""/>
        <default field="DSLINKNO" applyOnUpdate="0" expression=""/>
        <default field="USLINKNO1" applyOnUpdate="0" expression=""/>
        <default field="USLINKNO2" applyOnUpdate="0" expression=""/>
        <default field="DSNODEID" applyOnUpdate="0" expression=""/>
        <default field="Order" applyOnUpdate="0" expression=""/>
        <default field="Length" applyOnUpdate="0" expression=""/>
        <default field="Magnitude" applyOnUpdate="0" expression=""/>
        <default field="DS_Cont_Ar" applyOnUpdate="0" expression=""/>
        <default field="Drop" applyOnUpdate="0" expression=""/>
        <default field="Slope" applyOnUpdate="0" expression=""/>
        <default field="Straight_L" applyOnUpdate="0" expression=""/>
        <default field="US_Cont_Ar" applyOnUpdate="0" expression=""/>
        <default field="WSNO" applyOnUpdate="0" expression=""/>
        <default field="DOUT_END" applyOnUpdate="0" expression=""/>
        <default field="DOUT_START" applyOnUpdate="0" expression=""/>
        <default field="DOUT_MID" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="LINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DSLINKNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="USLINKNO1" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="USLINKNO2" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DSNODEID" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Order" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Length" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Magnitude" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DS_Cont_Ar" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Drop" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Slope" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Straight_L" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="US_Cont_Ar" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="WSNO" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DOUT_END" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DOUT_START" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="DOUT_MID" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="LINKNO" exp="" desc=""/>
        <constraint field="DSLINKNO" exp="" desc=""/>
        <constraint field="USLINKNO1" exp="" desc=""/>
        <constraint field="USLINKNO2" exp="" desc=""/>
        <constraint field="DSNODEID" exp="" desc=""/>
        <constraint field="Order" exp="" desc=""/>
        <constraint field="Length" exp="" desc=""/>
        <constraint field="Magnitude" exp="" desc=""/>
        <constraint field="DS_Cont_Ar" exp="" desc=""/>
        <constraint field="Drop" exp="" desc=""/>
        <constraint field="Slope" exp="" desc=""/>
        <constraint field="Straight_L" exp="" desc=""/>
        <constraint field="US_Cont_Ar" exp="" desc=""/>
        <constraint field="WSNO" exp="" desc=""/>
        <constraint field="DOUT_END" exp="" desc=""/>
        <constraint field="DOUT_START" exp="" desc=""/>
        <constraint field="DOUT_MID" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions/>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns/>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../Documents</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
      <editforminitcode><![CDATA[]]></editforminitcode>
      <featformsuppress>0</featformsuppress>
      <editorlayout>generatedlayout</editorlayout>
      <editable/>
      <labelOnTop/>
      <widgets/>
      <previewExpression></previewExpression>
      <mapTip>ID</mapTip>
    </maplayer>
    <maplayer geometry="Polygon" maxScale="-4.65661e-10" refreshOnNotifyEnabled="0" type="vector" styleCategories="AllStyleCategories" simplifyDrawingHints="1" simplifyMaxScale="1" autoRefreshEnabled="0" labelsEnabled="1" simplifyLocal="1" wkbType="MultiPolygon" minScale="1e+08" simplifyDrawingTol="1" refreshOnNotifyMessage="" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" autoRefreshTime="0">
      <extent>
        <xmin>328825.8826469536870718</xmin>
        <ymin>1287329.26022111857309937</ymin>
        <xmax>336355.8826469536870718</xmax>
        <ymax>1292189.26022111857309937</ymax>
      </extent>
      <id>Subbasins__subs1__3017a81e_0174_439c_b815_cf54de0e0667</id>
      <datasource>./Watershed/Shapes/subs1.shp</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>Subbasins (subs1)</layername>
      <srs>
        <spatialrefsys>
           <wkt>{prjcrs}</wkt>
          <proj4>{proj4}</proj4>
          <srsid>{srsid}</srsid>
          <srid>{srid}</srid>
          <authid>EPSG:{srid}</authid>
          <description>{srs_description}</description>
          <projectionacronym>{projectionacronym}</projectionacronym>
          <ellipsoidacronym>{ellipsoidacronym}</ellipsoidacronym>
          <geographicflag>{geographicflag}</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt></wkt>
            <proj4></proj4>
            <srsid>0</srsid>
            <srid>0</srid>
            <authid></authid>
            <description></description>
            <projectionacronym></projectionacronym>
            <ellipsoidacronym></ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="UTF-8">ogr</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
      <flags>
        <Identifiable>1</Identifiable>
        <Removable>1</Removable>
        <Searchable>1</Searchable>
      </flags>
      <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="RuleRenderer">
        <rules key--open-curly--192bdd02-ed6d-4f65-842d-a83746e86517--close-curly--">
          <rule key--open-curly--4b960711-df1e-4d23-bc17-d5ffaae25809--close-curly--" label="SWAT subbasin" description="Included in SWAT model" symbol="0" filter="&quot;Subbasin&quot;  IS NULL OR &quot;Subbasin&quot;  > 0 "/>
          <rule key--open-curly--96ec9113-62fe-4bba-a4e0-917d85ec2586--close-curly--" label="Upstream from inlet" description="Excluded from SWAT model" symbol="1" filter="&quot;Subbasin&quot;  =  0"/>
        </rules>
        <symbols>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="fill" name="0">
            <layer pass="0" locked="0" enabled="1" class="SimpleFill">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="32,37,161,255"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="255,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.26"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="style" v="no"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol clip_to_extent="1" force_rhr="0" alpha="1" type="fill" name="1">
            <layer pass="0" locked="0" enabled="1" class="SimpleFill">
              <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="255,255,255,255"/>
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
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </symbols>
      </renderer-v2>
      <labeling type="simple">
        <settings calloutType="simple">
          <text-style fontUnderline="0" blendMode="0" isExpression="1" fontStrikeout="0" textOrientation="horizontal" fontLetterSpacing="0" fieldName="CASE WHEN &quot;Subbasin&quot; = 0 THEN '' ELSE &quot;Subbasin&quot; END" useSubstitutions="0" fontItalic="0" fontSize="8.25" fontWeight="50" fontCapitals="0" previewBkgrdColor="255,255,255,255" textOpacity="1" fontKerning="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontFamily="MS Shell Dlg 2" fontWordSpacing="0" textColor="0,0,0,255" namedStyle="Normal" multilineHeight="1" fontSizeUnit="Point">
            <text-buffer bufferBlendMode="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSizeUnits="MM" bufferColor="255,255,255,255" bufferNoFill="0" bufferJoinStyle="64" bufferSize="1" bufferOpacity="1" bufferDraw="0"/>
            <background shapeType="0" shapeRotation="0" shapeSizeY="0" shapeRadiiY="0" shapeFillColor="255,255,255,255" shapeOpacity="1" shapeOffsetX="0" shapeRotationType="0" shapeBorderColor="128,128,128,255" shapeBlendMode="0" shapeRadiiUnit="MM" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeSizeX="0" shapeBorderWidthUnit="MM" shapeRadiiX="0" shapeDraw="0" shapeOffsetY="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeUnit="MM" shapeBorderWidth="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSizeType="0" shapeOffsetUnit="MM"/>
            <shadow shadowOffsetGlobal="1" shadowDraw="0" shadowOffsetAngle="135" shadowOffsetUnit="MM" shadowColor="0,0,0,255" shadowRadiusUnit="MM" shadowBlendMode="6" shadowUnder="0" shadowRadiusAlphaOnly="0" shadowOpacity="0.7" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowRadius="1.5" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100"/>
            <dd_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </dd_properties>
            <substitutions/>
          </text-style>
          <text-format plussign="0" useMaxLineLengthForAutoWrap="1" placeDirectionSymbol="0" decimals="3" leftDirectionSymbol="&lt;" multilineAlign="0" addDirectionSymbol="0" rightDirectionSymbol=">" reverseDirectionSymbol="0" autoWrapLength="0" wrapChar="" formatNumbers="0"/>
          <placement yOffset="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" distUnits="MM" overrunDistance="0" repeatDistance="0" geometryGenerator="" xOffset="0" maxCurvedCharAngleOut="-20" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" layerType="UnknownGeometry" placementFlags="0" placement="1" priority="5" dist="0" fitInPolygonOnly="0" geometryGeneratorType="PointGeometry" preserveRotation="1" distMapUnitScale="3x:0,0,0,0,0,0" centroidInside="1" quadOffset="4" offsetUnits="MapUnit" repeatDistanceUnits="MM" rotationAngle="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" overrunDistanceUnit="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" centroidWhole="1" maxCurvedCharAngleIn="20" offsetType="0" geometryGeneratorEnabled="0"/>
          <rendering fontMinPixelSize="3" limitNumLabels="0" scaleVisibility="0" displayAll="0" drawLabels="1" scaleMin="1" fontMaxPixelSize="10000" mergeLines="0" obstacleType="0" zIndex="0" scaleMax="10000000" labelPerPart="0" obstacleFactor="1" fontLimitPixelSize="0" maxNumLabels="2000" obstacle="1" upsidedownLabels="0" minFeatureSize="0"/>
          <dd_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </dd_properties>
          <callout type="simple">
            <Option type="Map">
              <Option value="pole_of_inaccessibility" type="QString" name="anchorPoint"/>
              <Option type="Map" name="ddProperties">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
              <Option value="false" type="bool" name="drawToAllParts"/>
              <Option value="0" type="QString" name="enabled"/>
              <Option value="&lt;symbol clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot; alpha=&quot;1&quot; type=&quot;line&quot; name=&quot;symbol&quot;>&lt;layer pass=&quot;0&quot; locked=&quot;0&quot; enabled=&quot;1&quot; class=&quot;SimpleLine&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; type=&quot;QString&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; type=&quot;QString&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString" name="lineSymbol"/>
              <Option value="0" type="double" name="minLength"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="minLengthMapUnitScale"/>
              <Option value="MM" type="QString" name="minLengthUnit"/>
              <Option value="0" type="double" name="offsetFromAnchor"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromAnchorMapUnitScale"/>
              <Option value="MM" type="QString" name="offsetFromAnchorUnit"/>
              <Option value="0" type="double" name="offsetFromLabel"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromLabelMapUnitScale"/>
              <Option value="MM" type="QString" name="offsetFromLabelUnit"/>
            </Option>
          </callout>
        </settings>
      </labeling>
      <customproperties/>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
        <activeChecks/>
        <checkConfiguration/>
      </geometryOptions>
      <fieldConfiguration>
        <field name="PolygonId">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Subbasin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Area">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Slo1">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Len1">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Sll">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Lat">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Lon">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="Elev">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="ElevMin">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
        <field name="ElevMax">
          <editWidget type="">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
      </fieldConfiguration>
      <aliases>
        <alias field="PolygonId" index="0" name=""/>
        <alias field="Subbasin" index="1" name=""/>
        <alias field="Area" index="2" name=""/>
        <alias field="Slo1" index="3" name=""/>
        <alias field="Len1" index="4" name=""/>
        <alias field="Sll" index="5" name=""/>
        <alias field="Lat" index="6" name=""/>
        <alias field="Lon" index="7" name=""/>
        <alias field="Elev" index="8" name=""/>
        <alias field="ElevMin" index="9" name=""/>
        <alias field="ElevMax" index="10" name=""/>
      </aliases>
      <excludeAttributesWMS/>
      <excludeAttributesWFS/>
      <defaults>
        <default field="PolygonId" applyOnUpdate="0" expression=""/>
        <default field="Subbasin" applyOnUpdate="0" expression=""/>
        <default field="Area" applyOnUpdate="0" expression=""/>
        <default field="Slo1" applyOnUpdate="0" expression=""/>
        <default field="Len1" applyOnUpdate="0" expression=""/>
        <default field="Sll" applyOnUpdate="0" expression=""/>
        <default field="Lat" applyOnUpdate="0" expression=""/>
        <default field="Lon" applyOnUpdate="0" expression=""/>
        <default field="Elev" applyOnUpdate="0" expression=""/>
        <default field="ElevMin" applyOnUpdate="0" expression=""/>
        <default field="ElevMax" applyOnUpdate="0" expression=""/>
      </defaults>
      <constraints>
        <constraint exp_strength="0" field="PolygonId" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Subbasin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Area" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Slo1" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Len1" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Sll" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Lat" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Lon" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="Elev" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="ElevMin" unique_strength="0" notnull_strength="0" constraints="0"/>
        <constraint exp_strength="0" field="ElevMax" unique_strength="0" notnull_strength="0" constraints="0"/>
      </constraints>
      <constraintExpressions>
        <constraint field="PolygonId" exp="" desc=""/>
        <constraint field="Subbasin" exp="" desc=""/>
        <constraint field="Area" exp="" desc=""/>
        <constraint field="Slo1" exp="" desc=""/>
        <constraint field="Len1" exp="" desc=""/>
        <constraint field="Sll" exp="" desc=""/>
        <constraint field="Lat" exp="" desc=""/>
        <constraint field="Lon" exp="" desc=""/>
        <constraint field="Elev" exp="" desc=""/>
        <constraint field="ElevMin" exp="" desc=""/>
        <constraint field="ElevMax" exp="" desc=""/>
      </constraintExpressions>
      <expressionfields/>
      <attributeactions/>
      <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
        <columns/>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">../../../Documents</editform>
      <editforminit/>
      <editforminitcodesource>0</editforminitcodesource>
      <editforminitfilepath></editforminitfilepath>
      <editforminitcode><![CDATA[]]></editforminitcode>
      <featformsuppress>0</featformsuppress>
      <editorlayout>generatedlayout</editorlayout>
      <editable/>
      <labelOnTop/>
      <widgets/>
      <previewExpression>"PolygonId"</previewExpression>
      <mapTip></mapTip>
    </maplayer>
  </projectlayers>
  <layerorder>
    <layer id="DEM__{dem_name}__f751ab49_fdac_4766_be7f_300fbfe6adf2"/>
    <layer id="Hillshade__{dem_name}hillshade__a6f33483_65e8_4cde_a966_948ff13f0c2a"/>
    <layer id="Inlets_outlets__{outlet_name}__0c49465a_2a2b_4ecb_ae4f_fbb60c4c1bcb"/>
    <layer id="Drawn_inlets_outlets__{outlet_name}__c41cb90c_f1d6_4ffe_8a64_99bcb575d961"/>
    <layer id="Landuses__{landuse_name}__f7ec5ca9_3dce_4d3e_8def_9e31ecc6c163"/>
    <layer id="Soils__{soil_name}_tif__2cd25288_d1b5_4e76_83af_39034c9f7ffd"/>
    <layer id="Snapped_inlets_outlets__{outlet_name}_snap__2a54eb19_3da0_420d_b964_e4cd8efd371f"/>
    <layer id="Streams__{dem_name}stream__6a837462_9d7d_48f0_a6c1_1710f553d03b"/>
    <layer id="Channels__{dem_name}channel__a7e3608c_b71d_44f6_8194_67e56bb7c543"/>
    <layer id="Full_LSUs__lsus1__8f4e9cfb_3ca6_4a70_83b9_fe977379bcf4"/>
    <layer id="Full_HRUs__hrus1__4e2ba365_e7bd_4f8e_9d6c_79056945afb5"/>
    <layer id="Slope_bands__{dem_name}slp_bands__daa1ee9a_d352_4de4_a12e_21aa0143f677"/>
    <layer id="Pt_sources_and_reservoirs__reservoirs2__ada5d781_850f_43ac_825b_b807e28299e4"/>
    <layer id="Channel_reaches__rivs1__514d2d76_3dcd_4834_8bd4_42392284ab2f"/>
    <layer id="Actual_HRUs__hrus2__7adc36e1_3c7f_40db_8b2c_bb4f79fa3338"/>
    <layer id="Subbasins__subs1__3017a81e_0174_439c_b815_cf54de0e0667"/>
  </layerorder>
  <properties>
    <Gui>
      <CanvasColorBluePart type="int">255</CanvasColorBluePart>
      <CanvasColorGreenPart type="int">255</CanvasColorGreenPart>
      <CanvasColorRedPart type="int">255</CanvasColorRedPart>
      <SelectionColorAlphaPart type="int">255</SelectionColorAlphaPart>
      <SelectionColorBluePart type="int">0</SelectionColorBluePart>
      <SelectionColorGreenPart type="int">255</SelectionColorGreenPart>
      <SelectionColorRedPart type="int">255</SelectionColorRedPart>
    </Gui>
    <Legend>
      <filterByMap type="bool">false</filterByMap>
    </Legend>
    <Measure>
      <Ellipsoid type="QString">{ellipsoidacronym}</Ellipsoid>
    </Measure>
    <Measurement>
      <AreaUnits type="QString">m2</AreaUnits>
      <DistanceUnits type="QString">meters</DistanceUnits>
    </Measurement>
    <PAL>
      <CandidatesLine type="int">50</CandidatesLine>
      <CandidatesPoint type="int">16</CandidatesPoint>
      <CandidatesPolygon type="int">30</CandidatesPolygon>
      <DrawRectOnly type="bool">false</DrawRectOnly>
      <DrawUnplaced type="bool">false</DrawUnplaced>
      <SearchMethod type="int">0</SearchMethod>
      <ShowingAllLabels type="bool">false</ShowingAllLabels>
      <ShowingCandidates type="bool">false</ShowingCandidates>
      <ShowingPartialsLabels type="bool">true</ShowingPartialsLabels>
      <TextFormat type="int">0</TextFormat>
      <UnplacedColor type="QString">255,0,0,255</UnplacedColor>
    </PAL>
    <Paths>
      <Absolute type="bool">false</Absolute>
    </Paths>
    <PositionPrecision>
      <Automatic type="bool">true</Automatic>
      <DecimalPlaces type="int">2</DecimalPlaces>
    </PositionPrecision>
    <SpatialRefSys>
      <ProjectionsEnabled type="int">1</ProjectionsEnabled>
    </SpatialRefSys>
    <{project_name}>
      <delin>
        <DEM type="QString">./Watershed/Rasters/DEM/{dem_file_name}</DEM>
        <burn type="QString"></burn>
        <channels type="QString">./Watershed/Shapes/{dem_name}channel.shp</channels>
        <delinNet type="QString">./Watershed/Shapes/{dem_name}stream.shp</delinNet>
        <drainageTable type="QString"></drainageTable>
        <existingWshed type="int">0</existingWshed>
        <extraOutlets type="QString"></extraOutlets>
        <gridDrainage type="int">0</gridDrainage>
        <gridSize type="int">0</gridSize>
        <lakePointsAdded type="int">0</lakePointsAdded>
        <lakes type="QString"></lakes>
        <lakesDone type="int">0</lakesDone>
        <net type="QString">./Watershed/Shapes/{dem_name}stream.shp</net>
        <outlets type="QString">./Watershed/Shapes/{outlet_name}.shp</outlets>
        <snapOutlets type="QString">./Watershed/Shapes/{outlet_name}_snap.shp</snapOutlets>
        <snapThreshold type="int">{snap_threshold}</snapThreshold>
        <streamDrainage type="int">1</streamDrainage>
        <subbasins type="QString">./Watershed/Shapes/{dem_name}subbasins.shp</subbasins>
        <thresholdCh type="int">{channel_threshold}</thresholdCh>
        <thresholdSt type="int">{stream_threshold}</thresholdSt>
        <useGridModel type="int">0</useGridModel>
        <useOutlets type="int">1</useOutlets>
        <verticalUnits type="QString">metres</verticalUnits>
        <wshed type="QString">./Watershed/Shapes/{dem_name}wshed.shp</wshed>
      </delin>
      <hru>
        <areaVal type="int">{area_val}</areaVal>
        <elevBandsThreshold type="int">0</elevBandsThreshold>
        <isArea type="int">{is_area}</isArea>
        <isDominantHRU type="int">{is_dominant_hru}</isDominantHRU>
        <isMultiple type="int">{is_multiple}</isMultiple>
        <isTarget type="int">{is_target}</isTarget>
        <landuseVal type="int">{hru_land_thres}</landuseVal>
        <numElevBands type="int">0</numElevBands>
        <slopeBands type="QString">[{slope_classes}]</slopeBands>
        <slopeBandsFile type="QString">./Watershed/Rasters/DEM/{dem_name}slp_bands.tif</slopeBandsFile>
        <slopeVal type="int">{hru_slope_thres}</slopeVal>
        <soilVal type="int">{hru_soil_thres}</soilVal>
        <targetVal type="int">{target_val}</targetVal>
        <useArea type="int">{use_area}</useArea>
      </hru>
      <landuse>
        <file type="QString">./Watershed/Rasters/Landuse/{landuse_file_name}</file>
        <plant type="QString">plant</plant>
        <table type="QString">{land_lookup}</table>
        <urban type="QString">urban</urban>
        <water type="int">1</water>
      </landuse>
      <lsu>
        <channelMergeByPercent type="int">1</channelMergeByPercent>
        <channelMergeVal type="int">0</channelMergeVal>
        <floodplainFile type="QString"></floodplainFile>
        <thresholdResNoFlood type="int">101</thresholdResNoFlood>
        <useLandscapes type="int">0</useLandscapes>
        <useLeftRight type="int">0</useLeftRight>
      </lsu>
      <soil>
        <database type="QString">./{project_name}.sqlite</database>
        <databaseTable type="QString">{usersoil}</databaseTable>
        <file type="QString">./Watershed/Rasters/Soil/{soil_file_name}</file>
        <table type="QString">{soil_lookup}</table>
        <useSSURGO type="int">0</useSSURGO>
        <useSTATSGO type="int">0</useSTATSGO>
      </soil>
    </{project_name}>
  </properties>
  <visibility-presets/>
  <transformContext/>
  <projectMetadata>
    <identifier></identifier>
    <parentidentifier></parentidentifier>
    <language></language>
    <type></type>
    <title>{project_name}</title>
    <abstract></abstract>
    <links/>
    <author>Celray James</author>
    <creation>2020-03-04T15:58:23</creation>
  </projectMetadata>
  <Annotations/>
  <Layouts/>
  <Bookmarks/>
  <ProjectViewSettings UseProjectScales="0">
    <Scales/>
  </ProjectViewSettings>
</qgis>
'''