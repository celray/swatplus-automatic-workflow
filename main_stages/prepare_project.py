'''
date        : 31/03/2020
description : this module creates and populates project directories
              and creates project file

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import os
import pickle
import sys
import zipfile
from glob import glob
from shutil import copyfile, rmtree

import gdal
import osr

sys.path.insert(0, os.path.join(os.environ["swatplus_wf_dir"], "packages"))
sys.path.append(os.path.join(os.environ["swatplus_wf_dir"]))
sys.path.insert(0, sys.argv[1])

from helper_functions import (read_from, write_to, raster_statistics,
    list_files, copy_file, file_name, python_variable, get_extents)
from projection_lookup import epsg_lookup_dictionary
from qgs_project_template import template
from sqlite_tools import sqlite_connection
from logger import log

log = log("{base}/swatplus_aw_log.txt".format(base = sys.argv[1]))
keep_log = True

# check if there is need to prepare project
if os.path.isfile("{base}/namelist.py".format(base=sys.argv[1])):
    import namelist
    if namelist.Keep_Log == True:
        keep_log = True
        log.initialise()
    else:
        keep_log = False
    if namelist.Model_2_namelist == True:
        log.info("namelist creation is required; 'Model_2_namelist' is set to 'True'", keep_log)

        sys.exit(0)
else:
    if namelist.Keep_Log == True:
        keep_log = True
        log.initialise()
    else:
        keep_log = False
    
    log.info("namelist was not found in the current directory", keep_log)
    print("\t! namelist.py not found in current directory")
    sys.exit(0)


class dem_data:
    def __init__(self):
        self.raster_data = None
        self.suffix_list = []

# location of wgn
# https://bitbucket.org/swatplus/swatplus.editor/downloads/swatplus_wgn.sqlite

# announce action
print("\n     >> preparing project")
log.info("preparing the qgis project", keep_log)

# set importane variables
project_name = namelist.Project_Name
outlet_name = namelist.Outlets.split(".")[0]
soil_lookup = namelist.Soil_Lookup.split(".")[0]
land_lookup = namelist.Landuse_Lookup.split(".")[0]
usersoil = namelist.Usersoil.split(".")[0]
thresholdCh = namelist.Channel_Threshold
thresholdSt = namelist.Stream_Threshold
burn_name = namelist.Burn_In_Shape

dem_name = namelist.Topography if ".tif" in namelist.Topography.lower(
) else "{dem}.tif".format(dem=namelist.Topography)
landuse_name = namelist.Land_Use if ".tif" in namelist.Land_Use.lower(
) else "{land}.tif".format(land=namelist.Land_Use)
soil_name = namelist.Soils if ".tif" in namelist.Soils.lower(
) else "{soil}.tif".format(soil=namelist.Soils)

extension_suffix = ".tif"

# prepare rasters
log.info("preparing raster files", keep_log)
dem_fn = "{base_dir}/data/rasters/{dem_file}".format(
    base_dir=sys.argv[1], dem_file=namelist.Topography)
log.info(" - dem file: {0}".format(namelist.Topography), keep_log)
soil_fn = "{base_dir}/data/rasters/{dem_file}".format(
    base_dir=sys.argv[1], dem_file=namelist.Soils)
log.info(" - soils file: {0}".format(namelist.Soils), keep_log)
landuse_fn = "{base_dir}/data/rasters/{dem_file}".format(
    base_dir=sys.argv[1], dem_file=namelist.Land_Use)
log.info(" - soils file: {0}".format(namelist.Land_Use), keep_log)


dem_dirname = '{base}/{project_name}/Watershed/Rasters/DEM/'.format(
    base=sys.argv[1], project_name=project_name)
soil_dirname = '{base}/{project_name}/Watershed/Rasters/Landuse/'.format(
    base=sys.argv[1], project_name=project_name)
landuse_dirname = '{base}/{project_name}/Watershed/Rasters/Soil/'.format(
    base=sys.argv[1], project_name=project_name)

log.info("creating raster directories in project", keep_log)
if not os.path.isdir(dem_dirname):
    os.makedirs(dem_dirname)

if not os.path.isdir(soil_dirname):
    os.makedirs(soil_dirname)

if not os.path.isdir(landuse_dirname):
    os.makedirs(landuse_dirname)

# prjcrs_tmp = "{base}/data/rasters/prjcrs.crs".format(base=sys.argv[1])
# prjcrs_formated_tmp = "{base}/data/rasters/prjcrs_formated.crs".format(base=sys.argv[1])
#
# if os.path.isfile(prjcrs_tmp):
#     os.remove(prjcrs_tmp)

# copy and convert rasters
log.info("extracting DEM to {0}".format(
    '{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}'.format(
        base=sys.argv[1], project_name=project_name, dem_name=dem_name)
), keep_log)
if namelist.Topography.lower().endswith(".tif"):
    copy_file(dem_fn, '{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}'.format(
        base=sys.argv[1], project_name=project_name, dem_name=dem_name))
    copy_file(dem_fn, '{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}slp_bands.tif'.format(
        base=sys.argv[1], project_name=project_name, dem_name=dem_name[:-4]))
else:
    src_ds = gdal.Open(dem_fn)
    ds = gdal.Translate('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}'.format(
        base=sys.argv[1], project_name=project_name, dem_name=dem_name), src_ds, format='GTiff')
    ds = gdal.Translate('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}slp_bands.tif'.format(
        base=sys.argv[1], project_name=project_name, dem_name=dem_name[:-4]), src_ds, format='GTiff')

log.info("extracting DEM to {0}".format(
    '{base}/{project_name}/Watershed/Rasters/Landuse/{landuse_name}'.format(
        base=sys.argv[1], project_name=project_name, landuse_name=landuse_name)
), keep_log)
if namelist.Land_Use.lower().endswith(".tif"):
    copy_file(landuse_fn, '{base}/{project_name}/Watershed/Rasters/Landuse/{landuse_name}'.format(
        base=sys.argv[1], project_name=project_name, landuse_name=landuse_name))
else:
    src_ds = gdal.Open(landuse_fn)
    ds = gdal.Translate('{base}/{project_name}/Watershed/Rasters/Landuse/{landuse_name}'.format(
        base=sys.argv[1], project_name=project_name, landuse_name=landuse_name), src_ds, format='GTiff')

log.info("extracting DEM to {0}".format(
    '{base}/{project_name}/Watershed/Rasters/Soil/{soil_name}'.format(
        base=sys.argv[1], project_name=project_name, soil_name=soil_name)
), keep_log)
if namelist.Soils.lower().endswith(".tif"):
    copy_file(soil_fn, '{base}/{project_name}/Watershed/Rasters/Soil/{soil_name}'.format(
        base=sys.argv[1], project_name=project_name, soil_name=soil_name))
else:
    src_ds = gdal.Open(soil_fn)
    ds = gdal.Translate('{base}/{project_name}/Watershed/Rasters/Soil/{soil_name}'.format(
        base=sys.argv[1], project_name=project_name, soil_name=soil_name), src_ds, format='GTiff')

log.info("getting dem projection information", keep_log)
dataset = gdal.Open('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}'.format(
    base=sys.argv[1], project_name=project_name, dem_name=dem_name))

formated_projcs = gdal.Info(dataset).split("Data axis")[
    0].split("System is:\n")[-1]

prjcrs = ""
for line in formated_projcs.split("\n"):
    while line.startswith(" "):
        line = line[1:]
    prjcrs += line.strip("\n")

srs = osr.SpatialReference(wkt=prjcrs)

proj4 = srs.ExportToProj4()
geogcs = srs.GetAttrValue('geogcs')
log.info("geogcs: {0}".format(geogcs), keep_log)
log.info("proj4: {0}".format(proj4), keep_log)

if prjcrs.split('"')[1] in epsg_lookup_dictionary:
    srid, projectionacronym, srsid, ellipsoidacronym = epsg_lookup_dictionary[prjcrs.split('"')[
        1]]
    geographicflag = "false"
else:
    srid, projectionacronym, srsid, ellipsoidacronym = "", "", "", ""
    geographicflag = "true"
    log.error("DEM is not projected", keep_log)
    print("Error! DEM is not projected!")
    sys.exit(1)

srs_description = prjcrs.split('"')[1]


# hru settings
log.info("setting hru filter method", keep_log)
hru_land_thres, hru_soil_thres, hru_slope_thres = "", "", ""
area_val = 0      # value for area if option 3 for HRU Filter Method is selected
target_val = 0    # value for area if option 4 for HRU Filter Method is selected
is_area = 0
use_area = 1 if namelist.HRU_Thresholds_Type == 1 else 0
is_dominant_hru = 0
is_multiple = 0
is_target = 0

if namelist.HRU_Filter_Method == 1:
    log.info("> filter method is dominant landuse, soil, slope", keep_log)
    is_dominant_hru = 1

if namelist.HRU_Filter_Method == 2:
    log.info("> filter method is dominant hrus", keep_log)
    is_dominant_hru = 1

if namelist.HRU_Filter_Method == 3:
    log.info("> filter method is target area", keep_log)
    area_val = namelist.Target_Area
    log.info("  - target area = {0}".format(area_val), keep_log)
    is_multiple = 1
    is_area = 1

if namelist.HRU_Filter_Method == 4:
    log.info("> filter method is target area", keep_log)
    target_val = namelist.Target_Value
    log.info("  - target value = {0}".format(target_val), keep_log)
    is_multiple = 1
    is_target = 1

if namelist.HRU_Filter_Method == 5:
    log.info("> filter method is filter by landuse, soil, slope", keep_log)
    log.info("  - thresholds = {0}".format(namelist.Land_Soil_Slope_Thres), keep_log)
    if len(namelist.Land_Soil_Slope_Thres.split(",")) != 3:
        print('\t! Provide thresholds in the namelist with the correct format\n\t - e.g. Land_Soil_Slope_Thres = "12, 10, 7"')
        sys.exit(1)
    else:
        hru_land_thres, hru_soil_thres, hru_slope_thres = namelist.Land_Soil_Slope_Thres.replace(
            " ", "").split(",")
        is_multiple = 1

log.info("writing raster projection information", keep_log)
write_to('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}.prj.txt'.format(
    base=sys.argv[1], project_name=project_name, dem_name=dem_name), formated_projcs)
write_to('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}.prj'.format(
    base=sys.argv[1], project_name=project_name, dem_name=dem_name), prjcrs)
write_to('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}hillshade.prj'.format(
    base=sys.argv[1], project_name=project_name, dem_name=dem_name), prjcrs)

log.info("getting gis data extents", keep_log)
extent_xmin, extent_ymin, extent_xmax, extent_ymax = get_extents(dem_fn)
raster_stats = raster_statistics(dem_fn)
third_delta = round((raster_stats.maximum - raster_stats.minimum)/3, 0)

lower_third = raster_stats.minimum + third_delta
upper_third = raster_stats.maximum - third_delta

project_string = template.format(
    # dem_raster=dem_name,
    prjcrs=prjcrs,
    shape_wkt=prjcrs,
    proj4=proj4,
    geogcs=geogcs,
    project_name=project_name,

    snap_threshold=namelist.Out_Snap_Threshold,
    channel_threshold=namelist.Channel_Threshold,
    stream_threshold=namelist.Stream_Threshold,

    hru_land_thres=hru_land_thres,
    hru_slope_thres=hru_slope_thres,
    hru_soil_thres=hru_soil_thres,

    area_val=area_val,
    target_val=target_val,
    is_area=is_area,
    use_area=use_area,
    is_dominant_hru=is_dominant_hru,
    is_multiple=is_multiple,
    is_target=is_target,

    outlet_name=outlet_name,

    dem_min=raster_stats.minimum,
    dem_max=raster_stats.maximum,
    lower_third=lower_third,
    upper_third=upper_third,
    mid_thirds=round((upper_third + lower_third)/2, 0),

    dem_name=dem_name[:-4],
    landuse_name=landuse_name[:-4],
    extension_suffix=extension_suffix,
    soil_name=soil_name[:-4],
    extent_xmin=extent_xmin,
    soil_lookup=soil_lookup,
    land_lookup=land_lookup,
    extent_ymin=extent_ymin,
    extent_xmax=extent_xmax,
    extent_ymax=extent_ymax,
    thresholdCh=thresholdCh,
    thresholdSt=thresholdSt,
    usersoil=usersoil,
    slope_classes=namelist.Slope_Classes,
    srsid=srsid,
    srid=srid,
    srs_description=srs_description,
    projectionacronym=projectionacronym,
    ellipsoidacronym=ellipsoidacronym,
    geographicflag=geographicflag,
)

project_string = project_string.replace("--close-curly--", "}")
project_string = project_string.replace("key--open-curly--", 'key="{')
project_string = project_string.replace("value--open-curly--", 'value="{')

log.info("writing qgis project file to {0}.qgs".format(
    "{base}/{project_name}/{project_name}.qgs".format(
    base=sys.argv[1], project_name=project_name)
), keep_log)
write_to("{base}/{project_name}/{project_name}.qgs".format(
    base=sys.argv[1], project_name=project_name), project_string)

# dem_data_variable = python_variable(
#     "{qswatplus_wf_dir}/dem_data.dat".format(qswatplus_wf_dir=os.environ["qswatplus_wf"]))

# for suff in dem_data_variable.suffix_list:   # suff is the last_part of each raster that is appended to dem
#     if suff == "fel.tif":
#         continue
#     with open('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}{suff}'.format(
#             base=sys.argv[1], project_name=project_name, dem_name=dem_name, suff=suff), 'wb') as fl:
#         fl.write(dem_data_variable.raster_data)

log.info("creating hillshade for DEM", keep_log)
hillshade_name = '{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}hillshade.tif'.format(
    base=sys.argv[1], project_name=project_name, dem_name=dem_name[:-4])
src_ds = gdal.Open('{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}'.format(
    base=sys.argv[1], project_name=project_name, dem_name=dem_name))
ds = gdal.DEMProcessing(hillshade_name, src_ds, 'hillshade', zFactor=45)

# copy shapefile
shapes_dir = '{base}/{project_name}/Watershed/Shapes/'.format(
    base=sys.argv[1], project_name=project_name)
rmtree(shapes_dir, ignore_errors=True)

data_shapes = list_files("{base_dir}/data/shapefiles/".format(
    base_dir=sys.argv[1]))

# place holding shapefiles
log.info("creating placeholder shapefiles", keep_log)
if not os.path.isdir(shapes_dir):
    os.makedirs(shapes_dir)
with zipfile.ZipFile("{qswatplus_wf_dir}/packages/shapes.dat".format(
        qswatplus_wf_dir=os.environ["swatplus_wf_dir"]), 'r') as zip_ref:
    zip_ref.extractall(shapes_dir)
all_files_shapes = list_files(shapes_dir)
for shp_file in all_files_shapes:
    os.rename(shp_file, shp_file.replace("[dem]", dem_name))

log.info("copying outlet and burn shapefiles", keep_log)
for shape_data in data_shapes:
    if (outlet_name in shape_data) or ((burn_name in shape_data)
        and (not burn_name == "")):
        copy_file(shape_data, "{shapes_dir}/{file_n}".format(
            shapes_dir=shapes_dir, file_n=file_name(shape_data, extension=True)))

# prepare databases
# - copy templates
log.info("getting swatplus_datasets.sqlite", keep_log)
copy_file(
    "{qswatplus_wf_dir}/editor_api/swatplus_datasets.sqlite".format(
        qswatplus_wf_dir=os.environ["swatplus_wf_dir"]),
    '{base}/{project_name}/swatplus_datasets.sqlite'.format(
        base=sys.argv[1], project_name=project_name)
)
log.info("creating {0}.sqlite".format(project_name), keep_log)
copy_file(
    "{qswatplus_wf_dir}/editor_api/template.sqlite".format(
        qswatplus_wf_dir=os.environ["swatplus_wf_dir"]),

    '{base}/{project_name}/{project_name}.sqlite'.format(
        base=sys.argv[1], project_name=project_name)
)

project_database = sqlite_connection(
    '{base}/{project_name}/{project_name}.sqlite'.format(
        base=sys.argv[1], project_name=project_name)
)

# - copy templates
log.info("importing usersoil into project database", keep_log)
project_database.connect()
if project_database.table_exists("{usersoil}".format(usersoil=usersoil)):
    project_database.delete_table("{usersoil}".format(usersoil=usersoil))

# - get_data into database
# - - usersoil
usersoil_rows = read_from("{base_dir}/data/tables/{usersoil_file}".format(
    base_dir=sys.argv[1], usersoil_file=namelist.Usersoil))

column_types_usersoil = {
    "OBJECTID": 'INTEGER',
    "TEXTURE": 'TEXT',
    "HYDGRP": 'TEXT',
    "CMPPCT": 'TEXT',
    "S5ID": 'TEXT',
    "SNAM": 'TEXT',
    "SEQN": 'TEXT',
    "MUID": 'TEXT',
}

project_database.create_table(
    "{usersoil}".format(usersoil=usersoil),
    usersoil_rows[0].replace('"', "").split(",")[0],
    column_types_usersoil[usersoil_rows[0].replace('"', "").split(
        ",")[0].upper()] if usersoil_rows[0].replace('"', "").split(",")[
            0].upper() in column_types_usersoil else 'REAL'
)

for usersoil_row in usersoil_rows:
    if usersoil_row == usersoil_rows[0]:
        for usersoil_column in usersoil_row.replace('"', "").split(",")[1:]:
            project_database.insert_field(
                "{usersoil}".format(usersoil=usersoil),
                usersoil_column.upper(),
                column_types_usersoil[usersoil_column.upper()] if usersoil_column.upper(
                ) in column_types_usersoil else 'REAL'
            )
    else:
        row_insert = usersoil_row.replace('"', "").split(",")
        row_insert = [row_item if not row_item ==
                      "" else None for row_item in row_insert]
        project_database.insert_rows("{usersoil}".format(
            usersoil=usersoil), [row_insert], messages=False)
print("")

# - - soil lookup
log.info("importing soil lookup into project database", keep_log)
soillookup_rows = read_from("{base_dir}/data/tables/{soil_lookup}".format(
    base_dir=sys.argv[1], soil_lookup=namelist.Soil_Lookup))

if project_database.table_exists(soil_lookup):
    project_database.delete_table(soil_lookup)

project_database.create_table(
    "{soil_lookup}".format(soil_lookup=soil_lookup),
    "SOIL_ID",
    "INTEGER"
)

project_database.insert_field(
    "{soil_lookup}".format(soil_lookup=soil_lookup),
    "SNAM",
    "TEXT"
)
print("")

for line in soillookup_rows[1:]:
    project_database.insert_rows("{soil_lookup}".format(
        soil_lookup=soil_lookup), [line.split(",")], messages=False)

# - - landuse lookup
log.info("importing landuse lookup into project database", keep_log)
landuselookup_rows = read_from("{base_dir}/data/tables/{landuse_file}".format(
    base_dir=sys.argv[1], landuse_file=namelist.Landuse_Lookup))

project_database.create_table(
    "{land_lookup}".format(land_lookup=land_lookup),
    "LANDUSE_ID",
    "INTEGER")
project_database.insert_field(
    "{land_lookup}".format(land_lookup=land_lookup),
    "SWAT_CODE",
    "TEXT")

print("")

for line in landuselookup_rows[1:]:
    line = line.strip(" ").strip("\n")
    project_database.insert_rows("{land_lookup}".format(
        land_lookup=land_lookup), [line.split(",")], messages=False)

project_database.close_connection()
log.info("project has been prepared\n", keep_log)
