
# set variables for project initialisation
export python_script_prepare_qswat=$HOME/.SWAT/SWATPlus/Workflow/main_stages/prepare_project.py
export python_script_make_namelist=$HOME/.SWAT/SWATPlus/Workflow/main_stages/generate_namelist.py
export python_script_run_qswat=$HOME/.SWAT/SWATPlus/Workflow/main_stages/run_qswat.py
export python_script_run_editor=$HOME/.SWAT/SWATPlus/Workflow/main_stages/run_editor.py
export python_script_run_calibration=$HOME/.SWAT/SWATPlus/Workflow/main_stages/run_calibration.py
export python_script_make_figures=$HOME/.SWAT/SWATPlus/Workflow/main_stages/run_make_figures.py
export python_script_clean_up=$HOME/.SWAT/SWATPlus/Workflow/main_stages/run_clean_up.py

export BASE_DIR=$PWD
export swatplus_wf_dir=$HOME/.SWAT/SWATPlus/Workflow/

# add default plugins and model directory to python path
export PYTHONPATH=$BASE_DIR:$PYTHONPATH
# export PATH=%PATH%

# start runing the workflow using PyQGIS
python3 $python_script_prepare_qswat $BASE_DIR

python3 $python_script_make_namelist $BASE_DIR  

python3 $python_script_run_qswat $BASE_DIR
python3 $python_script_run_editor $BASE_DIR
python3 $python_script_run_calibration $BASE_DIR
python3 $python_script_make_figures $BASE_DIR

python3 $python_script_clean_up $BASE_DIR
