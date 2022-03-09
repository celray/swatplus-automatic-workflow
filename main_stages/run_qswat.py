'''
date        : 31/03/2020
description : this module coordinates the gis part of model setup

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import os.path
import shutil
import sys
import platform
import warnings

if platform.system() == "Linux":
    import pyximport  # importing cython needs this on linux
    pyximport.install()

# skip deprecation warnings when importing PyQt5
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from qgis.core import *
    from qgis.utils import iface
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *

# QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.10/apps/qgis', True)
qgs = QgsApplication([], True)
qgs.initQgis()

# Prepare processing framework
if platform.system() == "Windows":
    sys.path.append('{QGIS_Dir}/apps/qgis/python/plugins'.format(
        QGIS_Dir = os.environ['QGIS_Dir'])) # Folder where Processing is located
else:
    sys.path.append('/usr/share/qgis/python/plugins') # Folder where Processing is located

# skip syntax warnings on linux
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from processing.core.Processing import Processing
    Processing.initialize()

    import processing

sys.path.append(os.path.join(os.environ["swatplus_wf_dir"], "packages"))
sys.path.append(os.path.join(os.environ["swatplus_wf_dir"], "qswatplus"))
sys.path.append(os.path.join(os.environ["swatplus_wf_dir"]))
sys.path.insert(0, sys.argv[1])

from helper_functions import list_files

import atexit
import qswatplus
import config
from logger import log

os.chdir(os.path.join(os.environ["swatplus_wf_dir"], "qswatplus"))

__package__ = 'qswatplus'
from .QSWATPlusMain import QSWATPlus
from .delineation import Delineation
from .hrus import HRUs
from .QSWATUtils import QSWATUtils
from .parameters import Parameters
from glob import glob

atexit.register(QgsApplication.exitQgis)


class DummyInterface(object):
    """Dummy iface to give access to layers."""

    def __getattr__(self, *args, **kwargs):
        """Dummy function."""
        def dummy(*args, **kwargs):
            return self
        return dummy

    def __iter__(self):
        """Dummy function."""
        return self

    def __next__(self):
        """Dummy function."""
        raise StopIteration

    def layers(self):
        """Simulate iface.legendInterface().layers()."""
        return list(QgsProject.instance().mapLayers().values())


if config.Model_2_config:
    sys.exit(0)

sp_api_mode = False
run_watershed = True
run_hrus = True


try:
    if sys.argv[2] == "watershed":
        sp_api_mode = True
        run_hrus = False
        print("\n     >> delineating watershed from DEM")
    if sys.argv[2] == "hrus":
        sp_api_mode = True
        run_watershed = False
        print("\n     >> creating model hrus")
except:
    pass

if not sp_api_mode:
    # announce
    print(f"\n     >> setting up model hrus")

keep_log = True if config.Keep_Log else False
log = log("{base}/swatplus_aw_log.txt".format(base = sys.argv[1]))

iface = DummyInterface()


plugin = QSWATPlus(iface)
dlg = plugin._odlg  # useful shorthand for later

base_dir = sys.argv[1]
projDir = "{base}/{model_name}".format(base=base_dir,
                                       model_name=config.Project_Name)

if not os.path.exists(projDir):
    QSWATUtils.error('Project directory {0} not found'.format(projDir), True)
    log.error('project directory {0} was not found'.format(projDir), keep_log)
    sys.exit(1)

projName = os.path.split(projDir)[1]
projFile = "{dir}/{nm}.qgs".format(dir=projDir, nm=projName)

log.info("creating qgis project instance", keep_log)
proj = QgsProject.instance()

if (sp_api_mode and run_watershed) or (not sp_api_mode):

    # clean up before new files
    log.info("cleaning up files from 'Watershed\Shapes'", keep_log)
    Watershed_shapes = list_files(QSWATUtils.join(
        projDir, r'Watershed/Shapes'), "shp")
    delete_shapes = []

    for Watershed_shape in Watershed_shapes:
        if os.path.basename(Watershed_shape).startswith("reservoirs"):
            delete_shapes.append(Watershed_shape)
        if os.path.basename(Watershed_shape).startswith("rivs"):
            delete_shapes.append(Watershed_shape)
        if os.path.basename(Watershed_shape).startswith("subs"):
            delete_shapes.append(Watershed_shape)
        if Watershed_shape.endswith("channel.shp"):
            delete_shapes.append(Watershed_shape)
        if Watershed_shape.endswith("stream.shp"):
            delete_shapes.append(Watershed_shape)
        if Watershed_shape.endswith("subbasins.shp"):
            delete_shapes.append(Watershed_shape)
        if os.path.basename(Watershed_shape).startswith("hrus"):
            delete_shapes.append(Watershed_shape)
        if Watershed_shape.endswith("wshed.shp"):
            delete_shapes.append(Watershed_shape)
        if os.path.basename(Watershed_shape).startswith("lsus"):
            delete_shapes.append(Watershed_shape)

    for delete_shape in delete_shapes:
        QSWATUtils.removeFiles(delete_shape)

    log.info("cleaning up files from 'Watershed\\Text'", keep_log)
    shutil.rmtree(QSWATUtils.join(projDir, r'Watershed/Text'), ignore_errors=True)

    shutil.rmtree(QSWATUtils.join(projDir, 'Scenarios'), ignore_errors=True)

    log.info("reading qgis project", keep_log)
    proj.read(projFile)

    log.info("initialising qswatplus module for watershed delineation", keep_log)
    plugin.setupProject(proj, True)

    if not (os.path.exists(plugin._gv.textDir) and os.path.exists(plugin._gv.landuseDir)):
        log.error("cannot initialise qswatplus module", keep_log)
        QSWATUtils.error('Directories not created', True)
        sys.exit(1)

    if not dlg.delinButton.isEnabled():
        log.error("cannot initialise qswatplus module", keep_log)
        QSWATUtils.error('Delineate button not enabled', True)
        sys.exit(1)

    log.info("initialising delineation", keep_log)
    delin = Delineation(plugin._gv, plugin._demIsProcessed)
    delin.init()

    QSWATUtils.information('\t - DEM: {0}'.format(os.path.split(plugin._gv.demFile)[1]), True)

    delin.addHillshade(plugin._gv.demFile, None, None, None)
    QSWATUtils.information('\t - Inlets/outlets file: {0}'.format(os.path.split(plugin._gv.outletFile)[1]), True)

    log.info("running taudem", keep_log)
    delin.runTauDEM2()
    log.info("finishing delineation", keep_log)
    delin.finishDelineation()
    if run_watershed:
        QSWATUtils.information('\t - finished delineation\n', True)
    if not dlg.hrusButton.isEnabled():
        log.error("could not initialise hru creation", keep_log)
        QSWATUtils.error('\t ! HRUs button not enabled', True)
        sys.exit(1)

if (sp_api_mode and run_hrus) or (not sp_api_mode):
    # ensure that HRUs runs 'from files' and not from 'saved from previous run'
    
    log.info("reading qgis project", keep_log)
    proj.read(projFile)

    log.info("initialising qswatplus module for HRU creation", keep_log)
    plugin.setupProject(proj, True)

    log.info("removing old gis data from 'BASINDATA' table in project database", keep_log)
    plugin._gv.db.clearTable('BASINSDATA')
    hrus = HRUs(plugin._gv, dlg.reportsBox)
    hrus.init()
    hrus.readFiles()
    if not os.path.exists(QSWATUtils.join(plugin._gv.textDir, Parameters._TOPOREPORT)):
        log.error("error reading HRU data", keep_log)
        QSWATUtils.error('\t ! Elevation report not created \n\n\t   Have you run Delineation?\n', True)
        sys.exit(1)

    if not os.path.exists(QSWATUtils.join(plugin._gv.textDir, Parameters._BASINREPORT)):
        log.error("error reading HRU data", keep_log)
        QSWATUtils.error('\t ! Landuse and soil report not created', True)
        sys.exit(1)

    hrus.calcHRUs()
    if not os.path.exists(QSWATUtils.join(plugin._gv.textDir, Parameters._HRUSREPORT)):
        log.error("error creating HRUs", keep_log)
        QSWATUtils.error('\t ! HRUs report not created', True)
        sys.exit(1)

    if not os.path.exists(QSWATUtils.join(projDir, r'Watershed/Shapes/rivs1.shp')):
        log.error("error creating HRUs", keep_log)
        QSWATUtils.error('\t ! Streams shapefile not created', True)
        sys.exit(1)

    if not os.path.exists(QSWATUtils.join(projDir, r'Watershed/Shapes/subs1.shp')):
        log.error("error creating HRUs", keep_log)
        QSWATUtils.error('\t ! Subbasins shapefile not created', True)
        sys.exit(1)

    log.info("finished creating HRUs\n", keep_log)
    if run_hrus:
        QSWATUtils.information('\t - finished creating HRUs\n', True)
