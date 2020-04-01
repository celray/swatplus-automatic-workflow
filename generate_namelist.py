'''
date        : 31/03/2020
description : this module creates a namelist and extracts a dataset from
              an existing model.

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

# imports
import os
import shutil
import sys

sys.argv[1] = sys.argv[1].replace("\\\\", "/")
sys.argv[1] = sys.argv[1].replace("\\", "/")

sys.path.insert(0, "{0}/packages".format(os.environ["swatplus_wf_dir"]))
sys.path.insert(0, sys.argv[1])

from namelist_template import namelist_string, calibration_config_template
from helper_functions import file_name, list_folders, read_from, xml_children_attributes, write_to

specified_name = False

if os.path.isfile("{base}/namelist.py".format(base = sys.argv[1])):
    import namelist
    specified_name = namelist.Project_Name in list_folders(sys.argv[1])
    if namelist.Model_2_namelist == False:
        sys.exit(0)

    if not os.path.isdir("{base}/data/old_namelists".format(base = sys.argv[1])):
        os.makedirs("{base}/data/old_namelists".format(base = sys.argv[1]))

    count = 1
    while True:
        if not os.path.isfile("{base}/data/old_namelists/namelist_bu_{count}.py".format(
                base = sys.argv[1], count = count
            )):
            shutil.copyfile("{base}/namelist.py".format(base = sys.argv[1]),
                "{base}/data/old_namelists/namelist_bu_{count}.py".format(
                    base = sys.argv[1], count = count
                )
            )
            break
        count += 1

directory_folders = list_folders(sys.argv[1])
model_directories = []

for model_directory in directory_folders:
    if os.path.isfile("{base}/{fn}/{fn}.qgs".format(base = sys.argv[1], fn = model_directory)):
        model_directories.append(model_directory)

if len(model_directories) == 0:
    print("\t! there is no model found in this directory.")
    sys.exit(1)

selected_model = None

if not specified_name:
    # get input from user
    while True:
        print("\t> for which model do you want to get namelist")
        count = 0
        for i in range(0, len(model_directories)):
            print("\t  {index} - {model_name}".format(model_name = model_directories[i], index = i + 1))

        try:
            m_index = int(input("\n\t  > ")) - 1
            if m_index < 0:
                raise ValueError
            selected_model = model_directories[m_index]
            break
        except:
            print("\t! invalid selection\n")

else:
    selected_model = namelist.Project_Name

# create dada directory structure
directories = ["calibration", "observations", "rasters", "shapefiles", "tables", "weather"]

for directory in directories:
    if not os.path.isdir("{0}/{1}/{2}".format(sys.argv[1], "data", directory)):
        os.makedirs("{0}/{1}/{2}".format(sys.argv[1], "data", directory))

# save calibration config file
write_to(
    "{base}/data/calibration/calibration_config.csv".format(base = sys.argv[1]),
    calibration_config_template
)

# get project data from xml file
xml_fn = "{base}/{fn}/{fn}.qgs".format(base = sys.argv[1], fn = selected_model)

title = xml_children_attributes(xml_fn, "./")["title"]
delin_data = xml_children_attributes(xml_fn, "./properties/{s}/delin".format(s = selected_model))
hru_data = xml_children_attributes(xml_fn, "./properties/{s}/hru".format(s = selected_model))
landuse_data = xml_children_attributes(xml_fn, "./properties/{s}/landuse".format(s = selected_model))
soil_data = xml_children_attributes(xml_fn, "./properties/{s}/soil".format(s = selected_model))

# get rasters
shutil.copyfile(    # get soil file
    "{base}/{project_name}/Watershed/Rasters/Soil/{soil_name}".format(
        base = sys.argv[1], project_name = selected_model,
        soil_name = file_name(soil_data["file"])
        ),
    "{base}/data/rasters/{soil_name}".format(
        base = sys.argv[1],
        soil_name = file_name(soil_data["file"])
        ))

shutil.copyfile(    # get landuse file
    "{base}/{project_name}/Watershed/Rasters/Landuse/{landuse_name}".format(
        base = sys.argv[1], project_name = selected_model,
        landuse_name = file_name(landuse_data["file"])
        ),
    "{base}/data/rasters/{landuse_name}".format(
        base = sys.argv[1],
        landuse_name = file_name(landuse_data["file"])
        ))

shutil.copyfile(    # get dem file
    "{base}/{project_name}/Watershed/Rasters/DEM/{dem_name}".format(
        base = sys.argv[1], project_name = selected_model,
        dem_name = file_name(delin_data["DEM"])
        ),
    "{base}/data/rasters/{dem_name}".format(
        base = sys.argv[1],
        dem_name = file_name(delin_data["DEM"])
        ))


# get shapefiles
shapefile_extensions = ["shp", "shx", "cpg", "dbf", "prj"]

for shapefile_extension in shapefile_extensions:
    if os.path.isfile(
        "{base}/{project_name}/Watershed/Shapes/{shp_base}.{ext}".format(
            base = sys.argv[1], project_name = selected_model,
            shp_base = file_name(delin_data["snapOutlets"], extension=False),
            ext = shapefile_extension
            ),
        ):

        shutil.copyfile(    # get outlets file
            "{base}/{project_name}/Watershed/Shapes/{shp_base}.{ext}".format(
                base = sys.argv[1], project_name = selected_model,
                shp_base = file_name(delin_data["snapOutlets"], extension=False),
                ext = shapefile_extension
                ),
            "{base}/data/shapefiles/outlets.{ext}".format(
                base = sys.argv[1],
                shp_base = file_name(delin_data["snapOutlets"], extension=False),
                ext = shapefile_extension
                ))

    if not delin_data["burn"] is None:
        if not os.path.isfile(
            "{base}/{project_name}/Watershed/Shapes/{shp_base}.{ext}".format(
                base = sys.argv[1], project_name = selected_model,
                shp_base = file_name(delin_data["burn"], extension=False),
                ext = shapefile_extension
                ),
            ):

            shutil.copyfile(    # get outlets file
                "{base}/{project_name}/Watershed/Shapes/{shp_base}.{ext}".format(
                    base = sys.argv[1], project_name = selected_model,
                    shp_base = file_name(delin_data["burn"], extension=False),
                    ext = shapefile_extension
                    ),
                "{base}/data/shapefiles/{shp_base}.{ext}".format(
                    base = sys.argv[1],
                    shp_base = file_name(delin_data["burn"], extension=False),
                    ext = shapefile_extension
                    ))

# retrieve weather
file_cio = read_from(
    "{base}/{project_name}/Scenarios/Default/TxtInOut/file.cio".format(
        base = sys.argv[1], project_name = selected_model
        )
)


weather_dir = file_cio[-2].strip("\n").split()[1] if not \
    file_cio[-2].strip("\n").split()[1] == "null" else \
        ""


if weather_dir is not None:
    pcp_files = read_from(
        "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}pcp.cli".format(
        base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir)
        )[2:]

    slr_files = read_from(
        "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}slr.cli".format(
        base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir)
        )[2:]

    hmd_files = read_from(
        "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}hmd.cli".format(
        base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir)
        )[2:]

    tmp_files = read_from(
        "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}tmp.cli".format(
        base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir)
        )[2:]

    wnd_files = read_from(
        "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}wnd.cli".format(
        base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir)
        )[2:]

    # get pcp
    pcp_stations = "ID,NAME,LAT,LONG,ELEVATION\n"
    slr_stations = "ID,NAME,LAT,LONG,ELEVATION\n"
    hmd_stations = "ID,NAME,LAT,LONG,ELEVATION\n"
    wnd_stations = "ID,NAME,LAT,LONG,ELEVATION\n"
    tmp_stations = "ID,NAME,LAT,LONG,ELEVATION\n"

    id_num = 1
    for w_file in pcp_files:
        f_content = read_from(
            "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}{wf}".format(
            base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir, wf = w_file[:-1])
        )
        pcp_stations += "{idn},{name},{lat},{lon},{elev}\n".format(
            idn = count,
            name = w_file[:-5],
            lat = f_content[2].split()[2],
            lon = f_content[2].split()[3],
            elev = f_content[2].split()[4]
            )

        fc_string = "{y}0101\n".format(y = f_content[3].split()[0])
        for line in f_content[3:]:
            fc_string += "{value}\n".format(value = ",".join(line.split()[2:]))
        write_to(
            "{base}/data/weather/{fname}.txt".format(
            base = sys.argv[1],
            fname = w_file[:-5]),
            fc_string
        )
        count += 1

    id_num = 1
    for w_file in slr_files:
        f_content = read_from(
            "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}{wf}".format(
            base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir, wf = w_file[:-1])
        )
        slr_stations += "{idn},{name},{lat},{lon},{elev}\n".format(
            idn = count,
            name = w_file[:-5],
            lat = f_content[2].split()[2],
            lon = f_content[2].split()[3],
            elev = f_content[2].split()[4]
            )

        fc_string = "{y}0101\n".format(y = f_content[3].split()[0])
        for line in f_content[3:]:
            fc_string += "{value}\n".format(value = ",".join(line.split()[2:]))
        write_to(
            "{base}/data/weather/{fname}.txt".format(
            base = sys.argv[1],
            fname = w_file[:-5]),
            fc_string
        )
        count += 1


    id_num = 1
    for w_file in wnd_files:
        f_content = read_from(
            "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}{wf}".format(
            base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir, wf = w_file[:-1])
        )
        wnd_stations += "{idn},{name},{lat},{lon},{elev}\n".format(
            idn = count,
            name = w_file[:-5],
            lat = f_content[2].split()[2],
            lon = f_content[2].split()[3],
            elev = f_content[2].split()[4]
            )

        fc_string = "{y}0101\n".format(y = f_content[3].split()[0])
        for line in f_content[3:]:
            fc_string += "{value}\n".format(value = ",".join(line.split()[2:]))
        write_to(
            "{base}/data/weather/{fname}.txt".format(
            base = sys.argv[1],
            fname = w_file[:-5]),
            fc_string
        )
        count += 1


    id_num = 1
    for w_file in tmp_files:
        f_content = read_from(
            "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}{wf}".format(
            base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir, wf = w_file[:-1])
        )
        tmp_stations += "{idn},{name},{lat},{lon},{elev}\n".format(
            idn = count,
            name = w_file[:-5],
            lat = f_content[2].split()[2],
            lon = f_content[2].split()[3],
            elev = f_content[2].split()[4]
            )

        fc_string = "{y}0101\n".format(y = f_content[3].split()[0])
        for line in f_content[3:]:
            fc_string += "{value}\n".format(value = ",".join(line.split()[2:]))
        write_to(
            "{base}/data/weather/{fname}.txt".format(
            base = sys.argv[1],
            fname = w_file[:-5]),
            fc_string
        )
        count += 1


    id_num = 1
    for w_file in hmd_files:
        f_content = read_from(
            "{base}/{project_name}/Scenarios/Default/TxtInOut/{weather_dir}{wf}".format(
            base = sys.argv[1], project_name = selected_model, weather_dir = weather_dir, wf = w_file[:-1])
        )
        hmd_stations += "{idn},{name},{lat},{lon},{elev}\n".format(
            idn = count,
            name = w_file[:-5],
            lat = f_content[2].split()[2],
            lon = f_content[2].split()[3],
            elev = f_content[2].split()[4]
            )

        fc_string = "{y}0101\n".format(y = f_content[3].split()[0])
        for line in f_content[3:]:
            fc_string += "{value}\n".format(value = ",".join(line.split()[2:]))
        write_to(
            "{base}/data/weather/{fname}.txt".format(
            base = sys.argv[1],
            fname = w_file[:-5]),
            fc_string
        )
        count += 1

    write_to(
        "{base}/data/weather/pcp.txt".format(
        base = sys.argv[1],
        fname = w_file[:-5]),
        pcp_stations
    )

    write_to(
        "{base}/data/weather/tmp.txt".format(
        base = sys.argv[1],
        fname = w_file[:-5]),
        tmp_stations
    )

    write_to(
        "{base}/data/weather/hmd.txt".format(
        base = sys.argv[1],
        fname = w_file[:-5]),
        hmd_stations
    )

    write_to(
        "{base}/data/weather/slr.txt".format(
        base = sys.argv[1],
        fname = w_file[:-5]),
        slr_stations
    )    

    write_to(
        "{base}/data/weather/wnd.txt".format(
        base = sys.argv[1],
        fname = w_file[:-5]),
        wnd_stations
    )

# get model options and retrieve tables from database
from sqlite_tools import sqlite_connection
db = sqlite_connection("{base}/{project_name}/{db_fn}".format(
    db_fn = file_name(soil_data["database"]),
    project_name = selected_model,
    base = sys.argv[1]
    ))

db.connect()

db.dump_csv(   # extract usersoil
    soil_data["databaseTable"],
    "{base}/data/tables/{data_table}.csv".format(
        base = sys.argv[1],
        data_table = soil_data["databaseTable"]
        ))

db.dump_csv(   # extract soil lookup
    soil_data["table"],
    "{base}/data/tables/{data_table}.csv".format(
        base = sys.argv[1],
        data_table = soil_data["table"]
        ))

db.dump_csv(   # extract landuse lookup
    landuse_data["table"],
    "{base}/data/tables/{data_table}.csv".format(
        base = sys.argv[1],
        data_table = landuse_data["table"]
        ))

et_method = db.read_table_columns("codes_bsn", ["pet"])[0][0] + 1
routing_method = db.read_table_columns("codes_bsn", ["rte_cha"])[0][0] + 1
routing_timestep = db.read_table_columns("codes_bsn", ["event"], report_ = True)[0][0] + 1

start_year = db.read_table_columns("time_sim", ["yrc_start"])[0][0]
end_year = db.read_table_columns("time_sim", ["yrc_end"], report_ = True)[0][0]
warm_up = db.read_table_columns("print_prt", ["nyskip"], report_ = True)[0][0]

print_prt_objects = db.read_table_columns("print_prt_object", "all", report_ = True)

print_objects = ""

for print_prt_object in print_prt_objects:
    object_name = print_prt_object[2]
    print_data = list(print_prt_object[3:])
    if not print_data == [0, 0, 1, 0]:
        print_data[0] = 1 if not print_data[0] == 0 else print_data[0]
        print_data[1] = 2 if not print_data[1] == 0 else print_data[0]
        print_data[2] = 3 if not print_data[2] == 0 else print_data[0]
        print_data[3] = 4 if not print_data[3] == 0 else print_data[0]

        print_data = [val for val in print_data if val != 0]

        print_objects += '{prt_obj}: {print_list},\n'.format(
            prt_obj = '"{0}"'.format(object_name).ljust(15).rjust(44),
            print_list = str(print_data)
        )

ws_threshold_type = 1
channel_threshold = delin_data["thresholdCh"]
stream_threshold = delin_data["thresholdSt"]
shap_threshold = delin_data["snapThreshold"]

slope_classes = hru_data["slopeBands"]
hru_method = 0
hru_threshold_type = 0
land_soil_slope_thresholds = ''
target_area = 0
target_value = 0

if hru_data["isArea"] == '1':
    hru_method = 3
    target_area = hru_data["areaVal"]
    hru_threshold_type = hru_data["useArea"] if hru_data["useArea"] == \
        0 else 2

if hru_data["isDominantHRU"] == '1':
    hru_method = 2

if hru_data["isTarget"] == '1':
    hru_method = 4
    target_value = hru_data["targetVal"]

if (hru_data["isArea"] == '0') and (hru_data["isDominantHRU"] == '0') and \
    (hru_data["isMultiple"] == '1') and (hru_data["isTarget"] == '0'):
    hru_method = 5
    land_soil_slope_thresholds = "{land}, {soil}, {slope}".format(
        land = hru_data["landuseVal"],
        soil = hru_data["soilVal"],
        slope = hru_data["slopeVal"]
    )

# get parameters
calfile_name = file_cio[21].split()[2] if not file_cio[21].split()[2] == \
    "null" else ""

# write namelist
write_to(
    "{base}/namelist.py".format(base = sys.argv[1]),
    namelist_string.format(
        prj_name = selected_model,
        dem_fn = file_name(delin_data["DEM"]),
        soil_fn = file_name(soil_data["file"]),
        landuse_fn = file_name(landuse_data["file"]),
        soillookup_fn = "{0}.csv".format(soil_data["table"]),
        landuselookup_fn = "{0}.csv".format(landuse_data["table"]),
        usersoil_fn = "{0}.csv".format(soil_data["databaseTable"]),
        outlets_fn = "outlets.shp",
        ws_threshold_type = ws_threshold_type,
        channel_threshold = channel_threshold,
        stream_threshold = stream_threshold,
        shap_threshold = shap_threshold,
        slope_classes = slope_classes,
        hru_method = hru_method,
        hru_threshold_type = hru_threshold_type,
        land_soil_slope_thresholds = land_soil_slope_thresholds,
        target_area = target_area,
        target_value = target_value,
        et_method = et_method,
        routing_method = routing_method,
        routing_timestep = routing_timestep,
        start_year = start_year,
        end_year = end_year,
        warm_up = warm_up,
        print_objects = print_objects,
        calfile_name = calfile_name,
        )
    )

if os.path.isdir("{base}/__pycache__".format(base = sys.argv[1])):
    shutil.rmtree("{base}/__pycache__".format(base = sys.argv[1]))

sys.exit(1)
