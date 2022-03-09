'''
date        : 31/03/2020
description : this module coordinates the editor part of model setup

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import os
import sys
import shutil
import subprocess
import platform

# adding to path before importing custom modules
sys.path.insert(0, os.path.join(os.environ["swatplus_wf_dir"], "packages"))
sys.path.append(os.path.join(os.environ["swatplus_wf_dir"]))
sys.path.insert(0, sys.argv[1])


from sqlite_tools import sqlite_connection
import model_options
from editor_api.weather2012_to_weather import list_files, read_from, write_to, copy_file
import config
from logger import log


base_dir = os.environ["BASE_DIR"]
model_name = config.Project_Name


class swat_plus_editor:
    def __init__(self, base_directory, model_name):
        self.db = None

        self.model_name = model_name

        self.base_directory = base_directory.replace('"', "")
        self.scripts_dir = os.environ["swatplus_wf_dir"]
        self.model_dir = "{base}/{model_name}".format(
            base=self.base_directory, model_name=model_name)

        # set up swat_editor api
        self.variables = {
            "model_dir": self.model_dir,
            "scripts_dir": self.scripts_dir,
            "base_directory": self.base_directory,
            "selection": model_name
        }

        self.api = "{scripts_dir}/editor_api/swatplus_api.py".format(
            **self.variables)

        self.api_dir = os.path.dirname(self.api)
        self.prj_database = "{model_dir}/{selection}.sqlite".format(
            **self.variables)
        self.ref_database = "{model_dir}/swatplus_datasets.sqlite".format(
            **self.variables)

        self.weather_source = "{base_directory}/data/weather".format(
            **self.variables)
        self.wgn_table_name = "wgn_cfsr_world"

        self.txt_in_out_dir = "{model_dir}/Scenarios/Default/TxtInOut".format(
            **self.variables)
        self.weather_data_dir = "{model_dir}/Scenarios/Default/TxtInOut".format(
            **self.variables)
        self.wgn_db = "{api_dir}/swatplus_wgn.sqlite".format(
            api_dir=self.api_dir)

        if platform.system() == "Windows":
            python_exe = "python"
        else:
            python_exe = "python3"

        self.variables = {
            "models_dir": self.model_dir,
            "scripts_dir": self.scripts_dir,
            "api": self.api,
            "weather_format": "observed",
            "txt_in_out_dir": self.txt_in_out_dir,
            "swat_exe_release": "rev60.5.4_64rel.exe" if platform.system() == "Windows" else "./rev60.5.2_64rel_linux",
            "swat_exe_debug": "rev60.5.4_64debug.exe" if platform.system() == "Windows" else "./rev60.5.2_64rel_linux",
            "python_exe": python_exe,
            "import_typ_wgn": "wgn",
            "api_dir": self.api_dir,
            "p_db": self.prj_database,
            "r_db": self.ref_database,
            "w_src": self.weather_source,
            "w_dat": self.weather_data_dir,
            "wgn_table": self.wgn_table_name,
            "wgn_db": self.wgn_db,
            "model_dir": self.model_dir,
            "base_directory": self.base_directory,
            "selection": model_name
        }
        self.db = sqlite_connection(self.prj_database)

    def initialise_databases(self):
        "correct bug in plants_plt days_mat"
        self.db = sqlite_connection(self.prj_database)
        self.db.connect()

        if self.db.table_exists('codes_bsn'):
            self.db.delete_table('codes_bsn')

        sql_command = '''CREATE TABLE codes_bsn (
                    id         INTEGER       NOT NULL
                                            PRIMARY KEY,
                    pet_file   VARCHAR (255),
                    wq_file    VARCHAR (255),
                    pet        INTEGER       NOT NULL,
                    event      INTEGER       NOT NULL,
                    crack      INTEGER       NOT NULL,
                    rtu_wq     INTEGER       NOT NULL,
                    sed_det    INTEGER       NOT NULL,
                    rte_cha    INTEGER       NOT NULL,
                    deg_cha    INTEGER       NOT NULL,
                    wq_cha     INTEGER       NOT NULL,
                    nostress   INTEGER       NOT NULL,
                    cn         INTEGER       NOT NULL,
                    c_fact     INTEGER       NOT NULL,
                    carbon     INTEGER       NOT NULL,
                    lapse      INTEGER       NOT NULL,
                    uhyd       INTEGER       NOT NULL,
                    sed_cha    INTEGER       NOT NULL,
                    tiledrain  INTEGER       NOT NULL,
                    wtable     INTEGER       NOT NULL,
                    soil_p     INTEGER       NOT NULL,
                    gampt      INTEGER       NOT NULL,
                    atmo_dep   VARCHAR (255) NOT NULL,
                    stor_max   INTEGER       NOT NULL,
                    i_fpwet    INTEGER       NOT NULL
                );
                '''
        self.db.cursor.execute(sql_command)
        self.db.commit_changes()

        if self.db.table_exists('parameters_bsn'):
            self.db.delete_table('parameters_bsn')

        sql_command = '''CREATE TABLE parameters_bsn (
                id           INTEGER NOT NULL
                                    PRIMARY KEY,
                lai_noevap   REAL    NOT NULL,
                sw_init      REAL    NOT NULL,
                surq_lag     REAL    NOT NULL,
                adj_pkrt     REAL    NOT NULL,
                adj_pkrt_sed REAL    NOT NULL,
                lin_sed      REAL    NOT NULL,
                exp_sed      REAL    NOT NULL,
                orgn_min     REAL    NOT NULL,
                n_uptake     REAL    NOT NULL,
                p_uptake     REAL    NOT NULL,
                n_perc       REAL    NOT NULL,
                p_perc       REAL    NOT NULL,
                p_soil       REAL    NOT NULL,
                p_avail      REAL    NOT NULL,
                rsd_decomp   REAL    NOT NULL,
                pest_perc    REAL    NOT NULL,
                msk_co1      REAL    NOT NULL,
                msk_co2      REAL    NOT NULL,
                msk_x        REAL    NOT NULL,
                nperco_lchtile REAL    NOT NULL,
                evap_adj     REAL    NOT NULL,
                scoef        REAL    NOT NULL,
                denit_exp    REAL    NOT NULL,
                denit_frac   REAL    NOT NULL,
                man_bact     REAL    NOT NULL,
                adj_uhyd     REAL    NOT NULL,
                cn_froz      REAL    NOT NULL,
                dorm_hr      REAL    NOT NULL,
                plaps        REAL    NOT NULL,
                tlaps        REAL    NOT NULL,
                n_fix_max    REAL    NOT NULL,
                rsd_decay    REAL    NOT NULL,
                rsd_cover    REAL    NOT NULL,
                urb_init_abst REAL    NOT NULL,
                petco_pmpt   REAL    NOT NULL,
                uhyd_alpha   REAL    NOT NULL,
                splash       REAL    NOT NULL,
                rill         REAL    NOT NULL,
                surq_exp     REAL    NOT NULL,
                cov_mgt      REAL    NOT NULL,
                cha_d50      REAL    NOT NULL,
                co2          REAL    NOT NULL,
                day_lag_max  REAL    NOT NULL,
                igen         INTEGER NOT NULL
            );
            '''
        self.db.cursor.execute(sql_command)
        self.db.commit_changes()

        
        if self.db.table_exists('plants_plt'):
            self.db.delete_table('plants_plt')

        sql_command = """CREATE TABLE plants_plt (
            id          INTEGER NOT NULL
                                PRIMARY KEY,
            name        TEXT    NOT NULL,
            plnt_typ    TEXT    NOT NULL,
            gro_trig    TEXT    NOT NULL,
            nfix_co     REAL    NOT NULL,
            days_mat    REAL    NOT NULL,
            bm_e        REAL    NOT NULL,
            harv_idx    REAL    NOT NULL,
            lai_pot     REAL    NOT NULL,
            frac_hu1    REAL    NOT NULL,
            lai_max1    REAL    NOT NULL,
            frac_hu2    REAL    NOT NULL,
            lai_max2    REAL    NOT NULL,
            hu_lai_decl REAL    NOT NULL,
            dlai_rate   REAL    NOT NULL,
            can_ht_max  REAL    NOT NULL,
            rt_dp_max   REAL    NOT NULL,
            tmp_opt     REAL    NOT NULL,
            tmp_base    REAL    NOT NULL,
            frac_n_yld  REAL    NOT NULL,
            frac_p_yld  REAL    NOT NULL,
            frac_n_em   REAL    NOT NULL,
            frac_n_50   REAL    NOT NULL,
            frac_n_mat  REAL    NOT NULL,
            frac_p_em   REAL    NOT NULL,
            frac_p_50   REAL    NOT NULL,
            frac_p_mat  REAL    NOT NULL,
            harv_idx_ws REAL    NOT NULL,
            usle_c_min  REAL    NOT NULL,
            stcon_max   REAL    NOT NULL,
            vpd         REAL    NOT NULL,
            frac_stcon  REAL    NOT NULL,
            ru_vpd      REAL    NOT NULL,
            co2_hi      REAL    NOT NULL,
            bm_e_hi     REAL    NOT NULL,
            plnt_decomp REAL    NOT NULL,
            lai_min     REAL    NOT NULL,
            bm_tree_acc REAL    NOT NULL,
            yrs_mat     REAL    NOT NULL,
            bm_tree_max REAL    NOT NULL,
            ext_co      REAL    NOT NULL,
            leaf_tov_mn REAL    NOT NULL,
            leaf_tov_mx REAL    NOT NULL,
            bm_dieoff   REAL    NOT NULL,
            rt_st_beg   REAL    NOT NULL,
            rt_st_end   REAL    NOT NULL,
            plnt_pop1   REAL    NOT NULL,
            frac_lai1   REAL    NOT NULL,
            plnt_pop2   REAL    NOT NULL,
            frac_lai2   REAL    NOT NULL,
            frac_sw_gro REAL    NOT NULL,
            aeration    REAL    NOT NULL,
            wnd_dead    REAL    NOT NULL,
            wnd_flat    REAL    NOT NULL,
            description TEXT
        );
        """
        self.db.cursor.execute(sql_command)
        self.db.commit_changes()

        # import GIS
        os.chdir(self.api_dir)
        os.system('{python_exe} {api} create_database --db_type=project --db_file="{p_db}" --db_file2="{r_db}"'.format(**self.variables))
        os.system('{python_exe} {api} import_gis --delete_existing=y --project_db_file="{p_db}"'.format(**self.variables))

    def setup_project(self):
        # specify project config info

        config_info = self.db.read_table_columns("project_config", "all")




        config_info = list(config_info[-1])

        for index in range(0, len(config_info)):
            config_info[index] = str(config_info[index])


        config_info[1] = self.model_name
        config_info[3] = "2.1.0"
        config_info[6] = self.prj_database
        config_info[7] = self.ref_database
        config_info[8] = self.wgn_db
        config_info[9] = self.wgn_table_name
        config_info[10] = self.weather_data_dir
        config_info[11] = "observed"
        config_info[12] = self.txt_in_out_dir

        print(" ")
        self.db.delete_rows("project_config")
        self.db.insert_row("project_config", config_info)
        self.db.commit_changes()


    def set_printing_weather(self, Start_Year, End_Year):

        # set printing once for all
        print_object_table = self.db.read_table_columns(
            "print_prt_object", "*")
        new_print_object_table = []
        for prt_row in print_object_table:
            prt_row = [str(item) for item in prt_row]

            new_print_object_table.append(prt_row)

        # set default printing to yearly for all
        self.db.delete_rows("print_prt_object")
        for new_row in new_print_object_table:
            new_row[3], new_row[4], new_row[5], new_row[6] = "0", "0", "1", "0"
            self.db.insert_row("print_prt_object", new_row)

        self.db.update_value("print_prt", "nyskip", str(
            config.Warm_Up_Period), "id", "1")
        self.db.update_value("print_prt", "csvout",
                             str(config.Print_CSV), "id", "1")

        for print_object in config.Print_Objects:
            self.db.update_value("print_prt_object", "daily", "0",
                "id", model_options.print_obj_lookup[print_object])
            self.db.update_value("print_prt_object", "monthly", "0",
                "id", model_options.print_obj_lookup[print_object])
            self.db.update_value("print_prt_object", "yearly", "0",
                "id", model_options.print_obj_lookup[print_object])
            self.db.update_value("print_prt_object", "avann", "0",
                "id", model_options.print_obj_lookup[print_object])

            if 1 in config.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "daily", "1",
                    "id", model_options.print_obj_lookup[print_object])

            if 2 in config.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "monthly", "1",
                    "id", model_options.print_obj_lookup[print_object])

            if 3 in config.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "yearly", "1",
                    "id", model_options.print_obj_lookup[print_object])

            if 4 in config.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "avann", "1",
                    "id", model_options.print_obj_lookup[print_object])

        self.db.close_connection()

        # add weather
        os.system('{python_exe} {api_dir}/weather2012_to_weather.py "{w_src}" "{w_dat}" {weather_format}'.format(**self.variables))
        os.system('{python_exe} {api} import_weather --delete_existing=y --create_stations=n --import_type={import_typ_wgn} --import_method=database --project_db_file="{p_db}"'.format(**self.variables))
        os.system('{python_exe} {api} import_weather --delete_existing=y --create_stations=y --import_type={weather_format} --project_db_file="{p_db}"'.format(**self.variables))

        # set simulation times
        time_sim_data = ["1", "0", str(Start_Year), "0", str(End_Year), "0"]
        print(" ")
        self.db.connect()
        self.db.delete_rows("time_sim")
        self.db.insert_row("time_sim", time_sim_data)
        self.db.close_connection()

    def write_files(self):

        # write files
        os.chdir(self.api_dir)
        os.system(
            '{python_exe} {api} write_files --output_files_dir="{txt_in_out_dir}" --project_db_file="{p_db}"'.format(**self.variables))

        # setting weather dir in cio
        # cio_content = read_from(
        #     "{tio}/file.cio".format(tio=self.txt_in_out_dir))
        # new_cio = ""

        # paths_to_set_for = ["pcp_path", "tmp_path",
        #                     "slr_path", "hmd_path", "wnd_path"]
        # for line_ in cio_content:
        #     if line_.split(" ")[0] in paths_to_set_for:
        #         line_ = line_.replace("null", "weather\\\\")
        #     new_cio += line_

        # write_to("{tio}/file.cio".format(tio=self.txt_in_out_dir), new_cio)

        # # clean up weather
        # weather_files = list_files(self.txt_in_out_dir, "tmp")
        # weather_files += list_files(self.txt_in_out_dir, "hmd")
        # weather_files += list_files(self.txt_in_out_dir, "slr")
        # weather_files += list_files(self.txt_in_out_dir, "pcp")
        # weather_files += list_files(self.txt_in_out_dir, "wnd")

        # for file in weather_files:
        #     if os.path.isfile(file):
        #         os.remove(file)

    def run(self, exe_type):
        os.chdir(self.txt_in_out_dir)

        copy_file("{scripts_dir}/editor_api/swat_exe/{swat_exe_debug}".format(**self.variables),
                  "{txt_in_out_dir}/{swat_exe_debug}".format(**self.variables))
        copy_file("{scripts_dir}/editor_api/swat_exe/{swat_exe_release}".format(**self.variables),
                  "{txt_in_out_dir}/{swat_exe_release}".format(**self.variables))

        if exe_type == 1:
            print("\n     >> running SWAT+")
            if platform.system() == "Linux":
                os.system("chmod 777 {swat_exe_release}".format(
                    **self.variables))

            # os.system("{swat_exe_release}")
            sub_process = subprocess.Popen("{swat_exe_release}".format(**self.variables), close_fds=True, shell=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            line = ""
            while sub_process.poll() is None:
                out = sub_process.stdout.read(1)
                encoding = 'utf-8'

                out_string = str(out, encoding)

                if (not out_string.endswith("\n")) or (not out_string.endswith("\r")):
                    line += out_string

                if out_string.endswith("\n") or out_string.endswith("\r"):
                    line = line.rstrip()
                    if not line == "":
                        line_parts = line.split()
                        # print(line_parts)
                        if line_parts[0] == "Original":
                            sys.stdout.write("\r\t   simulating: {yr}/{mn}/{dy}{tb}".format(
                                tb=" "*10, yr=line_parts[4], mn=line_parts[2], dy=line_parts[3]))
                        else:
                            if line_parts[0] == "Execution":
                                sys.stdout.write(
                                    "\r\t   finished running SWAT+    ")
                            elif line_parts[0] == "Revision":
                                print(
                                    "\t   SWAT+ version: {0}".format(line_parts[-1]))
                            elif line_parts[0] == "reading":
                                sys.stdout.write("\r\t   reading {0}            ".format(
                                    " ".join(line_parts[2:-3])))
                        sys.stdout.flush()
                    line = ""

        elif exe_type == 2:
            if platform.system() == "Linux":
                os.system("chmod 777 {swat_exe_release}".format(
                    **self.variables))

            os.system("{swat_exe_debug}".format(**self.variables))

    def landuse_management(self, launduse_management_settings):
        self.db.connect()

        if self.db.table_exists("landuse_lum"):
            mgt_sch_id_lookup = {sch_name[1]: str(
                sch_name[0]) for sch_name in self.db.read_table_columns("management_sch")}
            dtl_id_lookup = {dtl_name[1]: str(
                dtl_name[0]) for dtl_name in self.db.read_table_columns("d_table_dtl")}
            lum_mgtid_lookup = {dtl_name[1]: str(
                dtl_name[4]) for dtl_name in self.db.read_table_columns("landuse_lum")}
        else:
            print("\n\t> databases have not been configured")
            sys.exit(1)

        if len(launduse_management_settings) > 0:

            print("\n\t>  setting up land management options")

            for management_setting in launduse_management_settings:
                if management_setting["mgt_sch"] in mgt_sch_id_lookup:
                    self.db.delete_rows("management_sch_auto", col_where="management_sch_id",
                                        col_where_value=mgt_sch_id_lookup[management_setting["mgt_sch"]])
                    for auto_sch in management_setting:
                        if auto_sch.startswith("auto_sch"):
                            # get current id for management_sch_auto table
                            try:
                                maximum_mgt_sch_auto_id = max(int(auto_sch_row[0]) \
                                    for auto_sch_row in self.db.read_table_columns("management_sch_auto"))  # re-read incase of a changes
                            except ValueError:
                                maximum_mgt_sch_auto_id = 0

                            self.db.insert_row("management_sch_auto", [
                                str(maximum_mgt_sch_auto_id + 1),
                                str(mgt_sch_id_lookup[management_setting["mgt_sch"]]),
                                str(dtl_id_lookup[management_setting[auto_sch]]),
                            ]
                            )

                    self.db.delete_rows("management_sch_op", col_where="management_sch_id",
                                        col_where_value=mgt_sch_id_lookup[management_setting["mgt_sch"]])
                    for op_sch in management_setting:
                        if op_sch.startswith("op_sch"):
                            # get current id for management_sch_op table
                            try:
                                maximum_mgt_sch_op_id = max(int(op_sch_row[0]) for op_sch_row
                                                            in self.db.read_table_columns("management_sch_op"))  # re-read incase of a changes
                            except ValueError:
                                maximum_mgt_sch_op_id = 0

                            self.db.insert_row("management_sch_op", [
                                str(maximum_mgt_sch_op_id + 1),
                                str(mgt_sch_id_lookup[management_setting["mgt_sch"]]),
                                management_setting[op_sch]["op_typ"],
                                str(int(
                                    management_setting[op_sch]["date"].split("/")[1])),
                                str(int(
                                    management_setting[op_sch]["date"].split("/")[0])),
                                "0",
                                management_setting["landuse"].lower(),
                                "-",
                                str(management_setting[op_sch]
                                    ["date"].split("/")[0]),
                                "-",
                                str(management_setting[op_sch]["rot_year"])
                            ]
                            )

                            if management_setting[op_sch]["harvest_part"] is None:
                                self.db.update_value(
                                    "management_sch_op", "op_data2", None, "id", str(maximum_mgt_sch_op_id + 1))
                            else:
                                self.db.update_value("management_sch_op", "op_data2", 
                                    management_setting[op_sch]["harvest_part"], "id", str(maximum_mgt_sch_op_id + 1))
                            self.db.update_value(
                                "management_sch_op", "description", None, "id", str(maximum_mgt_sch_op_id + 1))

                else:
                    # get current id for management_sch_auto table
                    try:
                        maximum_mgt_sch_id = max(int(auto_sch_row[0]) for auto_sch_row
                                                 in self.db.read_table_columns("management_sch"))  # re-read incase of a changes
                    except ValueError:
                        maximum_mgt_sch_id = 0

                    self.db.insert_row("management_sch", [
                        str(maximum_mgt_sch_id + 1),
                        management_setting["mgt_sch"],
                    ])

                    mgt_sch_id_lookup = {sch_name[1]: str(sch_name[0])
                                         for sch_name in self.db.read_table_columns("management_sch")}  # re-read
                    lum_id_lookup = {lum_name[1]: str(lum_name[0])
                                     for lum_name in self.db.read_table_columns("landuse_lum")}  # re-read

                    self.db.update_value("landuse_lum", "mgt_id", mgt_sch_id_lookup[management_setting["mgt_sch"]],
                                         "id", lum_id_lookup["{0}_lum".format(management_setting["landuse"].lower())])

                    self.db.delete_rows("management_sch_auto", col_where="management_sch_id",
                                        col_where_value=mgt_sch_id_lookup[management_setting["mgt_sch"]])
                    for auto_sch in management_setting:
                        if auto_sch.startswith("auto_sch"):
                            # get current id for management_sch_auto table
                            try:
                                maximum_mgt_sch_auto_id = max(int(auto_sch_row[0]) for auto_sch_row
                                                              in self.db.read_table_columns("management_sch_auto"))  # re-read incase of a changes
                            except ValueError:
                                maximum_mgt_sch_auto_id = 0

                            self.db.insert_row("management_sch_auto", [
                                str(maximum_mgt_sch_auto_id + 1),
                                str(mgt_sch_id_lookup[management_setting["mgt_sch"]]),
                                str(dtl_id_lookup[management_setting[auto_sch]]),
                            ]
                            )

                    self.db.delete_rows("management_sch_op", col_where="management_sch_id",
                                        col_where_value=mgt_sch_id_lookup[management_setting["mgt_sch"]])
                    for op_sch in management_setting:
                        if op_sch.startswith("op_sch"):
                            # get current id for management_sch_op table
                            try:
                                maximum_mgt_sch_op_id = max(int(op_sch_row[0]) for op_sch_row
                                                            in self.db.read_table_columns("management_sch_op"))  # re-read incase of a changes
                            except ValueError:
                                maximum_mgt_sch_op_id = 0

                            self.db.insert_row("management_sch_op", [
                                str(maximum_mgt_sch_op_id + 1),
                                str(mgt_sch_id_lookup[management_setting["mgt_sch"]]),
                                management_setting[op_sch]["op_typ"],
                                str(int(
                                    management_setting[op_sch]["date"].split("/")[1])),
                                str(int(
                                    management_setting[op_sch]["date"].split("/")[0])),
                                "0",
                                management_setting["landuse"],
                                "-",
                                str(management_setting[op_sch]
                                    ["date"].split("/")[0]),
                                "-",
                                str(management_setting[op_sch]["rot_year"])
                            ]
                            )

                            if management_setting[op_sch]["harvest_part"] is None:
                                self.db.update_value(
                                    "management_sch_op", "op_data2", None, "id", str(maximum_mgt_sch_op_id + 1))
                            else:
                                self.db.update_value("management_sch_op", "op_data2",
                                    management_setting[op_sch]["harvest_part"], "id", str(maximum_mgt_sch_op_id + 1))
                            self.db.update_value(
                                "management_sch_op", "description", None, "id", str(maximum_mgt_sch_op_id + 1))

    def reservoir_management(self, reservoir_management_settings):
        if self.db.table_exists("d_table_dtl"):
            d_table_dtl = self.db.read_table_columns("d_table_dtl")
            dtl_id_lookup = {dtl_name[1]: str(
                dtl_name[0]) for dtl_name in d_table_dtl}
        else:
            print("databases have not been configured")
            sys.exit(1)

        if len(reservoir_management_settings) > 0:
            print("\n\t>  setting up reservoir management options")

            for reservoir_setting in reservoir_management_settings:
                reservoir_setting["id"] = str(reservoir_setting["id"])
                reservoir_setting["principal_area"] = \
                    str(float(reservoir_setting["principal_area"])/10000)
                reservoir_setting["emergency_area"] = \
                    str(float(reservoir_setting["emergency_area"])/10000)
                reservoir_setting["principal_volume"] = \
                    str(float(reservoir_setting["principal_volume"])/10000)
                reservoir_setting["emergency_volume"] = \
                    str(float(reservoir_setting["emergency_volume"])/10000)

                if reservoir_setting["dtl_name"] in dtl_id_lookup:
                    # add/update hydrology properties for existing management
                    self.db.update_value("reservoir_res", "rel_id",
                        dtl_id_lookup[reservoir_setting["dtl_name"]], "id", reservoir_setting["id"])
                    self.db.update_value("reservoir_res", "name",
                        reservoir_setting["set_res_name"], "id", reservoir_setting["id"])
                    self.db.update_value("reservoir_con", "name",
                        reservoir_setting["set_res_name"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "name",
                        reservoir_setting["set_res_name"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Yr_op", reservoir_setting["date_operational"].split(
                        "/")[2], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Mon_op", reservoir_setting["date_operational"].split(
                        "/")[1], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Area_ps",
                        reservoir_setting["principal_area"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Area_es",
                        reservoir_setting["emergency_area"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Vol_ps",
                        reservoir_setting["principal_volume"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Vol_es",
                        reservoir_setting["emergency_volume"], "id", reservoir_setting["id"])

                else:
                    maximum_dtl_id = max(
                        int(dtl_name[0]) for dtl_name in d_table_dtl)

                    self.db.insert_row("d_table_dtl", [str(
                        maximum_dtl_id + 1), reservoir_setting["dtl_name"], "res_rel.dtl"])

                    d_table_dtl = self.db.read_table_columns("d_table_dtl")
                    dtl_id_lookup = {dtl_name[1]: str(dtl_name[0])
                                     for dtl_name in d_table_dtl}

                    # add/update hydrology properties for new management
                    self.db.update_value("reservoir_res", "rel_id",
                        dtl_id_lookup[reservoir_setting["dtl_name"]], "id", reservoir_setting["id"])
                    self.db.update_value("reservoir_res", "name",
                        reservoir_setting["set_res_name"], "id", reservoir_setting["id"])
                    self.db.update_value("reservoir_con", "name",
                        reservoir_setting["set_res_name"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "name",
                        reservoir_setting["set_res_name"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Yr_op", reservoir_setting["date_operational"].split(
                        "/")[2], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Mon_op", reservoir_setting["date_operational"].split(
                        "/")[1], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Area_ps",
                        reservoir_setting["principal_area"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Area_es",
                        reservoir_setting["emergency_area"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Vol_ps",
                        reservoir_setting["principal_volume"], "id", reservoir_setting["id"])
                    self.db.update_value("hydrology_res", "Vol_es",
                        reservoir_setting["emergency_volume"], "id", reservoir_setting["id"])

                    # add conditions for decision table management
                    for setting in reservoir_setting:
                        if setting.startswith("cond"):
                            d_table_dtl_conds = self.db.read_table_columns(
                                "d_table_dtl_cond")
                            maximum_dtl_cond_id = max(int(cond_row[0])
                                                      for cond_row in d_table_dtl_conds)

                            self.db.insert_row("d_table_dtl_cond", [
                                str(maximum_dtl_cond_id + 1),
                                dtl_id_lookup[reservoir_setting["dtl_name"]],
                                reservoir_setting[setting]["main_variable"], "res", "0",
                                reservoir_setting[setting]["limiting_var"],
                                reservoir_setting[setting]["limit_operator"],
                                reservoir_setting[setting]["constraint"],
                            ])

                            # set condition aternatives
                            dtl_conds_id_lookup = {str(cond_row[1]): str(cond_row[0])
                                                   for cond_row in self.db.read_table_columns("d_table_dtl_cond")}  # re-read after changes

                            for cond_setting in reservoir_setting[setting]["alts"]:
                                maximum_dtl_cond_alt_id = max(int(cond_row[0])
                                                              for cond_row in self.db.read_table_columns("d_table_dtl_cond_alt"))

                                self.db.insert_row("d_table_dtl_cond_alt", [
                                    str(maximum_dtl_cond_alt_id + 1),
                                    dtl_conds_id_lookup[dtl_id_lookup[reservoir_setting["dtl_name"]]],
                                    cond_setting
                                ])

                    # add actions for decision table management
                    alt_count = 0  # keep track of number of aternative to throw an error if different between conditions
                    for setting in reservoir_setting:
                        if setting.startswith("act"):
                            d_table_dtl_act = self.db.read_table_columns(
                                "d_table_dtl_act")
                            maximum_dtl_act_id = max(
                                int(act_row[0]) for act_row in d_table_dtl_act)

                            self.db.insert_row("d_table_dtl_act", [
                                str(maximum_dtl_act_id + 1),
                                dtl_id_lookup[reservoir_setting["dtl_name"]],
                                reservoir_setting[setting]["action_type"], "res", "0",
                                reservoir_setting[setting]["name"],
                                reservoir_setting[setting]["action_option"],
                                reservoir_setting[setting]["const1"],
                                reservoir_setting[setting]["const2"],
                                reservoir_setting[setting]["fp"],
                            ])

                            # set output switches
                            d_table_act_out_id_lookup = {str(conds_row[1]): str(conds_row[0]) for conds_row
                                                         in self.db.read_table_columns("d_table_dtl_act")}

                            for cond_setting in reservoir_setting[setting]["out_switches"]:
                                maximum_dtl_act_out_alt_id = max(int(cond_row[0]) for \
                                    cond_row in self.db.read_table_columns("d_table_dtl_act_out"))  # re-read after changes

                                self.db.insert_row("d_table_dtl_act_out", [
                                    str(maximum_dtl_act_out_alt_id + 1),
                                    d_table_act_out_id_lookup[dtl_id_lookup[reservoir_setting["dtl_name"]]],
                                    "1" if cond_setting.lower() == "y" else "0"
                                ])


    def model_options(self):
        # self.db.connect()
        self.db.update_value("codes_bsn", "pet", str(
            config.ET_Method - 1), "id", "1")
        self.db.update_value("codes_bsn", "rte_cha", str(
            config.Routing_Method - 1), "id", "1")
        self.db.update_value("codes_bsn", "event", str(
            config.Routing_Timestep - 1), "id", "1")

        self.db.close_connection()

    def create_project(self):
        project_string = """{{\n"swatplus-project": {{
		"version": "1.2.3",
		"name": "{selection}",
		"databases": {{
			"project": "{selection}.sqlite",
			"datasets": "swatplus_datasets.sqlite"
		}},
		"model": "SWAT+"\n	}}\n}}
        """.format(**self.variables)
        write_to("{model_dir}/{selection}.json".format(**
                                                       self.variables), project_string)


if __name__ == "__main__":
    if config.Model_2_config:
        sys.exit(0)

    sp_api_mode = False
    setup_editor_project = False
    configure_model_options = False
    setup_management = False
    write_files = False
    run_swatplus = False

    try:
        if sys.argv[2] == "setup_editor_project":
            sp_api_mode = True
            setup_editor_project = True
            print("\n     >> creating SWATPlus editor compatible project")

        if sys.argv[2] == "configure_model_options":
            sp_api_mode = True
            configure_model_options = True
            print("\n     >> configuring model options")

        if sys.argv[2] == "setup_management":
            sp_api_mode = True
            setup_management = True
            print("\n     >> setting up management")

        if sys.argv[2] == "write_files":
            sp_api_mode = True
            write_files = True
            print("\n     >> writing SWAT+ files")

        if sys.argv[2] == "run_swatplus":
            sp_api_mode = True
            run_swatplus = True

    except:
        pass

    if not sp_api_mode:
        print("\n     >> configuring model in editor")

    keep_log = True if config.Keep_Log else False
    log = log("{base}/swatplus_aw_log.txt".format(base=sys.argv[1]))
    # announce
    log.info("running swatplus editor module", keep_log)
    editor = swat_plus_editor(base_dir, model_name)

    if (sp_api_mode and setup_editor_project) or (not sp_api_mode):
        editor.db.connect(report_ = False)
        log.info("initialising databases", keep_log)
        editor.initialise_databases()
        log.info("creating editor project for GUI compatibility", keep_log)
        editor.create_project()
        log.info("setting up the project", keep_log)
        editor.setup_project()

    if (sp_api_mode and configure_model_options) or (not sp_api_mode):
        editor.initialise_databases()
        editor.setup_project()
        log.info("setting simulation period and adding weather", keep_log)
        editor.set_printing_weather(config.Start_Year, config.End_Year)
    
    if (sp_api_mode and setup_management) or (not sp_api_mode):
        editor.db.connect(report_ = False)
        log.info("setting up management options for landuse", keep_log)
        editor.landuse_management(config.launduse_management_settings)
        log.info("setting up management options for reservoirs", keep_log)
        editor.reservoir_management(config.reservoir_management_settings)

    if (sp_api_mode and configure_model_options) or (not sp_api_mode):
        editor.db.connect(report_ = False)
        log.info("configuring model run options", keep_log)
        editor.model_options()

    if (sp_api_mode and write_files) or (not sp_api_mode):
        editor.db.connect(report_ = False)
        log.info("writing files", keep_log)
        editor.write_files()
        print("")

    if (sp_api_mode and run_swatplus) or (not sp_api_mode):
        editor.db.connect(report_ = False)
        if not config.Calibrate:
            log.info("model will not be calibrated", keep_log)
            if config.Executable_Type == 1:
                log.info("running model using release version", keep_log)
                editor.run(config.Executable_Type)
            if config.Executable_Type == 2:
                log.info("running model using debug version", keep_log)
                editor.run(config.Executable_Type)

        log.info("finnished running swatplus editor module\n", keep_log)
