# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QSWATBatch
 Run QSWATPlus in batch mode using a project file to provide inputs and parameters
                              -------------------
        begin                : 2015-10-20
        copyright            : (C) 2015 by Chris George
        email                : cgeorge@mcmaster.ca
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# derived from http://snorf.net/blog/2014/01/04/writing-unit-tests-for-qgis-python-plugins/

from qgis.core import * # @UnusedWildImport
from qgis.gui import * # @UnusedWildImport

from PyQt5.QtCore import * # @UnusedWildImport
from PyQt5.QtGui import * # @UnusedWildImport
import sys
import os.path
import shutil

import atexit
from QSWATPlus import QSWATPlus
from delineation import Delineation
from hrus import HRUs
from QSWATUtils import QSWATUtils
from parameters import Parameters

osGeo4wRoot = os.getenv('OSGEO4W_ROOT')
QgsApplication.setPrefixPath(osGeo4wRoot + r'\apps\qgis', True)

QgsApplication.initQgis()

# create a new application object
# without this importing processing causes the following error:
# QWidget: Must construct a QApplication before a QPaintDevice
app = QgsApplication([], True)

if len(QgsProviderRegistry.instance().providerList()) == 0:
    raise RuntimeError('No data providers available.  Check prefix path setting above')

# QSWATUtils.information('Providers: {0!s}'.format(QgsProviderRegistry.instance().providerList()), True)

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
iface = DummyInterface()

QCoreApplication.setOrganizationName('QGIS')
QCoreApplication.setApplicationName('QGIS2')

def main(projFile):
    """Run QSWAT in batch mode from project file."""
    if not os.path.exists(projFile):
        QSWATUtils.error('Cannot find project file {0}'.format(projFile), True)
        return -1
    projDir, suffix = os.path.splitext(projFile)
    if not suffix == '.qgs':
        QSWATUtils.error('{0} is not a project (.qgs) file'.format(projFile), True)
        return -1
    # print('Ignore messages about shape files not a recognised format\n')
    # SRS path is not set properly.
    if not os.path.exists(QgsApplication.srsDbFilePath()):
        QSWATUtils.error('Need to copy resources folder to make directory {0} exist, eg copy OSGeo4W/apps/qgis/resources to OSGeo4W'.format(QgsApplication.srsDbFilePath()), True)
        return -1
    plugin = QSWATPlus.QSWATPlus(iface)
    dlg = plugin._odlg # useful shorthand for later
    if not os.path.exists(projDir):
        QSWATUtils.error('Project directory {0} not found'.format(projDir), True) 
        return -1
    projName = os.path.split(projDir)[1]
    projectDatabase = QSWATUtils.join(projDir, projName + '.mdb')
    if os.path.exists(projectDatabase):
        os.remove(projectDatabase)
    shutil.rmtree(QSWATUtils.join(projDir, 'Scenarios'), ignore_errors=True)
    # would like to remover whole Watershed directory, 
    # but inlets/outlets shapefile stored in Watershed\Shapes
    QSWATUtils.removeFiles(QSWATUtils.join(projDir, r'Watershed\Shapes\rivs1.shp'))
    QSWATUtils.removeFiles(QSWATUtils.join(projDir, r'Watershed\Shapes\subs1.shp'))
    shutil.rmtree(QSWATUtils.join(projDir, r'Watershed\Text'), ignore_errors=True)
    proj = QgsProject.instance()
    proj.read(projFile)
    plugin.setupProject(proj, True)
    if not (os.path.exists(plugin._gv.textDir) and os.path.exists(plugin._gv.landuseDir)):
        QSWATUtils.error('Directories not created', True)
        return -1
    if not dlg.delinButton.isEnabled():
        QSWATUtils.error('Delineate button not enabled', True)
        return -1
    delin = Delineation(plugin._gv, plugin._demIsProcessed)
    delin.init()
    QSWATUtils.information('DEM: {0}'.format(os.path.split(plugin._gv.demFile)[1]), True)
    delin.addHillshade(plugin._gv.demFile, None, None)
    QSWATUtils.information('Inlets/outlets file: {0}'.format(os.path.split(plugin._gv.outletFile)[1]), True)
    delin.runTauDEM2()
    delin.finishDelineation()
    if not dlg.hrusButton.isEnabled():
        QSWATUtils.error('HRUs button not enabled', True)
        return -1
    hrus = HRUs(plugin._gv, dlg.reportsBox)
    hrus.init()
    hrus.readFiles()
    if not os.path.exists(QSWATUtils.join(plugin._gv.textDir, Parameters._TOPOREPORT)):
        QSWATUtils.error('Elevation report not created', True)
        return -1
    if not os.path.exists(QSWATUtils.join(plugin._gv.textDir, Parameters._BASINREPORT)):
        QSWATUtils.error('Landuse and soil report not created', True)
        return -1
    hrus.calcHRUs()
    if not os.path.exists(QSWATUtils.join(plugin._gv.textDir, Parameters._HRUSREPORT)):
        QSWATUtils.error('HRUs report not created', True)
        return -1
    if not os.path.exists(QSWATUtils.join(projDir, r'Watershed\Shapes\rivs1.shp')):
        QSWATUtils.error('Streams shapefile not created', True)
        return -1
    if not os.path.exists(QSWATUtils.join(projDir, r'Watershed\Shapes\subs1.shp')):
        QSWATUtils.error('Subbasins shapefile not created', True)
        return -1
    return 0

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        result = main(sys.argv[1])
        print('')
        if result == 0:
            print('QSWAT completed OK')
            sys.exit(0)
        else:
            print('QSWAT failed to complete')
            sys.exit(1)
        print('')
    else:
        print('You must provide a project file')
        sys.exit(1)
    
