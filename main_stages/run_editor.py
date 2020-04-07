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

# adding to path before importing custom modules
sys.path.insert(0, os.path.join(os.environ["swatplus_wf_dir"], "packages"))
sys.path.append(os.path.join(os.environ["swatplus_wf_dir"]))
sys.path.insert(0, sys.argv[1])

from sqlite_tools import sqlite_connection
import model_options
from editor_api.weather2012_to_weather import list_files, read_from, write_to, copy_file
import namelist
from logger import log


base_dir = os.environ["BASE_DIR"]
model_name = namelist.Project_Name


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
        self.weather_data_dir = "{model_dir}/Scenarios/Default/TxtInOut/weather".format(
            **self.variables)
        self.wgn_db = "{api_dir}/swatplus_wgn.sqlite".format(
            api_dir=self.api_dir)

        self.variables = {
            "models_dir": self.model_dir,
            "scripts_dir": self.scripts_dir,
            "api": self.api,
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

    def initialise_databases(self):
        "correct bug in plants_plt days_mat"
        self.db = sqlite_connection(self.prj_database)
        self.db.connect()
        self.db.delete_table("plants_plt")
        sql_command = """CREATE TABLE plants_plt (
            id          INTEGER       NOT NULL
                                      PRIMARY KEY,
            name        VARCHAR (255) NOT NULL,
            plnt_typ    VARCHAR (255) NOT NULL,
            gro_trig    VARCHAR (255) NOT NULL,
            nfix_co     REAL          NOT NULL,
            days_mat    REAL          NOT NULL,
            bm_e        REAL          NOT NULL,
            harv_idx    REAL          NOT NULL,
            lai_pot     REAL          NOT NULL,
            frac_hu1    REAL          NOT NULL,
            lai_max1    REAL          NOT NULL,
            frac_hu2    REAL          NOT NULL,
            lai_max2    REAL          NOT NULL,
            hu_lai_decl REAL          NOT NULL,
            dlai_rate   REAL          NOT NULL,
            can_ht_max  REAL          NOT NULL,
            rt_dp_max   REAL          NOT NULL,
            tmp_opt     REAL          NOT NULL,
            tmp_base    REAL          NOT NULL,
            frac_n_yld  REAL          NOT NULL,
            frac_p_yld  REAL          NOT NULL,
            frac_n_em   REAL          NOT NULL,
            frac_n_50   REAL          NOT NULL,
            frac_n_mat  REAL          NOT NULL,
            frac_p_em   REAL          NOT NULL,
            frac_p_50   REAL          NOT NULL,
            frac_p_mat  REAL          NOT NULL,
            harv_idx_ws REAL          NOT NULL,
            usle_c_min  REAL          NOT NULL,
            stcon_max   REAL          NOT NULL,
            vpd         REAL          NOT NULL,
            frac_stcon  REAL          NOT NULL,
            ru_vpd      REAL          NOT NULL,
            co2_hi      REAL          NOT NULL,
            bm_e_hi     REAL          NOT NULL,
            plnt_decomp REAL          NOT NULL,
            lai_min     REAL          NOT NULL,
            bm_tree_acc REAL          NOT NULL,
            yrs_mat     REAL          NOT NULL,
            bm_tree_max REAL          NOT NULL,
            ext_co      REAL          NOT NULL,
            leaf_tov_mn REAL          NOT NULL,
            leaf_tov_mx REAL          NOT NULL,
            bm_dieoff   REAL          NOT NULL,
            rt_st_beg   REAL          NOT NULL,
            rt_st_end   REAL          NOT NULL,
            plnt_pop1   REAL          NOT NULL,
            frac_lai1   REAL          NOT NULL,
            plnt_pop2   REAL          NOT NULL,
            frac_lai2   REAL          NOT NULL,
            frac_sw_gro REAL          NOT NULL,
            wnd_live    REAL          NOT NULL,
            wnd_dead    REAL          NOT NULL,
            wnd_flat    REAL          NOT NULL,
            description TEXT
        );
        """
        self.db.cursor.execute(sql_command)
        self.db.commit_changes()

        # import GIS
        os.chdir(self.api_dir)
        os.system(
            'python {api} create_database --db_type=project --db_file="{p_db}" --db_file2="{r_db}"'.format(**self.variables))
        os.system(
            'python {api} import_gis --delete_existing=y --project_db_file="{p_db}"'.format(**self.variables))

    def setup_project(self):
        # specify project config info

        config_info = self.db.read_table_columns("project_config", "all")
        config_info = list(config_info[-1])

        for index in range(0, len(config_info)):
            config_info[index] = str(config_info[index])

        config_info[1] = self.model_name
        config_info[3] = "1.2.3"
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
            namelist.Warm_Up_Period), "id", "1")
        self.db.update_value("print_prt", "csvout",
                             str(namelist.Print_CSV), "id", "1")

        for print_object in namelist.Print_Objects:
            self.db.update_value("print_prt_object", "daily", "0",
                                 "id", model_options.print_obj_lookup[print_object])
            self.db.update_value("print_prt_object", "monthly", "0",
                                 "id", model_options.print_obj_lookup[print_object])
            self.db.update_value("print_prt_object", "yearly", "0",
                                 "id", model_options.print_obj_lookup[print_object])
            self.db.update_value("print_prt_object", "avann", "0",
                                 "id", model_options.print_obj_lookup[print_object])

            if 1 in namelist.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "daily", "1",
                                     "id", model_options.print_obj_lookup[print_object])

            if 2 in namelist.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "monthly", "1",
                                     "id", model_options.print_obj_lookup[print_object])

            if 3 in namelist.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "yearly", "1",
                                     "id", model_options.print_obj_lookup[print_object])

            if 4 in namelist.Print_Objects[print_object]:
                self.db.update_value("print_prt_object", "avann", "1",
                                     "id", model_options.print_obj_lookup[print_object])

        self.db.close_connection()

        # add weather
        os.chdir(self.api_dir)
        os.system('python {api_d}/weather2012_to_weather.py "{ws}" "{wdd}" {wf}'.format(
            ws=self.weather_source, wdd=self.weather_data_dir, wf="observed", api_d=self.api_dir))
        os.system('python {api} import_weather --delete_existing=y --create_stations=n --import_type={imp_typ} --import_method=database --project_db_file="{p_db}"'.format(
            api=self.api, p_db=self.prj_database, imp_typ="wgn"))
        os.system('python {api} import_weather --delete_existing=y --create_stations=y --import_type={imp_typ} --project_db_file="{p_db}"'.format(
            api=self.api, p_db=self.prj_database, imp_typ="observed"))

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
        os.system('python {0} write_files --output_files_dir="{2}" --project_db_file="{1}"'.format(
            self.api, self.prj_database, self.txt_in_out_dir))

        # setting weather dir in cio
        cio_content = read_from(
            "{tio}/file.cio".format(tio=self.txt_in_out_dir))
        new_cio = ""

        paths_to_set_for = ["pcp_path", "tmp_path",
                            "slr_path", "hmd_path", "wnd_path"]
        for line_ in cio_content:
            if line_.split(" ")[0] in paths_to_set_for:
                line_ = line_.replace("null", "weather\\\\")
            new_cio += line_

        write_to("{tio}/file.cio".format(tio=self.txt_in_out_dir), new_cio)

        # clean up weather
        weather_files = list_files(self.txt_in_out_dir, "tmp")
        weather_files += list_files(self.txt_in_out_dir, "hmd")
        weather_files += list_files(self.txt_in_out_dir, "slr")
        weather_files += list_files(self.txt_in_out_dir, "pcp")
        weather_files += list_files(self.txt_in_out_dir, "wnd")

        for file in weather_files:
            if os.path.isfile(file):
                os.remove(file)

    def run(self, exe_type):
        os.chdir(self.txt_in_out_dir)

        copy_file("{base}/editor_api/swat_exe/rev60.1_64debug.exe".format(base=self.scripts_dir),
                  "{txt_in_out_dir}/rev60.1_64debug.exe".format(txt_in_out_dir=self.txt_in_out_dir))
        copy_file("{base}/editor_api/swat_exe/rev60.1_64rel.exe".format(base=self.scripts_dir),
                  "{txt_in_out_dir}/rev60.1_64rel.exe".format(txt_in_out_dir=self.txt_in_out_dir))

        if exe_type == 1:
            print("\n     >> running SWAT+")
            # os.system("rev60.1_64rel.exe")
            sub_process = subprocess.Popen("rev60.1_64rel.exe", close_fds=True, shell=True,
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
                                tb = " "*10, yr = line_parts[4], mn = line_parts[2], dy = line_parts[3]))
                        else:
                            if line_parts[0] == "Execution":
                                sys.stdout.write("\r\t   finished running SWAT+    ")
                            elif line_parts[0] == "Revision":
                                print("\t   SWAT+ version: {0}".format(line_parts[-1]))
                            elif line_parts[0] == "reading":
                                sys.stdout.write("\r\t   reading {0}            ".format(" ".join(line_parts[2:-3])))
                        sys.stdout.flush()
                    line = ""

        elif exe_type == 2:
            os.system("rev60.1_64debug.exe")

    def model_options(self):
        self.db.connect()
        self.db.update_value("codes_bsn", "pet", str(
            namelist.ET_Method - 1), "id", "1")
        self.db.update_value("codes_bsn", "rte_cha", str(
            namelist.Routing_Method - 1), "id", "1")
        self.db.update_value("codes_bsn", "event", str(
            namelist.Routing_Timestep - 1), "id", "1")

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
        write_to("{model_dir}/{selection}.json".format(**self.variables), project_string)
        

if __name__ == "__main__":
    if namelist.Model_2_namelist:
        sys.exit(0)
                    
    keep_log = True if namelist.Keep_Log else False
    log = log("{base}/swatplus_aw_log.txt".format(base = sys.argv[1]))
    # announce
    print("\n     >> configuring model in editor")
    log.info("running swatplus editor module", keep_log)
    editor = swat_plus_editor(base_dir, model_name)
    log.info("initialising databases", keep_log)
    editor.initialise_databases()
    log.info("creating editor project for GUI compatibility", keep_log)
    editor.create_project()
    log.info("setting up the project", keep_log)
    editor.setup_project()
    log.info("setting simulation period and adding weather", keep_log)
    editor.set_printing_weather(namelist.Start_Year, namelist.End_Year)
    log.info("configuring model run options", keep_log)
    editor.model_options()
    log.info("writing files", keep_log)
    editor.write_files()
    print("")
    if not namelist.Calibrate:
        log.info("model will not be calibrated", keep_log)
        if namelist.Executable_Type == 1:
            log.info("running model using release version", keep_log)
            editor.run(namelist.Executable_Type)
        if namelist.Executable_Type == 2:
            log.info("running model using debug version", keep_log)
            editor.run(namelist.Executable_Type)

    log.info("finnished running swatplus editor module\n", keep_log)
