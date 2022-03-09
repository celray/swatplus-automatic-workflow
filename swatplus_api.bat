@echo off

REM set the directory of QGIS
set QGIS_Dir=C:\Program Files\QGIS 3.22.3
REM set ERRORLEVEL=0

REM set variables for project initialisation
set api_script=C:\SWAT\SWATPlus\Workflow\packages\swatplus_api.py

set BASE_DIR="%cd:\=\\%"
set WF_QGIS=%QGIS_Dir%\apps\qgis\python\plugins

REM add default plugins and model directory to python path
set PYTHONPATH=%BASE_DIR%;%QGIS_Dir%\apps\qgis\python\plugins;%PYTHONPATH%
set PATH=%QGIS_Dir%\apps\qgis\python\plugins;%PATH%

REM change directory to the python-qgis-ltr.bat
cd %QGIS_Dir%\bin

REM start runing the workflow using PyQGIS
call python-qgis.bat %api_script% %BASE_DIR% %1

