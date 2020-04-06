'''
date        : 05/04/2020
description : this module creates figures specified in namelist

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import shutil
import os
import sys

sys.path.insert(0, os.path.join(os.environ["swatplus_wf_dir"], "packages"))
sys.path.insert(0, sys.argv[1])

import geopandas
import namelist
from logger import log
from helper_functions import read_from, clear_directory, rasterise, show_progress


class wb_result:
    def __init__(self, wb_parts):
        self.unit = wb_parts[4]
        self.precip = wb_parts[7]
        self.surq_gen = wb_parts[10]
        self.latq = wb_parts[11]
        self.wateryld = wb_parts[12]
        self.perc = wb_parts[13]
        self.et = wb_parts[14]
        self.cn = wb_parts[19]
        self.pet = wb_parts[23]


if namelist.Model_2_namelist:
    sys.exit(0)

base = sys.argv[1].replace("\\\\", "/")
base = base.replace("\\", "/")

log = log("{base}/swatplus_aw_log.txt".format(base=base))

keep_log = False
if namelist.Keep_Log:
        keep_log = True

log.info("preparing to create figures", keep_log)
print("\n\n     >> preparing to create figures")

# check available shapefiles
## set variables
lsus_shapefile = "{base}/{model_name}/Watershed/Shapes/lsus2.shp".format(
    base=base, model_name=namelist.Project_Name)
hrus_shapefile = "{base}/{model_name}/Watershed/Shapes/hrus2.shp".format(
    base=base, model_name=namelist.Project_Name)
aa_lsu_wb_file = "{base}/{model_name}/Scenarios/Default/TxtInOut/lsunit_wb_aa.txt".format(
    base=base, model_name=namelist.Project_Name)
yr_lsu_wb_file = "{base}/{model_name}/Scenarios/Default/TxtInOut/lsunit_wb_yr.txt".format(
    base=base, model_name=namelist.Project_Name)


# lsunit
print("\t-> looking for LSUs shapefile")
log.info("looking for LSUs shapefile", keep_log)
if os.path.isfile(lsus_shapefile):
    print("\t-> LSUs shapefile has been found")
    log.info(" - LSUs shapefile has been found", keep_log)
    if os.path.isfile(aa_lsu_wb_file):
        print("\t-> creating annual average maps at LSU level")
        log.info("creating annual average maps at LSU level", keep_log)
        # read shapefile
        log.info("reading lsu shapefile", keep_log)

        lsu_shapefile_gpd = geopandas.read_file(lsus_shapefile)
        new_lsu_shapefile_gpd = lsu_shapefile_gpd

        new_lsu_shapefile_gpd["precip"] = 0.0
        new_lsu_shapefile_gpd["surq_gen"] = 0.0
        new_lsu_shapefile_gpd["latq"] = 0.0
        new_lsu_shapefile_gpd["wateryld"] = 0.0
        new_lsu_shapefile_gpd["perc"] = 0.0
        new_lsu_shapefile_gpd["et"] = 0.0
        new_lsu_shapefile_gpd["cn"] = 0.0
        new_lsu_shapefile_gpd["pet"] = 0.0

        # read output data into dictionary
        log.info("reading annual average LSU results", keep_log)
        wb_aa_data_list = read_from(aa_lsu_wb_file)
        wb_aa_data_dict = {}
        for wb_aa_line in wb_aa_data_list[3:]:
            wb_aa_line_parts = wb_aa_line.split()
            lsu_no = wb_aa_line_parts[4]
            if not lsu_no in wb_aa_data_dict:
                wb_aa_data_dict[lsu_no] = wb_result(wb_aa_line_parts)

        # add output to shapefile
        log.info("mapping annual average LSU results", keep_log)
        for index, row in lsu_shapefile_gpd.iterrows():
            new_lsu_shapefile_gpd.loc[index, "precip"] = float(
                wb_aa_data_dict[str(row.Channel)].precip)
            new_lsu_shapefile_gpd.loc[index, "surq_gen"] = float(
                wb_aa_data_dict[str(row.Channel)].surq_gen)
            new_lsu_shapefile_gpd.loc[index, "latq"] = float(
                wb_aa_data_dict[str(row.Channel)].latq)
            new_lsu_shapefile_gpd.loc[index, "wateryld"] = float(
                wb_aa_data_dict[str(row.Channel)].wateryld)
            new_lsu_shapefile_gpd.loc[index, "perc"] = float(
                wb_aa_data_dict[str(row.Channel)].perc)
            new_lsu_shapefile_gpd.loc[index, "et"] = float(
                wb_aa_data_dict[str(row.Channel)].et)
            new_lsu_shapefile_gpd.loc[index, "cn"] = float(
                wb_aa_data_dict[str(row.Channel)].cn)
            new_lsu_shapefile_gpd.loc[index, "pet"] = float(
                wb_aa_data_dict[str(row.Channel)].pet)

        output_map_categories = ["precip", "surq_gen",
                                 "latq", "wateryld", "perc", "et", "cn", "pet"]

        if not os.path.isdir(os.path.join(os.environ["swatplus_wf_dir"], "temp")):
            os.makedirs(os.path.join(os.environ["swatplus_wf_dir"], "temp"))

        new_lsu_shapefile_gpd.to_file(os.path.join(
            os.environ["swatplus_wf_dir"], "temp", "tmp.shp"))
        if not os.path.isdir("{base}/{model_name}/Scenarios/Default/Figures".format(
                base=base, model_name=namelist.Project_Name)):
            os.makedirs("{base}/{model_name}/Scenarios/Default/Figures/annual_average_maps".format(
                base=base, model_name=namelist.Project_Name))

        for map_category in output_map_categories:
            log.info(
                "  - creating {cat} map in {out}".format(
                    cat=map_category,
                    out="{base}/{model_name}/Scenarios/Default/Figures/annual_average_maps".format(
                        base=base, model_name=namelist.Project_Name)
                ),
                keep_log)

            rasterise(
                os.path.join(os.environ["swatplus_wf_dir"], "temp", "tmp.shp"),
                map_category,
                "{base}/{model_name}/Watershed/Rasters/DEM/{dem}".format(
                    base=base, model_name=namelist.Project_Name,
                    dem=namelist.Topography if namelist.Topography.endswith(".tif") else \
                            namelist.Topography + ".tif"),
                "{base}/{model_name}/Scenarios/Default/Figures/annual_average_maps/{cat}.tif".format(
                    base=base, model_name=namelist.Project_Name, cat=map_category))
        wb_aa_data_list = None

    if os.path.isfile(yr_lsu_wb_file):
        print("\t-> creating yearly maps at LSU level")
        log.info("creating yearly maps at LSU level", keep_log)
        # read shapefile
        log.info("reading lsu shapefile", keep_log)

        lsu_shapefile_gpd = geopandas.read_file(lsus_shapefile)

        lsu_shapefile_gpd["precip"] = 0.0
        lsu_shapefile_gpd["surq_gen"] = 0.0
        lsu_shapefile_gpd["latq"] = 0.0
        lsu_shapefile_gpd["wateryld"] = 0.0
        lsu_shapefile_gpd["perc"] = 0.0
        lsu_shapefile_gpd["et"] = 0.0
        lsu_shapefile_gpd["cn"] = 0.0
        lsu_shapefile_gpd["pet"] = 0.0

        # read output data into dictionary
        log.info("reading yearly LSU results", keep_log)
        wb_yr_data_list = read_from(yr_lsu_wb_file)
        wb_yr_data_dict = {}
        for wb_yr_line in wb_yr_data_list[3:]:
            wb_yr_line_parts = wb_yr_line.split()

            year = wb_yr_line_parts[3]
            if not year in wb_yr_data_dict:
                wb_yr_data_dict[year] = {}

            lsu_no = wb_yr_line_parts[4]
            if not lsu_no in wb_yr_data_dict[year]:
                wb_yr_data_dict[year][lsu_no] = wb_result(wb_yr_line_parts)

        # add output to shapefile
        log.info("mapping LSU results for each year", keep_log)
        output_map_categories = ["precip", "surq_gen",
                "latq", "wateryld", "perc", "et", "cn", "pet"]
        maps_total = len(wb_yr_data_dict) * len(output_map_categories)
        count = 0
        for results_year in wb_yr_data_dict:
            new_lsu_shapefile_gpd = lsu_shapefile_gpd
            for index, row in lsu_shapefile_gpd.iterrows():
                new_lsu_shapefile_gpd.loc[index, "precip"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].precip)
                new_lsu_shapefile_gpd.loc[index, "surq_gen"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].surq_gen)
                new_lsu_shapefile_gpd.loc[index, "latq"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].latq)
                new_lsu_shapefile_gpd.loc[index, "wateryld"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].wateryld)
                new_lsu_shapefile_gpd.loc[index, "perc"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].perc)
                new_lsu_shapefile_gpd.loc[index, "et"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].et)
                new_lsu_shapefile_gpd.loc[index, "cn"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].cn)
                new_lsu_shapefile_gpd.loc[index, "pet"] = float(
                    wb_yr_data_dict[results_year][str(row.Channel)].pet)


            if not os.path.isdir(os.path.join(os.environ["swatplus_wf_dir"], "temp")):
                os.makedirs(os.path.join(
                    os.environ["swatplus_wf_dir"], "temp"))

            new_lsu_shapefile_gpd.to_file(os.path.join(
                os.environ["swatplus_wf_dir"], "temp", "tmp.shp"))
            if not os.path.isdir("{base}/{model_name}/Scenarios/Default/Figures/yearly_maps".format(
                    base=base, model_name=namelist.Project_Name)):
                os.makedirs("{base}/{model_name}/Scenarios/Default/Figures/yearly_maps".format(
                    base=base, model_name=namelist.Project_Name))

            for map_category in output_map_categories:
                log.info(
                    "  - creating {yr} {cat} map in {out}".format(
                        cat=map_category,
                        yr=results_year,
                        out="{base}/{model_name}/Scenarios/Default/Figures/yearly_maps".format(
                            base=base, model_name=namelist.Project_Name)),
                    keep_log)
                rasterise(
                    os.path.join(os.environ["swatplus_wf_dir"], "temp", "tmp.shp"),
                    map_category,
                    "{base}/{model_name}/Watershed/Rasters/DEM/{dem}".format(
                        base=base,
                        model_name=namelist.Project_Name,
                        dem=namelist.Topography if namelist.Topography.endswith(".tif") else \
                            namelist.Topography + ".tif"),
                    "{base}/{model_name}/Scenarios/Default/Figures/yearly_maps/{cat}_{yr}.tif".format(
                        base=base,
                        model_name=namelist.Project_Name,
                        cat=map_category,
                        yr=results_year)
                    )
                count += 1
                show_progress(count, maps_total, string_before = "\t   ", string_after = "creating {0} for the year {1}".format(
                    map_category, results_year))
            wb_yr_data_list = None
else:
    print("\n\t ! LSUs shapefile was not found, cannot create LSU figures")
    log.info(" - LSUs shapefile was not found, cannot create LSU figures", keep_log)

# hrus
log.info("looking for HRUs shapefile", keep_log)
print("\n\n\t-> looking for HRUs shapefile")
if os.path.isfile(hrus_shapefile):
    print("\t-> HRUs shapefile has been found, however, maps cannot be created in this version of SWAT+ AW")
    log.info(" - HRUs shapefile has been found, however, maps cannot be created in this version of SWAT+ AW", keep_log)
    log.info(" - however, maps cannot be created in this version of SWAT+ AW", keep_log)
else:
    print("\t ! HRUs shapefile was not found, cannot create HRU figures")
    log.info(" - HRUs shapefile was not found, cannot create HRU figures", keep_log)

clear_directory(os.path.join(os.environ["swatplus_wf_dir"], "temp"))
