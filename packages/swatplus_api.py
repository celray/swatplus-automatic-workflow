
'''
date        : 23/04/2020
description : this is a template for qgs file

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''


import sys
import os
import platform


class swatplus_api:
    """
    Class to run steps without running the entire workflow
    """

    def __init__(self):
        self.options = ["prepare_project", "delineate_watershed", "create_hrus",
                        "setup_editor_project", "configure_model_options", "setup_management",
                        "write_files", "run_swatplus", "make_figures", "calibrate"]
    # take care of wrong options

    def run_step(self, option, has_argument=True):
        if not has_argument:
            print("\n\t! no option was selected, please use one of the following")
            for available_option in self.options:
                print(f'\t  - {available_option}')

            print("\t> usage: swatplus_api [option]\n")
            return False

        if (not option in self.options):
            print(f'\n\t! the selected option, "{option}", was not found, please use one of the following')
            for available_option in self.options:
                print(f'\t  - {available_option}')
            print("\t> usage: swatplus_api [option]\n")
            return False

        if option == "prepare_project":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/prepare_project.py "{sys.argv[1]}"')

        if option == "delineate_watershed":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_qswat.py "{sys.argv[1]}" watershed')

        if option == "create_hrus":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_qswat.py "{sys.argv[1]}" hrus')

        if option == "setup_editor_project":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_editor.py "{sys.argv[1]}" setup_editor_project')

        if option == "configure_model_options":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_editor.py "{sys.argv[1]}" configure_model_options')

        if option == "setup_management":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_editor.py "{sys.argv[1]}" setup_management')

        if option == "write_files":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_editor.py "{sys.argv[1]}" write_files')

        if option == "run_swatplus":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_editor.py "{sys.argv[1]}" run_swatplus')

        if option == "make_figures":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_make_figures.py "{sys.argv[1]}"')

        if option == "calibrate":
            wf_path = os.environ["swatplus_wf_dir"]
            if platform.system() == "Windows":
                os.system(f'python-qgis.bat {wf_path}/main_stages/run_calibration.py "{sys.argv[1]}"')

# check number of arguments incase user did not provide
num_args = len(sys.argv)
api = swatplus_api()

if num_args > 2:
    api.run_step(sys.argv[2])
else:
    api.run_step("", False)
