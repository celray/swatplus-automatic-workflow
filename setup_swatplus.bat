@echo off

REM set the directory of QGIS
set QGIS_Dir=C:\Program Files\QGIS 3.10
REM set ERRORLEVEL=0

REM set variables for project initialisation
set python_script_prepare_qswat=C:\SWAT\SWATPlus\Workflow\prepare_project.py
set python_script_make_namelist=C:\SWAT\SWATPlus\Workflow\generate_namelist.py
set python_script_run_qswat=C:\SWAT\SWATPlus\Workflow\run_qswat.py
set python_script_run_editor=C:\SWAT\SWATPlus\Workflow\run_editor.py
set python_script_run_calibration=C:\SWAT\SWATPlus\Workflow\run_calibration.py
set python_script_clean_up=C:\SWAT\SWATPlus\Workflow\run_clean_up.py

set BASE_DIR="%cd:\=\\%"
set WF_QGIS=%QGIS_Dir%\apps\qgis\python\plugins

REM add default plugins and model directory to python path
set PYTHONPATH=%BASE_DIR%;%QGIS_Dir%\apps\qgis\python\plugins;%PYTHONPATH%
set PATH=%QGIS_Dir%\apps\qgis\python\plugins;%PATH%

REM change directory to the python-qgis-ltr.bat
cd %QGIS_Dir%\bin

REM start runing the workflow using PyQGIS
call python-qgis-ltr.bat %python_script_prepare_qswat% %BASE_DIR%

If %ERRORLEVEL% == 0 (
        call python-qgis-ltr.bat %python_script_make_namelist% %BASE_DIR%   
        If %ERRORLEVEL% == 0 (
                call python-qgis-ltr.bat %python_script_run_qswat% %BASE_DIR%
                If %ERRORLEVEL% == 0 (
                        call python-qgis-ltr.bat %python_script_run_editor% %BASE_DIR%
                        call python-qgis-ltr.bat %python_script_run_calibration% %BASE_DIR%
                ) else (Echo there was an error in running QSWAT+.)
        )
) else (Echo there was an error preparing the project file.)

call python-qgis-ltr.bat %python_script_clean_up% %BASE_DIR%

exit /b %ERRORLEVEL%
